"""Bipolar, sustained and SW18 switching stress for the 62-node oracle."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_transient_bipolar_reference import bipolar_stress


class HeadphoneTransientBipolarTest(unittest.TestCase):
    def test_four_longer_scenarios_converge_and_reverse_j7_polarity(self):
        result = bipolar_stress()
        self.assertEqual(result["scenario_count"], 4)
        self.assertEqual(result["step_count"], 768)
        rows = {(row["dt_s"], row["tip_ring_ohm"]): row
                for row in result["rows"]}
        self.assertEqual(len(rows), 4)
        for dt in (1/48000, 1/4800):
            open_load = rows[(dt, None)]
            loaded = rows[(dt, 32)]
            for row in (open_load, loaded):
                self.assertEqual(row["steps"], 192)
                self.assertLess(row["max_kcl_residual_a"], 1e-10)
                self.assertLessEqual(row["max_newton_iterations"], 20)
                self.assertEqual(row["max_off_hi_lo_v"], 0)
                self.assertLess(row["min_j7_v"], 0)
                self.assertGreater(row["max_j7_v"], 0)
            self.assertGreater(open_load["max_j7_v"], loaded["max_j7_v"])
            self.assertGreater(abs(open_load["min_j7_v"]),
                               abs(loaded["min_j7_v"]))
        self.assertGreater(abs(rows[(1/4800, 32)]["min_j7_v"]), 0.01)


if __name__ == "__main__":
    unittest.main()
