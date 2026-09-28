"""33-node conditional AC: ladder, recovery, EMPHASIS and active first VCA.

The eight-node Q16/Q15/Q18 Jacobian is stamped at its own DC point. The
balance wiper and loudness source are AC-ground boundaries; Q14/Q13 are open.
"""

from __future__ import annotations

import math

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_vca1_loaded_small_signal_reference import loaded_matrices
from vca1_active_core_dc_reference import NODES as VCA_NODES
from vca1_input_boundary_reference import _values as vca_values


VCA_TO_SYSTEM = (25, 26, 27, 28, 29, 30, 31, 32)
NODE_COUNT = 33


def active_loaded_matrices(*, ladder_dc: dict, recovery_dc: dict,
                           vca_dc: dict) -> tuple[list[list[float]], list[list[float]], float]:
    """Stamp VCA local conductance once; preserve C6/C15 in the 27-node core."""
    g27, c27_matrix, bus_c = loaded_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    g = [[0.0] * NODE_COUNT for _ in range(NODE_COUNT)]
    c = [[0.0] * NODE_COUNT for _ in range(NODE_COUNT)]
    for row in range(27):
        for col in range(27):
            g[row][col] = g27[row][col]
            c[row][col] = c27_matrix[row][col]
    _, _, r34, _, r36 = vca_values()
    # These passive terms exist in both matrices. Remove the 27-node copies
    # before adding the complete eight-node local Jacobian.
    g[25][25] += 1 / r34
    g[26][26] += 1 / r34 + 1 / r36
    g[25][26] -= 1 / r34
    g[26][25] -= 1 / r34
    vca_g = vca_dc["conductance_matrix_s"]
    if len(vca_g) != len(VCA_NODES) or any(len(row) != len(VCA_NODES) for row in vca_g):
        raise ValueError("first-VCA Jacobian must have eight rows and columns")
    for row, system_row in enumerate(VCA_TO_SYSTEM):
        for col, system_col in enumerate(VCA_TO_SYSTEM):
            g[system_row][system_col] += vca_g[row][col]
    return g, c, bus_c


def filter_with_active_vca1(*, ladder_dc: dict, recovery_dc: dict,
                            vca_dc: dict, frequency_hz: float,
                            r14_pin7_to_pin6_ohm: float,
                            r73_bottom_side_to_wiper_ohm: float,
                            c10_farads: float | None = None) -> dict:
    """BUS=1 V small-signal phasor, not a physical 1 V drive level."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    r30_dc = ladder_dc["network_parameters"]["r30"]
    if not math.isclose(r30_dc, 330 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 left segment differs from AC return")
    if not (vca_dc["external_wiper_and_loudness_voltages_imposed"]
            and vca_dc["second_vca_base_currents_imposed_zero"]):
        raise ValueError("first-VCA DC boundary differs from AC model")
    y_return = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    g, c, bus_c = active_loaded_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc, vca_dc=vca_dc)
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
        "q15_base_v_per_bus_v": v[26],
        "first_vca_differential_base_v_per_bus_v": v[25] - v[26],
        "first_vca_differential_collector_v_per_bus_v": v[30] - v[31],
        "r2_current_a_per_bus_v": (v[21] - v[24]) / r2,
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "vca_wiper_and_loudness_ac_ground_imposed": True,
        "second_vca_base_currents_imposed_zero": True,
    }
