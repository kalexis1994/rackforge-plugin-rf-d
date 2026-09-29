"""Conditional isolated DC solution of board-3 headphone amplifier circuit 11."""

from __future__ import annotations

import json
import math

from filter_ladder_ebers_moll_dc_reference import _device, _solve_linear
from headphone_amp_bias_reference import EVIDENCE
from output_diode_reference import diode_current_a
from semiconductor_ideal import thermal_voltage_v


NODES = ("Q16_BASE", "Q16_EMITTER_DIODE_TOP", "DIODE_MIDDLE",
         "DIODE_BOTTOM", "Q11_BASE", "Q11_COLLECTOR", "Q11_EMITTER",
         "Q10_BASE", "Q10_COLLECTOR", "Q10_EMITTER",
         "AMP_OUTPUT_BEFORE_C21")
INITIAL_V = (-8, -7.3, -6.7, -6.1, -7.4, -19.9, -6.7,
             -6.1, -0.1, -6.8, -6.7)


def _graph() -> dict:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    resistors = {row["ref"]: row for row in data["resistors"]}
    caps = {row["ref"]: row for row in data["capacitors"]}
    devices = {row["ref"]: row for row in data["active_devices"]}
    if (set(resistors) != {"R50", "R53", "R36", "R44", "R33", "R32",
                           "R35", "R49", "R40"}
            or set(caps) != {"C19", "C15", "C21"}
            or set(devices) != {"Q16", "Q11", "Q10", "CR1", "CR2"}
            or data["rails"] != {"BOARD3_PIN18": -10, "BOARD3_PIN21": -20,
                                  "BOARD3_PINS9_10": 0}
            or devices["Q16"]["marking"] != "TIS-93"
            or devices["Q11"]["marking"] != "TIS-93"
            or devices["Q10"]["marking"] != "TIS-92"
            or any(devices[name]["marking"] != "1N458A"
                   for name in ("CR1", "CR2"))):
        raise ValueError("board-3 headphone active graph differs from schematic")
    return data


def evaluate_headphone_amp_dc(node_v: list[float], *,
                              transistor_is_a: float,
                              beta_forward: float,
                              beta_reverse: float,
                              temperature_k: float,
                              diode_model: dict,
                              _prepared_graph: dict | None = None) -> tuple[list[float], dict]:
    """Outgoing-current KCL for eleven unknowns; capacitors open at DC."""
    if len(node_v) != len(NODES) or not all(math.isfinite(v) for v in node_v):
        raise ValueError("eleven finite node voltages required")
    if (not all(math.isfinite(v) and v > 0 for v in
                (transistor_is_a, beta_forward, beta_reverse))):
        raise ValueError("positive finite imposed transistor parameters required")
    vt = thermal_voltage_v(temperature_k)
    if diode_model["temperature_k"] != temperature_k:
        raise ValueError("diode and transistor temperatures must agree")
    graph = _graph() if _prepared_graph is None else _prepared_graph
    voltage = dict(zip(NODES, node_v))
    voltage.update(MINUS_10=-10.0, MINUS_20=-20.0, GROUND=0.0)
    kcl = {name: 0.0 for name in NODES}
    resistor_currents = {}
    for row in graph["resistors"]:
        left, right = row["between"]
        current = (voltage[left]-voltage[right])/row["ohm"]
        resistor_currents[row["ref"]] = current
        if left in kcl:
            kcl[left] += current
        if right in kcl:
            kcl[right] -= current
    transistor_currents = {}
    for row in graph["active_devices"]:
        if not row["ref"].startswith("Q"):
            continue
        polarity = -1 if row["marking"] == "TIS-93" else 1
        b, c, e = (row[terminal] for terminal in ("base", "collector", "emitter"))
        current = _device(*(polarity*voltage[name] for name in (b, c, e)),
                          transistor_is_a, beta_forward, beta_reverse, vt)
        transistor_currents[row["ref"]] = current
        for name, outgoing in ((b, polarity*current["base_a"]),
                               (c, polarity*current["collector_a"]),
                               (e, -polarity*current["emitter_a"])):
            if name in kcl:
                kcl[name] += outgoing
    diode_currents = {}
    for row in graph["active_devices"]:
        if not row["ref"].startswith("CR"):
            continue
        anode, cathode = row["anode"], row["cathode"]
        current = diode_current_a(voltage[anode]-voltage[cathode],
                                  model=diode_model, vt=vt)
        diode_currents[row["ref"]] = current
        kcl[anode] += current
        kcl[cathode] -= current
    return [kcl[name] for name in NODES], {
        "resistor_currents_a": resistor_currents,
        "transistor_currents_npn_sign_a": transistor_currents,
        "diode_anode_to_cathode_a": diode_currents}


def headphone_amp_dc_jacobian(node_v: list[float], *,
                              transistor_is_a: float,
                              beta_forward: float,
                              beta_reverse: float,
                              temperature_k: float,
                              diode_model: dict,
                              _prepared_graph: dict | None = None) -> list[list[float]]:
    """Exact 11x11 derivative of outgoing-current KCL at a finite trial."""
    if len(node_v) != len(NODES) or not all(math.isfinite(v) for v in node_v):
        raise ValueError("eleven finite node voltages required")
    if not all(math.isfinite(v) and v > 0 for v in (
            transistor_is_a, beta_forward, beta_reverse)):
        raise ValueError("positive finite imposed transistor parameters required")
    vt = thermal_voltage_v(temperature_k)
    if diode_model["temperature_k"] != temperature_k:
        raise ValueError("diode and transistor temperatures must agree")
    graph = _graph() if _prepared_graph is None else _prepared_graph
    index = {name: i for i, name in enumerate(NODES)}
    voltage = dict(zip(NODES, node_v))
    voltage.update(MINUS_10=-10.0, MINUS_20=-20.0, GROUND=0.0)
    jac = [[0.0]*len(NODES) for _ in NODES]

    def add(row: str, col: str, value: float) -> None:
        if row in index and col in index:
            jac[index[row]][index[col]] += value

    for row in graph["resistors"]:
        left, right = row["between"]
        g = 1/row["ohm"]
        for a, b in ((left, right), (right, left)):
            add(a, a, g)
            add(a, b, -g)
    for row in graph["active_devices"]:
        if not row["ref"].startswith("Q"):
            continue
        b, c, e = (row[key] for key in ("base", "collector", "emitter"))
        polarity = -1 if row["marking"] == "TIS-93" else 1
        xbe = polarity*(voltage[b]-voltage[e])/vt
        xbc = polarity*(voltage[b]-voltage[c])/vt
        if max(xbe, xbc) > 45:
            raise ValueError("trial voltage outside finite BJT exponential domain")
        gf = transistor_is_a*math.exp(xbe)/vt
        gr = transistor_is_a*math.exp(xbc)/vt
        # Polarity appears twice when differentiating a PNP's signed
        # current against its inverted voltages, so the slopes have the
        # same stamp signs as for an NPN at the transformed operating point.
        slopes = {
            b: (gf/beta_forward+gr/beta_reverse,
                -gr/beta_reverse, -gf/beta_forward),
            c: (gf-(1+1/beta_reverse)*gr,
                (1+1/beta_reverse)*gr, -gf),
            e: (-(1+1/beta_forward)*gf+gr,
                -gr, (1+1/beta_forward)*gf),
        }
        for terminal, derivatives in slopes.items():
            for wrt, derivative in zip((b, c, e), derivatives):
                add(terminal, wrt, derivative)
    for row in graph["active_devices"]:
        if not row["ref"].startswith("CR"):
            continue
        anode, cathode = row["anode"], row["cathode"]
        exponent = (voltage[anode]-voltage[cathode])/(
            diode_model["ideality"]*vt)
        if not math.isfinite(exponent) or exponent > 45:
            raise ValueError("diode trial exceeds finite exponential domain")
        g = diode_model["is_a"]*math.exp(exponent)/(
            diode_model["ideality"]*vt)
        for a, b in ((anode, cathode), (cathode, anode)):
            add(a, a, g)
            add(a, b, -g)
    return jac


def conditional_headphone_amp_dc(*, transistor_is_a: float,
                                 beta_forward: float,
                                 beta_reverse: float,
                                 temperature_k: float,
                                 diode_model: dict) -> dict:
    """Damped Newton solution for a specified common TIS family scenario."""
    parameters = dict(transistor_is_a=transistor_is_a,
                      beta_forward=beta_forward, beta_reverse=beta_reverse,
                      temperature_k=temperature_k, diode_model=diode_model,
                      _prepared_graph=_graph())
    x = list(INITIAL_V)
    for iteration in range(80):
        residual, parts = evaluate_headphone_amp_dc(x, **parameters)
        error = max(abs(value) for value in residual)
        if error < 1e-11:
            break
        jacobian = headphone_amp_dc_jacobian(x, **parameters)
        direction = _solve_linear(jacobian, [-value for value in residual])
        for power in range(24):
            step = 0.5**power
            trial = [voltage+step*change for voltage, change in zip(x, direction)]
            try:
                trial_residual, _ = evaluate_headphone_amp_dc(trial, **parameters)
                trial_error = max(abs(value) for value in trial_residual)
            except ValueError:
                continue
            if trial_error < error:
                x = trial
                break
        else:
            raise ValueError("headphone DC Newton iteration did not decrease KCL")
    else:
        raise ValueError("headphone DC Newton iteration did not converge")
    residual, parts = evaluate_headphone_amp_dc(x, **parameters)
    return {"node_v": dict(zip(NODES, x)), "iterations": iteration,
            "max_kcl_residual_a": max(abs(value) for value in residual),
            "parts": parts, "parameters_imposed": parameters,
            "c19_c15_c21_dc_open": True}
