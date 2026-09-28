"""Verify the unloaded second FET gate KCL for imposed collector voltages."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_fet_gate_reference import conditional_second_gate_v  # noqa: E402


class FetGateTests(unittest.TestCase):
    def test_kcl_and_nominal_collector_endpoints(self) -> None:
        for q3_collector in (4.0, -4.0):
            gate = conditional_second_gate_v(q3_collector)
            kcl = (gate - 10.0) / 33200 + (gate - q3_collector) / 10700 + (gate + 10.0) / 15000
            self.assertAlmostEqual(kcl, 0.0, places=12)
        self.assertAlmostEqual(conditional_second_gate_v(4.0), 0.04, delta=0.01)
        self.assertAlmostEqual(conditional_second_gate_v(-4.0), -3.89, delta=0.01)

    def test_rejects_nonfinite_inputs(self) -> None:
        for voltage in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                conditional_second_gate_v(voltage)


if __name__ == "__main__":
    unittest.main()
