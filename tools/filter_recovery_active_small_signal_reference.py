"""24-node ladder plus active Q5-Q8 recovery, feedback open.

Both stages are linearized at their independent DC points; C1/C5 connect
them in AC and C9 bypasses the recovery R6/R7 node to ground.
"""

from __future__ import annotations

import json
import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_ladder_small_signal_reference import capacitance_matrix_f
from filter_recovery_active_dc_reference import EVIDENCE as RECOVERY_EVIDENCE


def coupled_matrices(ladder_dc: dict, recovery_dc: dict) -> tuple[list[list[float]], list[list[float]], float]:
    """Construct 24-node G (S), C (F) with source BUS boundary omitted."""
    data = json.loads(RECOVERY_EVIDENCE.read_text(encoding="utf-8"))
    caps = data["ac_capacitors"]
    if (caps["C5"], caps["C1"], caps["C9"]) != (
            {"farad": 0.22e-6, "between": ["L_Q10C_Q2E", "Q8_BASE"]},
            {"farad": 0.22e-6, "between": ["R_Q11C_Q3E", "Q6_BASE"]},
            {"farad": 100e-6, "between": ["RECOVER_R6_R7", "GROUND"]}):
        raise ValueError("active recovery AC capacitors differ from source")
    ladder_g = ladder_dc["conductance_matrix_s"]
    recovery_g = recovery_dc["conductance_matrix_s"]
    if (len(ladder_g) != 16 or any(len(row) != 16 for row in ladder_g)
            or len(recovery_g) != 8 or any(len(row) != 8 for row in recovery_g)):
        raise ValueError("16-node ladder and eight-node recovery DC matrices required")
    ladder_c, c27 = capacitance_matrix_f()
    g = [[0.0] * 24 for _ in range(24)]
    c = [[0.0] * 24 for _ in range(24)]
    for i in range(16):
        for j in range(16):
            g[i][j], c[i][j] = ladder_g[i][j], ladder_c[i][j]
    for i in range(8):
        for j in range(8):
            g[16 + i][16 + j] = recovery_g[i][j]
    for left, right, value in ((11, 16, caps["C5"]["farad"]),
                               (15, 17, caps["C1"]["farad"])):
        c[left][left] += value
        c[right][right] += value
        c[left][right] -= value
        c[right][left] -= value
    c[23][23] += caps["C9"]["farad"]
    return g, c, c27


def active_recovery_small_signal(*, ladder_dc: dict, recovery_dc: dict,
                                 frequency_hz: float) -> dict:
    """Solve the AC network with BUS=1 V and open C10 emphasis branch."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    g, c, c27 = coupled_matrices(ladder_dc, recovery_dc)
    s = 2j * math.pi * frequency_hz
    system = [[g[i][j] - s * c[i][j] for j in range(24)] for i in range(24)]
    rhs = [0j] * 24
    rhs[6] = -s * c27
    v = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j] * v[j] for j in range(24)) - rhs[i])
                   for i in range(24))
    return {
        "frequency_hz": frequency_hz,
        "ladder_top_differential_v_per_bus_v": v[11] - v[15],
        "recovery_base_differential_v_per_bus_v": v[16] - v[17],
        "recovery_collector_v_per_bus_v": v[21],
        "emphasis_pickoff_r7_r3_v_per_bus_v": v[22],
        "recovery_bypass_r6_r7_v_per_bus_v": v[23],
        "input_admittance_s": s * c27 * (1 - v[6]),
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "emphasis_feedback_open": True,
        "device_parameters_imposed": True,
    }


if __name__ == "__main__":
    from filter_ladder_active_dc_reference import UPPER
    from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
    from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc

    recovery = conditional_recovery_dc(
        is_a={name: 1e-14 for name in DEVICES},
        beta_forward={name: 100 for name in DEVICES},
        beta_reverse={name: 5 for name in DEVICES}, temperature_k=298.15)
    cutoff_inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                           scale_active_ohm=250, contour_pin16_v=0),
                         range_fraction_from_ground=0.1,
                         is26_a=1e-14, is28_a=1e-14,
                         beta26=100, beta28=100, temperature_k=298.15)
    for candidate in (200, 200000):
        ladder = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff_inputs, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
        for frequency in (0, 100, 1000):
            result = active_recovery_small_signal(
                ladder_dc=ladder, recovery_dc=recovery, frequency_hz=frequency)
            print(json.dumps({"r61_ohm": candidate, "frequency_hz": frequency,
                              "pickoff_magnitude": abs(result[
                                  "emphasis_pickoff_r7_r3_v_per_bus_v"]),
                              "ladder_top_magnitude": abs(result[
                                  "ladder_top_differential_v_per_bus_v"]),
                              "kcl_residual": result[
                                  "max_linear_kcl_residual_a_per_bus_v"]}, indent=2))
