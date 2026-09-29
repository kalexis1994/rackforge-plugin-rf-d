"""Backward-Euler nonlinear board-3 headphone amplifier laboratory step."""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from headphone_amp_active_dc_reference import (
    NODES, _graph, conditional_headphone_amp_dc, evaluate_headphone_amp_dc,
    headphone_amp_dc_jacobian)
from headphone_output_coupling_reference import _shunt_conductance_s


J7 = len(NODES)
CAP_NODES = {"C19": (None, 0), "C15": (7, 8), "C21": (10, J7)}


def initial_headphone_amp_state(*, transistor_is_a: float,
                                beta_forward: float, beta_reverse: float,
                                temperature_k: float, diode_model: dict) -> dict:
    """DC-consistent capacitor charge with pin 7 and J7 at zero volts."""
    dc = conditional_headphone_amp_dc(
        transistor_is_a=transistor_is_a,
        beta_forward=beta_forward, beta_reverse=beta_reverse,
        temperature_k=temperature_k, diode_model=diode_model)
    values = [dc["node_v"][name] for name in NODES]+[0.0]
    graph = _graph()
    cap = {row["ref"]: row["farad"] for row in graph["capacitors"]}
    if cap != {"C19": 2.5e-6, "C15": 220e-12, "C21": 400e-6}:
        raise ValueError("headphone capacitor values differ from schematic")
    cap_v = {"C19": -values[0], "C15": values[7]-values[8],
             "C21": values[10]-values[J7]}
    return {"node_v": tuple(values), "capacitor_v": cap_v,
            "previous_pin7_v": 0.0,
            "dc_max_kcl_residual_a": dc["max_kcl_residual_a"]}


def nonlinear_headphone_amp_step(*, previous_state: dict,
                                 pin7_v: float, dt_s: float,
                                 transistor_is_a: float,
                                 beta_forward: float,
                                 beta_reverse: float,
                                 temperature_k: float,
                                 diode_model: dict,
                                 tip_load_ohm: float | None = None,
                                 ring_load_ohm: float | None = None) -> dict:
    """Solve all three active BJTs, two diodes and capacitors at this step."""
    if (not math.isfinite(pin7_v) or not math.isfinite(dt_s) or dt_s <= 0):
        raise ValueError("finite input voltage and positive finite dt required")
    old_v = previous_state["node_v"]
    old_cap = previous_state["capacitor_v"]
    if (len(old_v) != len(NODES)+1 or not all(math.isfinite(v) for v in old_v)
            or set(old_cap) != set(CAP_NODES)
            or not all(math.isfinite(v) for v in old_cap.values())):
        raise ValueError("complete finite previous headphone state required")
    graph = _graph()
    cap = {row["ref"]: row["farad"] for row in graph["capacitors"]}
    if cap != {"C19": 2.5e-6, "C15": 220e-12, "C21": 400e-6}:
        raise ValueError("headphone capacitor values differ from schematic")
    load_g = _shunt_conductance_s(tip_load_ohm, ring_load_ohm)
    parameters = dict(transistor_is_a=transistor_is_a,
                      beta_forward=beta_forward, beta_reverse=beta_reverse,
                      temperature_k=temperature_k, diode_model=diode_model,
                      _prepared_graph=graph)

    def evaluate(x: list[float]) -> tuple[list[float], dict]:
        residual, parts = evaluate_headphone_amp_dc(x[:J7], **parameters)
        residual.append(load_g*x[J7])
        currents = {}
        for name, (left, right) in CAP_NODES.items():
            left_v = pin7_v if left is None else x[left]
            cap_v = left_v-x[right]
            current = cap[name]/dt_s*(cap_v-old_cap[name])
            currents[name] = current
            if left is not None:
                residual[left] += current
            residual[right] -= current
        parts["capacitor_currents_a"] = currents
        return residual, parts

    x = list(old_v)
    for iteration in range(80):
        residual, parts = evaluate(x)
        error = max(abs(value) for value in residual)
        if error < 1e-10:
            break
        tangent = headphone_amp_dc_jacobian(x[:J7], **parameters)
        jacobian = [row+[0.0] for row in tangent]
        jacobian.append([0.0]*len(x))
        jacobian[J7][J7] = load_g
        for name, (left, right) in CAP_NODES.items():
            g = cap[name]/dt_s
            if left is not None:
                jacobian[left][left] += g
                jacobian[left][right] -= g
                jacobian[right][left] -= g
            jacobian[right][right] += g
        direction = _solve_linear(jacobian, [-value for value in residual])
        for power in range(24):
            step = 0.5**power
            trial = [voltage+step*change for voltage, change in zip(x, direction)]
            try:
                candidate, _ = evaluate(trial)
                next_error = max(abs(value) for value in candidate)
            except ValueError:
                continue
            if next_error < error:
                x = trial
                break
        else:
            raise ValueError("headphone transient Newton iteration did not decrease KCL")
    else:
        raise ValueError("headphone transient Newton iteration did not converge")
    residual, parts = evaluate(x)
    new_cap = {"C19": pin7_v-x[0], "C15": x[7]-x[8],
               "C21": x[10]-x[J7]}
    return {"node_v": tuple(x), "capacitor_v": new_cap,
            "previous_pin7_v": pin7_v, "j7_tip_v": x[J7],
            "j7_ring_v": x[J7], "pre_c21_v": x[10],
            "capacitor_currents_a": parts["capacitor_currents_a"],
            "transistor_currents_npn_sign_a": parts["transistor_currents_npn_sign_a"],
            "max_charge_kcl_residual_a": max(abs(value) for value in residual),
            "iterations": iteration,
            "parameters_imposed": parameters}
