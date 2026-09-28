"""Linear AC core of board-4 ladder around an Ebers-Moll DC solution.

BUS is an ideal one-volt small-signal source through C27. The top differential
emitter nodes are observed unloaded; recovery and external feedback are open.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_input_reference import _parts
from filter_ladder_ebers_moll_dc_reference import NODE_NAMES, _solve_linear


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_ladder_ac_core.json"


def _capacitances() -> tuple[tuple[tuple[int, int, float], ...], float, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    expected = (
        ("C16", "L_Q29C_Q23E", "R_Q30C_Q24E"),
        ("C11", "L_Q23C_Q19E", "R_Q24C_Q20E"),
        ("C7", "L_Q19C_Q10E", "R_Q20C_Q11E"),
        ("C3", "L_Q10C_Q2E", "R_Q11C_Q3E"))
    actual = tuple((entry["ref"], *entry["between"])
                   for entry in data["interstage_capacitors"])
    if (data["schematic"]["figure"], data["parts_list"]["table"], actual) != (
            "9-11", "7-8", expected):
        raise ValueError("ladder AC topology differs from documentary source")
    if any(entry["farad"] != 68e-9 for entry in data["interstage_capacitors"]):
        raise ValueError("ladder cell capacitor values differ from parts list")
    parts = _parts()
    if (data["bottom_capacitor"]["farad"] != parts["C24"]["farad"]
            or data["input_capacitor"]["farad"] != parts["C27"]["farad"]):
        raise ValueError("input capacitors differ from board-4 evidence")
    edges = tuple((NODE_NAMES.index(left), NODE_NAMES.index(right), entry["farad"])
                  for entry, (_, left, right) in zip(data["interstage_capacitors"], expected))
    return edges, parts["C24"]["farad"], parts["C27"]["farad"]


def capacitance_matrix_f() -> tuple[tuple[tuple[float, ...], ...], float]:
    """Symmetric 16-node charge matrix and BUS-to-base capacitance in F."""
    edges, c24, c27 = _capacitances()
    c = [[0.0] * 16 for _ in range(16)]
    for left, right, value in edges:
        c[left][left] += value
        c[right][right] += value
        c[left][right] -= value
        c[right][left] -= value
    c[4][4] += c24
    c[6][6] += c27
    return tuple(tuple(row) for row in c), c27


def small_signal_at_frequency(*, dc_solution: dict, frequency_hz: float) -> dict:
    """Solve (G - jωC)v = -jω C27 e_BASE for BUS=1 V AC.

    The DC KCL used incoming-minus-outgoing signs; the capacitor terms are
    subtracted accordingly. Returned complex transfers use volts per volt.
    """
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency in hertz required")
    edges, _, _ = _capacitances()
    c, c27 = capacitance_matrix_f()
    g = dc_solution["conductance_matrix_s"]
    if len(g) != 16 or any(len(row) != 16 for row in g):
        raise ValueError("16-node DC conductance matrix required")
    angular = 2 * math.pi * frequency_hz
    s = 1j * angular
    system = [[g[i][j] - s * c[i][j] for j in range(16)] for i in range(16)]
    rhs = [0j] * 16
    rhs[6] = -s * c27
    voltage = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j] * voltage[j] for j in range(16)) - rhs[i])
                   for i in range(16))
    top_difference = voltage[11] - voltage[15]
    cap_currents = {ref: s * value * (voltage[left] - voltage[right])
                    for (left, right, value), ref in zip(
                        edges, ("C16", "C11", "C7", "C3"))}
    return {
        "frequency_hz": frequency_hz,
        "node_v_per_bus_v": dict(zip(NODE_NAMES, voltage)),
        "top_differential_v_per_bus_v": top_difference,
        "top_differential_magnitude": abs(top_difference),
        "input_admittance_s": s * c27 * (1 - voltage[6]),
        "interstage_capacitor_currents_a_per_bus_v": cap_currents,
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "core_output_load_imposed_open": True,
        "emphasis_feedback_open": True,
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
        results = [small_signal_at_frequency(dc_solution=dc, frequency_hz=f)
                   for f in (0, 100, 1000, 10000)]
        print(json.dumps({"r61_ohm": candidate,
                          "response": [{"frequency_hz": row["frequency_hz"],
                                        "top_differential_magnitude": row[
                                            "top_differential_magnitude"],
                                        "max_kcl_residual": row[
                                            "max_linear_kcl_residual_a_per_bus_v"]}
                                       for row in results]}, indent=2))
