"""Verify the conditional R28/R23 output divider by KCL."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_triangle_passive_reference import passive_triangle_21b  # noqa: E402


class TrianglePassiveTests(unittest.TestCase):
    def test_coefficients_satisfy_output_kcl(self) -> None:
        result = passive_triangle_21b()
        weights = result["boundary_voltage_coefficients"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertAlmostEqual(result["passive_thevenin_resistance_ohm"], 1 / (1 / 750 + 1 / 8200))
        q1_emitter_v, saw_v = 1.5, -1.0
        triangle_v = weights["Q1_EMITTER"] * q1_emitter_v + weights["SAW_OUTPUT_9B"] * saw_v
        self.assertAlmostEqual((triangle_v - q1_emitter_v) / 750 + (triangle_v - saw_v) / 8200, 0.0)


if __name__ == "__main__":
    unittest.main()
