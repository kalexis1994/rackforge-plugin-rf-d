"""40-node conditional AC through both active VCA multipliers.

The 15-node coupled VCA DC Jacobian shares Q16/Q15 bases with the 27-node
filter/recovery core. Supply and control boundaries have zero AC movement.
Q12/Q17 conversion and the final output load are still absent.
"""

from __future__ import annotations

import math

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_vca1_loaded_small_signal_reference import loaded_matrices
from vca1_input_boundary_reference import _values as vca_values
from vca_cascaded_dc_reference import NODES as VCA_NODES


NODE_COUNT = 40
VCA_TO_SYSTEM = (25, 26, 27, 28, 29, 30, 31, 32, 33,
                 34, 35, 36, 37, 38, 39)


def cascaded_loaded_matrices(*, ladder_dc: dict, recovery_dc: dict,
                             cascaded_vca_dc: dict) -> tuple[list[list[float]],
                                                              list[list[float]], float]:
    """Insert coupled VCA Jacobian once, preserving C6/C15 and BUS C27."""
    old_g, old_c, bus_c = loaded_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    g = [[0.0] * NODE_COUNT for _ in range(NODE_COUNT)]
    c = [[0.0] * NODE_COUNT for _ in range(NODE_COUNT)]
    for row in range(27):
        for col in range(27):
            g[row][col] = old_g[row][col]
            c[row][col] = old_c[row][col]
    _, _, r34, _, r36 = vca_values()
    g[25][25] += 1 / r34
    g[26][26] += 1 / r34 + 1 / r36
    g[25][26] -= 1 / r34
    g[26][25] -= 1 / r34
    local = cascaded_vca_dc["conductance_matrix_s"]
    if len(local) != len(VCA_NODES) or any(len(row) != len(VCA_NODES) for row in local):
        raise ValueError("cascaded VCA Jacobian must have fifteen rows and columns")
    for row, system_row in enumerate(VCA_TO_SYSTEM):
        for col, system_col in enumerate(VCA_TO_SYSTEM):
            g[system_row][system_col] += local[row][col]
    return g, c, bus_c


def filter_with_cascaded_vca(*, ladder_dc: dict, recovery_dc: dict,
                             cascaded_vca_dc: dict, frequency_hz: float,
                             r14_pin7_to_pin6_ohm: float,
                             r73_bottom_side_to_wiper_ohm: float,
                             c10_farads: float | None = None) -> dict:
    """BUS=1 V phasor normalization through the second VCA collectors."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    r30_dc = ladder_dc["network_parameters"]["r30"]
    if not math.isclose(r30_dc, 330 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 left segment differs from AC return")
    if not (cascaded_vca_dc["upper_supply_and_controls_imposed"]
            and cascaded_vca_dc["output_conversion_base_currents_imposed_zero"]):
        raise ValueError("cascaded VCA DC boundary differs from AC model")
    y_return = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    g, c, bus_c = cascaded_loaded_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_vca_dc=cascaded_vca_dc)
    s = 2j * math.pi * frequency_hz
    system = [[g[i][j] - s * c[i][j] for j in range(NODE_COUNT)]
              for i in range(NODE_COUNT)]
    base, tap = 7, 22
    system[base][base] -= y_return
    system[tap][tap] -= y_return
    system[base][tap] += y_return
    system[tap][base] += y_return
    rhs = [0j] * NODE_COUNT
    rhs[6] = -s * bus_c
    v = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j] * v[j] for j in range(NODE_COUNT))
                       - rhs[i]) for i in range(NODE_COUNT))
    r2, _, _, _, _ = vca_values()
    return {
        "frequency_hz": frequency_hz,
        "node_v_per_bus_v": tuple(v),
        "vca_node_v_per_bus_v": dict(zip(VCA_NODES, (v[i] for i in VCA_TO_SYSTEM))),
        "recovery_collector_v_per_bus_v": v[21],
        "q16_base_v_per_bus_v": v[25],
        "first_vca_differential_collector_v_per_bus_v": v[30] - v[31],
        "second_vca_differential_collector_v_per_bus_v": v[37] - v[38],
        "first_balance_wiper_v_per_bus_v": v[33],
        "second_balance_wiper_v_per_bus_v": v[39],
        "r2_current_a_per_bus_v": (v[21] - v[24]) / r2,
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "upper_supply_and_controls_ac_ground_imposed": True,
        "output_conversion_base_currents_imposed_zero": True,
    }
