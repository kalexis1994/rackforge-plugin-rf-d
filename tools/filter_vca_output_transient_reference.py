"""Offline 48-node nonlinear transient through C2 and loaded output pins.

All 23 BJT laws are reevaluated each step. The open-diode condition is
checked at every accepted point; this is not a clipping or realtime model.
"""

from __future__ import annotations

import math

from filter_full_nonlinear_transient_reference import initial_state
from filter_ladder_ebers_moll_dc_reference import _solve_linear, evaluate_nodal_kcl
from filter_recovery_active_dc_reference import _evaluate as recovery_kcl
from filter_regeneration_reference import _values as regeneration_values
from filter_vca_output_small_signal_reference import (
    NODE_COUNT, LOCAL_TO_SYSTEM, loaded_output_matrices)
from vca1_input_boundary_reference import _values as vca_values
from vca_cascaded_output_dc_reference import _evaluate as output_kcl
from vca_output_conversion_dc_reference import _parts as output_parts


def initial_output_state(*, ladder_dc: dict, recovery_dc: dict,
                         cascaded_output_dc: dict) -> dict:
    """C6_LEFT follows recovery, C2_RIGHT is at ground behind open C2."""
    core = initial_state(ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    local = tuple(cascaded_output_dc["nodes_v"].values())
    if len(local) != 22:
        raise ValueError("22 coupled VCA/output DC voltages required")
    x = core["node_v"] + (core["node_v"][21],) + local + (0.0,)
    return {"node_v": x, "c10_capacitor_v": core["c10_capacitor_v"],
            "bus_v": 0.0}


def nonlinear_output_step(*, ladder_dc: dict, recovery_dc: dict,
                          cascaded_output_dc: dict,
                          previous_node_v: tuple[float, ...],
                          previous_c10_capacitor_v: float,
                          previous_bus_v: float, bus_v: float,
                          dt_s: float, r14_pin7_to_pin6_ohm: float,
                          r73_bottom_side_to_wiper_ohm: float,
                          main_load_ohm: float,
                          headphone_input_ohm: float,
                          c10_farads: float | None = None) -> dict:
    """Backward-Euler step with explicit C4/C2 charge and two output loads."""
    c10_nominal, r14_total, r73_total, r76 = regeneration_values()
    c10 = c10_nominal if c10_farads is None else c10_farads
    r2, _, _, _, _ = vca_values()
    if (len(previous_node_v) != NODE_COUNT
            or not all(math.isfinite(v) for v in previous_node_v)
            or not all(math.isfinite(v) for v in (
                previous_c10_capacitor_v, previous_bus_v, bus_v, dt_s,
                r14_pin7_to_pin6_ohm, r73_bottom_side_to_wiper_ohm,
                main_load_ohm, headphone_input_ohm, c10))
            or dt_s <= 0 or main_load_ohm <= 0 or headphone_input_ohm <= 0
            or not 0.9*c10_nominal <= c10 <= 1.5*c10_nominal
            or not 0 <= r14_pin7_to_pin6_ohm <= r14_total
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total):
        raise ValueError("finite 48-node state and in-range step/loads required")
    lp = ladder_dc["network_parameters"]
    rp = recovery_dc["network_parameters"]
    vp = cascaded_output_dc["network_parameters"]
    if not math.isclose(lp["r30"], r76 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from transient return")
    if not cascaded_output_dc["input_and_controls_imposed"]:
        raise ValueError("VCA/output DC boundary differs from transient model")
    _, cap, bus_c = loaded_output_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        main_load_ohm=main_load_ohm,
        headphone_input_ohm=headphone_input_ohm)
    r = output_parts()
    output_conductance = (1/(r["R75"]+main_load_ohm)
                          + 1/(r["R77"]+headphone_input_ohm))
    rtop = r14_pin7_to_pin6_ohm + r73_total - r73_bottom_side_to_wiper_ohm
    gc10 = c10/dt_s
    y10 = gc10/(1 + gc10*rtop)
    delta_bus = bus_v - previous_bus_v
    scales = ([1e-5]*5 + [1e-7]*3 + [1e-7]*8
              + [1e-6]*2 + [1e-4]*6 + [1e-5]
              + [1e-5, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-5, 1e-3]
              + [1e-3]*6 + [1e-3]*8)

    def evaluate(x: list[float]) -> tuple[list[float], list[float], float, dict]:
        if not 0 <= x[46] <= vp["plus_v"]:
            raise ValueError("diode-open transient domain exceeded")
        ladder, _ = evaluate_nodal_kcl(x[:16], **lp)
        recovery, _ = recovery_kcl(x[16:24], **rp)
        local, devices = output_kcl([x[i] for i in LOCAL_TO_SYSTEM], **vp)
        f = ladder + recovery + [0.0]*24
        r2_current = (x[21] - x[24])/r2
        f[21] -= r2_current
        f[24] += r2_current
        for index, value in zip(LOCAL_TO_SYSTEM, local):
            f[index] += value
        f[47] -= output_conductance*x[47]
        i10 = y10*(x[22] - x[7] - previous_c10_capacitor_v)
        f[22] -= i10
        f[7] += i10
        dv = [x[j]-previous_node_v[j] for j in range(NODE_COUNT)]
        charge = [sum(cap[i][j]*dv[j] for j in range(NODE_COUNT))
                  - (bus_c*delta_bus if i == 6 else 0.0)
                  for i in range(NODE_COUNT)]
        return ([f[i]-charge[i]/dt_s for i in range(NODE_COUNT)],
                charge, i10, devices)

    x = list(previous_node_v)
    for iteration in range(80):
        residual, charge, i10, devices = evaluate(x)
        error = max(abs(v/s) for v, s in zip(residual, scales))
        if max(abs(v) for v in residual) < 1e-10 and error < 1e-3:
            break
        jacobian = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
        for col in range(NODE_COUNT):
            trial = x.copy()
            trial[col] += 1e-5
            high, _, _, _ = evaluate(trial)
            for row in range(NODE_COUNT):
                jacobian[row][col] = ((high[row]-residual[row])
                                      / 1e-5 / scales[row])
        direction = _solve_linear(jacobian,
                                  [-v/s for v, s in zip(residual, scales)])
        for power in range(32):
            candidate = [v+0.5**power*dv for v, dv in zip(x, direction)]
            try:
                next_residual, _, _, _ = evaluate(candidate)
            except ValueError:
                continue
            if max(abs(v/s) for v, s in zip(next_residual, scales)) < error:
                x = candidate
                break
        else:
            raise ValueError("output transient Newton step did not decrease residual")
    else:
        raise ValueError("output transient Newton iteration did not converge")
    residual, charge, i10, devices = evaluate(x)
    c10_v = x[22] - x[7] - rtop*i10
    return {
        "node_v": tuple(x), "c10_capacitor_v": c10_v,
        "bus_v": bus_v, "q17_collector_v": x[46],
        "c2_right_v": x[47],
        "main_pin21_v": x[47]*main_load_ohm/(r["R75"]+main_load_ohm),
        "headphone_pin22_v": x[47]*headphone_input_ohm/(
            r["R77"]+headphone_input_ohm),
        "main_pin21_current_a": x[47]/(r["R75"]+main_load_ohm),
        "headphone_pin22_current_a": x[47]/(
            r["R77"]+headphone_input_ohm),
        "r2_current_a": (x[21]-x[24])/r2,
        "c6_current_a": charge[24]/dt_s,
        "c2_current_a": charge[46]/dt_s,
        "return_current_a": i10,
        "charge_change_c": tuple(charge),
        "max_charge_kcl_residual_a": max(abs(v) for v in residual),
        "iterations": iteration, "offline_reference_only": True,
        "diodes_assumed_open": True,
    }
