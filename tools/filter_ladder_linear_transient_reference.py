"""Backward-Euler charge-conserving transient of the 16-node linear core.

This is an offline reference around one imposed DC point, not an audio engine.
BUS voltage is an ideal boundary and recovery/emphasis remain open.
"""

from __future__ import annotations

import json
import math

from filter_ladder_ebers_moll_dc_reference import NODE_NAMES, _solve_linear
from filter_ladder_small_signal_reference import capacitance_matrix_f


def linear_step(*, dc_solution: dict, dt_s: float,
                previous_node_delta_v: tuple[float, ...],
                previous_bus_delta_v: float,
                bus_delta_v: float) -> dict:
    """Implicit step in V relative to DC; BUS change drives C27.

    G uses incoming-minus-outgoing KCL. The discrete capacitor term is
    -C(x_n-x_prev)/dt and the BUS contribution is +C27 ΔBUS/dt at BASE.
    """
    if (not math.isfinite(dt_s) or dt_s <= 0
            or len(previous_node_delta_v) != 16
            or not all(math.isfinite(v) for v in previous_node_delta_v)
            or not math.isfinite(previous_bus_delta_v)
            or not math.isfinite(bus_delta_v)):
        raise ValueError("positive dt and finite 16-node and BUS perturbations required")
    g = dc_solution["conductance_matrix_s"]
    if len(g) != 16 or any(len(row) != 16 for row in g):
        raise ValueError("16-node DC conductance matrix required")
    c, c27 = capacitance_matrix_f()
    system = [[g[i][j] - c[i][j] / dt_s for j in range(16)] for i in range(16)]
    rhs = [-sum(c[i][j] * previous_node_delta_v[j] for j in range(16)) / dt_s
           for i in range(16)]
    rhs[6] -= c27 * (bus_delta_v - previous_bus_delta_v) / dt_s
    next_v = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j] * next_v[j] for j in range(16)) - rhs[i])
                   for i in range(16))
    input_current = c27 * ((bus_delta_v - next_v[6])
                           - (previous_bus_delta_v - previous_node_delta_v[6])) / dt_s
    return {
        "node_delta_v": tuple(next_v),
        "top_differential_delta_v": next_v[11] - next_v[15],
        "board_input_current_delta_a": input_current,
        "max_discrete_kcl_residual_a": residual,
        "dt_s": dt_s,
        "linearized_about_imposed_dc": True,
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
        previous = (0.0,) * len(NODE_NAMES)
        old_bus = 0.0
        peak = 0.0
        final = None
        for _ in range(480):
            final = linear_step(dc_solution=dc, dt_s=1/48000,
                                previous_node_delta_v=previous,
                                previous_bus_delta_v=old_bus,
                                bus_delta_v=0.001)
            previous = final["node_delta_v"]
            old_bus = 0.001
            peak = max(peak, abs(final["top_differential_delta_v"]))
        print(json.dumps({"r61_ohm": candidate, "peak_top_diff_v": peak,
                          "top_diff_after_10ms_v": final["top_differential_delta_v"],
                          "max_kcl_residual_a_last": final[
                              "max_discrete_kcl_residual_a"]}, indent=2))
