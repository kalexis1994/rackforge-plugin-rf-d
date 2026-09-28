"""Offline nonlinear 16-node board-4 ladder transient with Ebers-Moll BJTs.

Backward Euler conserves the six nominal capacitor charges. Every Newton
evaluation recomputes both transistor junction currents at current voltages.
"""

from __future__ import annotations

import json
import math

from filter_ladder_ebers_moll_dc_reference import (
    NODE_NAMES, _solve_linear, evaluate_nodal_kcl)
from filter_ladder_small_signal_reference import capacitance_matrix_f


def nonlinear_step(*, dc_solution: dict, dt_s: float,
                   previous_node_v: tuple[float, ...],
                   previous_bus_v: float, bus_v: float) -> dict:
    """Implicit circuit step in absolute volts for a prescribed BUS voltage.

    The DC Q28 current-source parameters are fixed during a step. Recovery,
    emphasis and external loading remain disconnected boundaries.
    """
    if (not math.isfinite(dt_s) or dt_s <= 0
            or len(previous_node_v) != 16
            or not all(math.isfinite(value) for value in previous_node_v)
            or not math.isfinite(previous_bus_v) or not math.isfinite(bus_v)):
        raise ValueError("positive dt and finite 16-node and BUS voltages required")
    parameters = dc_solution["network_parameters"]
    c, c27 = capacitance_matrix_f()
    change_bus = bus_v - previous_bus_v
    scales = [1e-5] * 5 + [1e-7] * 3 + [1e-7] * 8

    def evaluate(x: list[float]) -> tuple[list[float], dict, list[float]]:
        dc_residual, devices = evaluate_nodal_kcl(x, **parameters)
        change = [x[j] - previous_node_v[j] for j in range(16)]
        charge_change = [sum(c[i][j] * change[j] for j in range(16))
                         - (c27 * change_bus if i == 6 else 0.0)
                         for i in range(16)]
        residual = [dc_residual[i] - charge_change[i] / dt_s
                    for i in range(16)]
        return residual, devices, charge_change

    x = list(previous_node_v)
    iterations = 0
    for iteration in range(60):
        residual, devices, charge = evaluate(x)
        error = max(abs(value / scale) for value, scale in zip(residual, scales))
        if max(abs(value) for value in residual) < 1e-10 and error < 1e-3:
            iterations = iteration
            break
        jacobian = [[0.0] * 16 for _ in range(16)]
        for column in range(16):
            shifted = x.copy()
            shifted[column] += 1e-5
            high, _, _ = evaluate(shifted)
            for row in range(16):
                jacobian[row][column] = ((high[row] - residual[row])
                                         / 1e-5 / scales[row])
        direction = _solve_linear(jacobian,
                                  [-value / scale for value, scale in zip(residual, scales)])
        accepted = False
        for power in range(28):
            step = 0.5 ** power
            trial = [value + step * delta for value, delta in zip(x, direction)]
            try:
                trial_residual, _, _ = evaluate(trial)
            except ValueError:
                continue
            trial_error = max(abs(value / scale)
                              for value, scale in zip(trial_residual, scales))
            if trial_error < error:
                x = trial
                accepted = True
                break
        if not accepted:
            raise ValueError("nonlinear ladder step did not decrease charge/KCL residual")
    else:
        raise ValueError("nonlinear ladder step did not converge")

    residual, devices, charge = evaluate(x)
    input_current = c27 * ((bus_v - x[6])
                           - (previous_bus_v - previous_node_v[6])) / dt_s
    return {
        "node_v": tuple(x),
        "top_differential_v": x[11] - x[15],
        "board_input_current_a": input_current,
        "charge_change_c": dict(zip(NODE_NAMES, charge)),
        "kcl_residuals_a": dict(zip(NODE_NAMES, residual)),
        "max_charge_kcl_residual_a": max(abs(value) for value in residual),
        "base_collector_forward_devices": tuple(
            name for name, device in devices.items() if device["v_bc_v"] > 0),
        "iterations": iterations,
        "dt_s": dt_s,
        "offline_reference_only": True,
    }


if __name__ == "__main__":
    from filter_ladder_active_dc_reference import UPPER
    from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc

    cutoff_inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                           scale_active_ohm=250, contour_pin16_v=0),
                         range_fraction_from_ground=0.1,
                         is26_a=1e-14, is28_a=1e-14,
                         beta26=100, beta28=100, temperature_k=298.15)
    for candidate in (200, 200000):
        dc = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff_inputs, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
        initial = tuple(dc["nodes_v"][name] for name in NODE_NAMES)
        for input_v in (0.001, 0.1):
            result = nonlinear_step(
                dc_solution=dc, dt_s=1/48000,
                previous_node_v=initial, previous_bus_v=0, bus_v=input_v)
            print(json.dumps({"r61_ohm": candidate, "bus_step_v": input_v,
                              "top_differential_change_v": (
                                  result["top_differential_v"] - initial[11] + initial[15]),
                              "iterations": result["iterations"],
                              "max_charge_kcl_residual_a": result[
                                  "max_charge_kcl_residual_a"]}, indent=2))
