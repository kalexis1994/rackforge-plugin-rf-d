"""27-node filter/recovery/emphasis AC with passive first-VCA entrance.

R2 and C6 load the recovery collector. Q16/Q15 base currents, first-VCA
balance network and subsequent active stages remain open boundaries.
"""

from __future__ import annotations

import math

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_recovery_active_small_signal_reference import coupled_matrices
from vca1_input_boundary_reference import _values as vca_values


def loaded_matrices(*, ladder_dc: dict,
                    recovery_dc: dict) -> tuple[list[list[float]], list[list[float]], float]:
    """27-node DC conductance and capacitor matrices, before C10 feedback."""
    r2, c6, r34, c15, r36 = vca_values()
    core_g, core_c, c27 = coupled_matrices(ladder_dc, recovery_dc)
    g = [[0.0] * 27 for _ in range(27)]
    c = [[0.0] * 27 for _ in range(27)]
    for row in range(24):
        for column in range(24):
            g[row][column] = core_g[row][column]
            c[row][column] = core_c[row][column]
    def stamp(matrix, left, right, value):
        matrix[left][left] += value
        if right is not None:
            matrix[right][right] += value
            matrix[left][right] -= value
            matrix[right][left] -= value
    stamp(g, 21, 24, -1 / r2)
    stamp(c, 24, 25, c6)
    stamp(g, 25, 26, -1 / r34)
    stamp(g, 26, None, -1 / r36)
    stamp(c, 26, None, c15)
    return g, c, c27


def filter_with_passive_vca1(*, ladder_dc: dict, recovery_dc: dict,
                             frequency_hz: float,
                             r14_pin7_to_pin6_ohm: float,
                             r73_bottom_side_to_wiper_ohm: float,
                             c10_farads: float | None = None) -> dict:
    """Solve all circuit nodes for an ideal BUS=1 V perturbation."""
    r2, _, _, _, _ = vca_values()
    r30_dc = ladder_dc["network_parameters"]["r30"]
    if not math.isclose(r30_dc, 330 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 left segment differs from AC return")
    y_return = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    g, c, c27 = loaded_matrices(ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    s = 2j * math.pi * frequency_hz
    system = [[g[i][j] - s * c[i][j] for j in range(27)] for i in range(27)]
    base, tap = 7, 22
    system[base][base] -= y_return
    system[tap][tap] -= y_return
    system[base][tap] += y_return
    system[tap][base] += y_return
    rhs = [0j] * 27
    rhs[6] = -s * c27
    v = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j] * v[j] for j in range(27)) - rhs[i])
                   for i in range(27))
    return {
        "frequency_hz": frequency_hz,
        "node_v_per_bus_v": tuple(v),
        "recovery_collector_v_per_bus_v": v[21],
        "recovery_tap_v_per_bus_v": v[22],
        "q16_base_v_per_bus_v": v[25],
        "q15_base_v_per_bus_v": v[26],
        "first_vca_differential_base_v_per_bus_v": v[25] - v[26],
        "r2_current_a_per_bus_v": (v[21] - v[24]) / r2,
        "ladder_top_differential_v_per_bus_v": v[11] - v[15],
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "vca_base_currents_imposed_zero": True,
        "first_vca_balance_open": True,
    }


if __name__ == "__main__":
    import json

    from filter_ladder_active_dc_reference import UPPER
    from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
    from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc

    recovery = conditional_recovery_dc(
        is_a={name: 1e-14 for name in DEVICES},
        beta_forward={name: 100 for name in DEVICES},
        beta_reverse={name: 5 for name in DEVICES}, temperature_k=298.15)
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250, contour_pin16_v=0),
                  range_fraction_from_ground=0.1,
                  is26_a=1e-14, is28_a=1e-14,
                  beta26=100, beta28=100, temperature_k=298.15)
    for r61 in (200, 200000):
        ladder = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)
        for frequency in (0, 30, 100, 300, 1000):
            out = filter_with_passive_vca1(
                ladder_dc=ladder, recovery_dc=recovery,
                frequency_hz=frequency, r14_pin7_to_pin6_ohm=0,
                r73_bottom_side_to_wiper_ohm=500)
            print(json.dumps({
                "r61_ohm": r61, "frequency_hz": frequency,
                "collector_magnitude": abs(out["recovery_collector_v_per_bus_v"]),
                "q16_magnitude": abs(out["q16_base_v_per_bus_v"]),
                "kcl_residual": out["max_linear_kcl_residual_a_per_bus_v"]}))
