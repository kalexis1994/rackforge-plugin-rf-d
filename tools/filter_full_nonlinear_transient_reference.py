"""Offline 24-node nonlinear filter and recovery with C10 emphasis return.

All fourteen transistor pairs of junctions are reevaluated at each Newton
trial. C10 plus its unbranched series resistors use the exact backward Euler
companion relation, including previous capacitor voltage.
"""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import (
    NODE_NAMES as LADDER_NODES, _solve_linear, evaluate_nodal_kcl)
from filter_recovery_active_dc_reference import NODES as RECOVERY_NODES, _evaluate as recovery_kcl
from filter_recovery_active_small_signal_reference import coupled_matrices
from filter_regeneration_reference import _values


NODES = LADDER_NODES + RECOVERY_NODES


def initial_state(*, ladder_dc: dict, recovery_dc: dict) -> dict:
    """Capacitor charges consistent with the two independent DC solutions."""
    nodes = tuple(ladder_dc["nodes_v"][name] for name in LADDER_NODES) + tuple(
        recovery_dc["nodes_v"][name] for name in RECOVERY_NODES)
    return {"node_v": nodes, "c10_capacitor_v": nodes[22] - nodes[7],
            "bus_v": 0.0}


def nonlinear_coupled_step(*, ladder_dc: dict, recovery_dc: dict,
                           previous_node_v: tuple[float, ...],
                           previous_c10_capacitor_v: float,
                           previous_bus_v: float, bus_v: float,
                           dt_s: float, r14_pin7_to_pin6_ohm: float,
                           r73_bottom_side_to_wiper_ohm: float,
                           c10_farads: float | None = None) -> dict:
    """Backward Euler charge/KCL step with absolute node voltages."""
    c10_nominal, r14_total, r73_total, r76 = _values()
    c10 = c10_nominal if c10_farads is None else c10_farads
    if (not math.isfinite(dt_s) or dt_s <= 0
            or not math.isfinite(c10) or not 0.9 * c10_nominal <= c10 <= 1.5 * c10_nominal
            or len(previous_node_v) != 24
            or not all(math.isfinite(v) for v in previous_node_v)
            or not all(math.isfinite(v) for v in (
                previous_c10_capacitor_v, previous_bus_v, bus_v,
                r14_pin7_to_pin6_ohm, r73_bottom_side_to_wiper_ohm))
            or not 0 <= r14_pin7_to_pin6_ohm <= r14_total
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total):
        raise ValueError("finite state, positive step and in-range electrical settings required")
    r30_dc = ladder_dc["network_parameters"]["r30"]
    if not math.isclose(r30_dc, r76 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from transient return")
    rtop = r14_pin7_to_pin6_ohm + r73_total - r73_bottom_side_to_wiper_ohm
    _, cap, c27 = coupled_matrices(ladder_dc, recovery_dc)
    ladder_parameters = ladder_dc["network_parameters"]
    recovery_parameters = recovery_dc["network_parameters"]
    bus_delta = bus_v - previous_bus_v
    gc = c10 / dt_s
    series_be_s = gc / (1 + gc * rtop)
    scales = [1e-5] * 5 + [1e-7] * 3 + [1e-7] * 8 + [1e-6] * 2 + [1e-4] * 6

    def evaluate(x: list[float]) -> tuple[list[float], dict, dict, list[float], float]:
        ladder_residual, ladder_devices = evaluate_nodal_kcl(
            x[:16], **ladder_parameters)
        recovery_residual, recovery_devices = recovery_kcl(
            x[16:], **recovery_parameters)
        dc_residual = ladder_residual + recovery_residual
        return_current = series_be_s * (
            x[22] - x[7] - previous_c10_capacitor_v)
        dc_residual[22] -= return_current
        dc_residual[7] += return_current
        delta = [x[j] - previous_node_v[j] for j in range(24)]
        charge = [sum(cap[i][j] * delta[j] for j in range(24))
                  - (c27 * bus_delta if i == 6 else 0.0)
                  for i in range(24)]
        residual = [dc_residual[i] - charge[i] / dt_s for i in range(24)]
        return residual, ladder_devices, recovery_devices, charge, return_current

    x = list(previous_node_v)
    iterations = 0
    for iteration in range(60):
        residual, ladder_devices, recovery_devices, charge, current = evaluate(x)
        error = max(abs(value / scale) for value, scale in zip(residual, scales))
        if max(abs(value) for value in residual) < 1e-10 and error < 1e-3:
            iterations = iteration
            break
        jacobian = [[0.0] * 24 for _ in range(24)]
        for column in range(24):
            shifted = x.copy()
            shifted[column] += 1e-5
            high, _, _, _, _ = evaluate(shifted)
            for row in range(24):
                jacobian[row][column] = ((high[row] - residual[row])
                                         / 1e-5 / scales[row])
        direction = _solve_linear(jacobian,
                                  [-value / scale for value, scale in zip(residual, scales)])
        accepted = False
        for power in range(28):
            step = 0.5 ** power
            trial = [value + step * change for value, change in zip(x, direction)]
            try:
                trial_residual, _, _, _, _ = evaluate(trial)
            except ValueError:
                continue
            if max(abs(value / scale) for value, scale in zip(trial_residual, scales)) < error:
                x = trial
                accepted = True
                break
        if not accepted:
            raise ValueError("coupled transient Newton step did not decrease KCL/charge error")
    else:
        raise ValueError("coupled transient Newton step did not converge")
    residual, ladder_devices, recovery_devices, charge, current = evaluate(x)
    c10_v = x[22] - x[7] - rtop * current
    return {
        "node_v": tuple(x),
        "c10_capacitor_v": c10_v,
        "c10_farads": c10,
        "return_current_a": current,
        "return_capacitor_current_a": c10 * (
            c10_v - previous_c10_capacitor_v) / dt_s,
        "charge_change_c": dict(zip(NODES, charge)),
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_charge_kcl_residual_a": max(abs(value) for value in residual),
        "base_collector_forward_devices": tuple(
            name for name, device in {**ladder_devices, **recovery_devices}.items()
            if device["v_bc_v"] > 0),
        "iterations": iterations,
        "dt_s": dt_s,
        "offline_reference_only": True,
    }
