"""Numerical domain regression for the declared 256-step stress grid."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_transient_stress_reference import stress_grid


class HeadphoneTransientStressTest(unittest.TestCase):
    def test_all_declared_scenarios_converge_and_isolate_sw18(self):
        report = stress_grid()
        self.assertEqual(report["scenario_count"], 16)
        self.assertEqual(report["step_count"], 256)
        self.assertLess(report["max_kcl_residual_a"], 1e-10)
        self.assertLessEqual(report["max_newton_iterations"], 8)
        self.assertTrue(all(row["steps"] == 16 for row in report["rows"]))
        self.assertTrue(all(row["mean_step_s"] > 0 for row in report["rows"]))
        by_key = {(r["bus_peak_v"], r["dt_s"], r["sw18_on"],
                   r["tip_ring_ohm"]): r for r in report["rows"]}
        for peak in (0.1, 1.0):
            for dt in (1/48000, 1/96000):
                for switch in (False, True):
                    open_j7 = by_key[(peak, dt, switch, None)]
                    loaded_j7 = by_key[(peak, dt, switch, 32)]
                    self.assertGreater(open_j7["max_abs_j7_v"],
                                       loaded_j7["max_abs_j7_v"])


if __name__ == "__main__":
    unittest.main()
