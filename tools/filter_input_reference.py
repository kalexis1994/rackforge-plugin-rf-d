"""Conditional C27/R54/C24/R61 board-4 input, SVC-9 Fig. 9-11.

BUS voltage and active currents are imposed boundaries. R61 has conflicting
schematic/BOM values, so its candidate must be selected explicitly. This is a
charge-conserving passive reference, not a filter or sound-fidelity model.
"""

from __future__ import annotations

import json
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_input_board4.json"


def _parts() -> dict:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parts = data["parts"]
    if (data["schematic"]["figure"], data["parts_list"]["table"]) != ("9-11", "7-8"):
        raise ValueError("board-4 documentary sources changed")
    if (parts["C27"]["farad"], parts["R54"]["ohm"], parts["C24"]["farad"],
            parts["R61"]["candidate_ohm"]) != (10e-6, 470, 220e-6, [200, 200000]):
        raise ValueError("board-4 input values changed; recheck source pages")
    return parts


def step(*, dt_s: float, bus_v: float, previous_bus_v: float,
         previous_base_v: float, previous_bottom_v: float, r61_ohm: int,
         q29_base_current_a: float = 0.0, ladder_bottom_current_a: float = 0.0) -> dict:
    """Backward-Euler KCL; positive boundary currents leave BASE/BOTTOM.

    All voltages are relative to ground. Initial capacitor voltages are set by
    the previous BUS/BASE/BOTTOM values. A discontinuity in BUS is allowed.
    """
    parts = _parts()
    if dt_s <= 0 or r61_ohm not in parts["R61"]["candidate_ohm"]:
        raise ValueError("positive dt_s and an explicit R61 documentary candidate required")
    c27, c24, r54 = (parts["C27"]["farad"], parts["C24"]["farad"],
                      parts["R54"]["ohm"])
    g27, g24, g54, g61 = c27 / dt_s, c24 / dt_s, 1 / r54, 1 / r61_ohm
    # C27 current from BASE to BUS is C27 * d(BASE - BUS)/dt.
    a, b, d = g27 + g54, -g54, g24 + g54 + g61
    rhs_base = g27 * (bus_v + previous_base_v - previous_bus_v) - q29_base_current_a
    rhs_bottom = g24 * previous_bottom_v - ladder_bottom_current_a
    determinant = a * d - b * b
    base_v = (rhs_base * d - b * rhs_bottom) / determinant
    bottom_v = (a * rhs_bottom - b * rhs_base) / determinant
    c27_from_base_a = c27 * ((base_v - bus_v) - (previous_base_v - previous_bus_v)) / dt_s
    r54_from_base_a = (base_v - bottom_v) / r54
    c24_to_ground_a = c24 * (bottom_v - previous_bottom_v) / dt_s
    r61_to_ground_a = bottom_v / r61_ohm
    return {
        "base_v": base_v, "bottom_v": bottom_v,
        "board_input_current_a": -c27_from_base_a,
        "base_kcl_residual_a": c27_from_base_a + r54_from_base_a + q29_base_current_a,
        "bottom_kcl_residual_a": c24_to_ground_a + r61_to_ground_a
                                  - r54_from_base_a + ladder_bottom_current_a,
        "r61_ohm": r61_ohm,
    }


if __name__ == "__main__":
    print(json.dumps(step(dt_s=1e-4, bus_v=1, previous_bus_v=0,
                          previous_base_v=0, previous_bottom_v=0,
                          r61_ohm=200000), indent=2))
