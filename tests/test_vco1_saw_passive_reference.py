"""Check the 9B passive conductance inventory and its cross-wave coupling."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_saw_passive_reference import passive_saw_9b  # noqa: E402


class SawPassiveTests(unittest.TestCase):
    def test_weights_are_kcl_conductance_fractions(self) -> None:
        result = passive_saw_9b()
        weights = result["boundary_voltage_coefficients"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertEqual(set(weights), {
            "SCHMITT_DRIVE", "GND", "TRI_OUTPUT_21B", "Q2_COLLECTOR", "Q11_BASE", "Q12_BASE"
        })
        self.assertAlmostEqual(
            result["passive_thevenin_resistance_ohm"],
            1 / sum(1 / r for r in (4300, 4700, 8200, 150000, 390000, 100000)),
        )

    def test_triangle_branch_prevents_isolated_divider_assumption(self) -> None:
        weights = passive_saw_9b()["boundary_voltage_coefficients"]
        self.assertGreater(weights["TRI_OUTPUT_21B"], 0.20)
        self.assertLess(weights["SCHMITT_DRIVE"], 4700 / (4300 + 4700))


if __name__ == "__main__":
    unittest.main()
