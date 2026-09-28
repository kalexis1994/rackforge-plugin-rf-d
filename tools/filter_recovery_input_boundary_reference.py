"""Passive Q2/Q3-to-Q8/Q6 coupling boundary around conditional ladder DC.

Two 0.22-uF capacitors and 47-kohm shunts load the ladder at small signal.
Q8/Q6 base currents are imposed zero; active recovery is not represented.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_ladder_small_signal_reference import capacitance_matrix_f


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_recovery_input_boundary.json"
OUTPUT_NODES = ("Q8_BASE", "Q6_BASE")


def loaded_matrices(dc_solution: dict) -> tuple[list[list[float]], list[list[float]], float]:
    """Return 18-node G in S, C in F, and C27 in F."""
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    branches = data["branches"]
    expected = (("C5", "L_Q10C_Q2E", "Q8_BASE", "R31"),
                ("C1", "R_Q11C_Q3E", "Q6_BASE", "R38"))
    if (data["schematic"]["figure"], data["parts_list"]["table"],
            tuple((b["capacitor"], b["from"], b["to"], b["shunt_resistor"])
                  for b in branches)) != ("9-11", "7-8", expected):
        raise ValueError("recovery-input boundary differs from documentary source")
    if any(b["farad"] != 0.22e-6 or b["shunt_ohm"] != 47000 for b in branches):
        raise ValueError("recovery coupling values differ from parts list")
    base_c, c27 = capacitance_matrix_f()
    base_g = dc_solution["conductance_matrix_s"]
    if len(base_g) != 16 or any(len(row) != 16 for row in base_g):
        raise ValueError("16-node ladder conductance matrix required")
    g = [[0.0] * 18 for _ in range(18)]
    c = [[0.0] * 18 for _ in range(18)]
    for i in range(16):
        for j in range(16):
            g[i][j], c[i][j] = base_g[i][j], base_c[i][j]
    for source, sink, branch in ((11, 16, branches[0]), (15, 17, branches[1])):
        value = branch["farad"]
        c[source][source] += value
        c[sink][sink] += value
        c[source][sink] -= value
        c[sink][source] -= value
        # All G residuals use incoming minus outgoing KCL.
        g[sink][sink] -= 1 / branch["shunt_ohm"]
    return g, c, c27


def loaded_small_signal_at_frequency(*, dc_solution: dict, frequency_hz: float) -> dict:
    """Resolve passive recovery-input loading for ideal 1-V AC BUS drive."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency in hertz required")
    g, c, c27 = loaded_matrices(dc_solution)
    s = 2j * math.pi * frequency_hz
    system = [[g[i][j] - s * c[i][j] for j in range(18)] for i in range(18)]
    rhs = [0j] * 18
    rhs[6] = -s * c27
    voltage = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j] * voltage[j] for j in range(18)) - rhs[i])
                   for i in range(18))
    return {
        "frequency_hz": frequency_hz,
        "top_emitter_differential_v_per_bus_v": voltage[11] - voltage[15],
        "recovery_base_differential_v_per_bus_v": voltage[16] - voltage[17],
        "q8_base_v_per_bus_v": voltage[16],
        "q6_base_v_per_bus_v": voltage[17],
        "input_admittance_s": s * c27 * (1 - voltage[6]),
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "recovery_transistor_base_currents_imposed_zero": True,
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
        for frequency in (0, 100, 1000):
            result = loaded_small_signal_at_frequency(
                dc_solution=dc, frequency_hz=frequency)
            print(json.dumps({"r61_ohm": candidate, "frequency_hz": frequency,
                              "top_emitter_magnitude": abs(result[
                                  "top_emitter_differential_v_per_bus_v"]),
                              "recovery_base_magnitude": abs(result[
                                  "recovery_base_differential_v_per_bus_v"]),
                              "kcl_residual": result[
                                  "max_linear_kcl_residual_a_per_bus_v"]}, indent=2))
