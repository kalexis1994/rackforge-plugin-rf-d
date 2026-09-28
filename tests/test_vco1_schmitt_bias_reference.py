"""Check the conditional two-node KCL without treating it as a trip threshold."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_schmitt_bias_reference import conditional_bias_v  # noqa: E402


class SchmittBiasTests(unittest.TestCase):
    def test_two_node_kcl_with_imposed_boundaries(self) -> None:
        drive, collector, plus, minus = -1.0, -5.0, 10.0, -10.0
        sense, bias = conditional_bias_v(drive, collector, plus, minus)
        sense_kcl = (sense - plus) / 33200 + (sense - drive) / 10700 + (sense - bias) / 10000
        bias_kcl = (bias - sense) / 10000 + (bias - collector) / 56 + (bias - minus) / 1000
        self.assertAlmostEqual(sense_kcl, 0.0, places=12)
        self.assertAlmostEqual(bias_kcl, 0.0, places=12)
        self.assertLess(sense, 0.0)
        self.assertLess(bias, 0.0)

    def test_q6_collector_couples_into_q5_sense(self) -> None:
        first_sense, _ = conditional_bias_v(-1.0, -5.0)
        next_sense, _ = conditional_bias_v(-1.0, -4.0)
        self.assertGreater(next_sense - first_sense, 0.4)
        self.assertLess(next_sense - first_sense, 0.45)

    def test_rejects_nonfinite_boundaries(self) -> None:
        for voltage in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                conditional_bias_v(voltage, -5.0)


if __name__ == "__main__":
    unittest.main()
