"""Three-node passive R2/C6/R34/C15/R36 entrance of the first VCA.

The recovery collector signal is an ideal 1 V small-signal boundary.
Q16/Q15 base currents and the VCA balance bias path are set to zero/open.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _solve_linear


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "vca1_input_boundary.json"


def _values() -> tuple[float, float, float, float, float]:
    source = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parts = {row["ref"]: row for row in source["passive_components"]}
    actual = {ref: (row.get("farad", row.get("ohm")), tuple(row["between"]))
              for ref, row in parts.items()}
    expected = {
        "R2": (82000, ("RECOVER_COLLECTOR", "C6_LEFT")),
        "C6": (0.33e-6, ("C6_LEFT", "Q16_BASE")),
        "R34": (820, ("Q16_BASE", "Q15_BASE")),
        "C15": (220e-6, ("Q15_BASE", "GROUND")),
        "R36": (510, ("Q15_BASE", "GROUND")),
    }
    if (source["schematic"]["figure"], source["parts_list"]["table"],
            source["functional_description"]["section"], actual) != (
                "9-11", "7-8", "2.9", expected):
        raise ValueError("VCA input values/topology differ from documentary source")
    return 82000, 0.33e-6, 820, 220e-6, 510


def passive_vca1_input(*, frequency_hz: float) -> dict:
    """Phasor solution for ideal 1 V recovery collector, volts per volt."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    r2, c6, r34, c15, r36 = _values()
    s = 2j * math.pi * frequency_hz
    y2, y6, y34, y15, y36 = 1 / r2, s * c6, 1 / r34, s * c15, 1 / r36
    matrix = [[-(y2 + y6), y6, 0j],
              [y6, -(y6 + y34), y34],
              [0j, y34, -(y34 + y15 + y36)]]
    rhs = [-y2, 0j, 0j]
    c6_left, q16_base, q15_base = _solve_linear(matrix, rhs)
    voltage = (c6_left, q16_base, q15_base)
    residual = max(abs(sum(matrix[i][j] * voltage[j]
                           for j in range(3)) - rhs[i]) for i in range(3))
    return {
        "frequency_hz": frequency_hz,
        "c6_left_v_per_recovery_v": c6_left,
        "q16_base_v_per_recovery_v": q16_base,
        "q15_base_v_per_recovery_v": q15_base,
        "differential_base_v_per_recovery_v": q16_base - q15_base,
        "source_admittance_s": y2 * (1 - c6_left),
        "max_linear_kcl_residual_a_per_v": residual,
        "source_imposed_ideal": True,
        "base_currents_imposed_zero": True,
        "balance_network_imposed_open": True,
    }


if __name__ == "__main__":
    for frequency in (0, 30, 100, 300, 1000, 10000):
        row = passive_vca1_input(frequency_hz=frequency)
        print(json.dumps({"frequency_hz": frequency,
                          "q16_base_magnitude": abs(row["q16_base_v_per_recovery_v"]),
                          "differential_base_magnitude": abs(row[
                              "differential_base_v_per_recovery_v"]),
                          "kcl_residual": row["max_linear_kcl_residual_a_per_v"]}))
