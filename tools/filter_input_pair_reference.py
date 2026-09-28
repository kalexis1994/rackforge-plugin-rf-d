"""Conditional ideal Q29/Q30 TIS97 current split, SVC-9 Fig. 9-11.

The bases, tail emitter current and junction temperature are imposed. This
computes no Q28 operating point, ladder rail voltage, Q30 feedback loading,
or circuit resonance. The ideal BJT exponential is TI SLOA059B eq. 3.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from semiconductor_ideal import thermal_voltage_v


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_input_pair.json"


def _check_topology() -> None:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    nodes = data["connections"]
    if (data["schematic"]["figure"], data["parts_list"]["table"],
            data["population"]["Q29_Q30"],
            nodes["Q29"]["base"], nodes["Q30"]["base"],
            nodes["Q29"]["emitter"], nodes["Q30"]["emitter"],
            nodes["R60"]["ohm"], nodes["R60"]["between"],
            nodes["Q28"]["collector"], nodes["Q28"]["base"]) != (
                "9-11", "7-8", "TIS97 matched pair", "BASE after C27",
                "REGEN_BASE at R73 wiper", "TAIL", "TAIL", 680,
                ["TAIL", "Q28_COLLECTOR"], "Q28_COLLECTOR", "SHARED_Q26_EMITTER"):
        raise ValueError("Q29/Q30 tail topology differs from documentary source")


def ideal_current_split(*, q29_base_v: float, q30_base_v: float,
                        tail_current_a: float, temperature_k: float) -> dict:
    """Split a fixed emitter tail current between matched forward-active BJTs.

    Infinite-beta approximation makes collector currents sum to tail_current.
    Neither Q28 current nor device headroom is solved here.
    """
    _check_topology()
    if (not math.isfinite(q29_base_v) or not math.isfinite(q30_base_v)
            or not math.isfinite(tail_current_a) or tail_current_a <= 0):
        raise ValueError("finite base voltages and positive tail current required")
    vt = thermal_voltage_v(temperature_k)
    difference_v = q29_base_v - q30_base_v
    fraction_difference = math.tanh(difference_v / (2 * vt))
    q29_current_a = 0.5 * tail_current_a * (1 + fraction_difference)
    q30_current_a = tail_current_a - q29_current_a
    return {
        "q29_collector_current_a": q29_current_a,
        "q30_collector_current_a": q30_current_a,
        "left_minus_right_current_a": tail_current_a * fraction_difference,
        "differential_transconductance_s": tail_current_a / (2 * vt)
                                           * (1 - fraction_difference * fraction_difference),
        "thermal_voltage_v": vt,
        "base_difference_v": difference_v,
        "tail_current_a_imposed": tail_current_a,
        "actual_tail_current_known": False,
    }


if __name__ == "__main__":
    for difference_mv in (-100, -25, 0, 25, 100):
        out = ideal_current_split(q29_base_v=difference_mv / 1000,
                                  q30_base_v=0, tail_current_a=1e-3,
                                  temperature_k=298.15)
        print(f"base difference {difference_mv:+4d} mV: "
              f"Q29={out['q29_collector_current_a'] * 1000:.4f} mA, "
              f"Q30={out['q30_collector_current_a'] * 1000:.4f} mA")
