"""Conditional 62-node sensitivity remains solved and preserves KCL."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_transient_semiconductor_grid import semiconductor_grid


class HeadphoneTransientSemiconductorGridTest(unittest.TestCase):
    def test_board3_and_temperature_scenarios(self):
        result = semiconductor_grid()
        self.assertEqual(result["scenario_count"], 11)
        self.assertEqual(result["total_steps"], 1056)
        self.assertLess(result["max_kcl_residual_a"], 1.1e-10)
        self.assertLessEqual(result["max_newton_iterations"], 8)
        self.assertGreater(result["board3_grid_j7_rms_max_v"],
                           result["board3_grid_j7_rms_min_v"])
        self.assertGreater(result["temperature_grid_j7_rms_max_v"],
                           result["temperature_grid_j7_rms_min_v"])
        for row in result["rows"]:
            self.assertEqual(row["steps"], 96)
            self.assertGreater(row["j7_rms_v"], 0)
            self.assertLess(row["max_kcl_residual_a"], 1.1e-10)
        for beta in (80, 160, 300):
            rms = [next(row["j7_rms_v"] for row in result["rows"] if
                        row["temperature_k"] == 298.15 and
                        row["board3_beta_forward"] == beta and
                        row["diode_forward_voltage_at_100ma_v"] == forward)
                   for forward in (0.65, 0.7, 0.75)]
            self.assertLess(rms[0], rms[1])
            self.assertLess(rms[1], rms[2])


if __name__ == "__main__":
    unittest.main()
