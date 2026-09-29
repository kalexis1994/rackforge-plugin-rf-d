"""The same physical BUS sine converges under implicit-Euler refinement."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_transient_dt_convergence_reference import convergence_grid


class HeadphoneTransientConvergenceTest(unittest.TestCase):
    def test_two_cycle_step_refinement_reduces_aligned_errors(self):
        result = convergence_grid()
        self.assertEqual(result["sample_counts"],
                         {"4800": 96, "9600": 192, "19200": 384})
        self.assertEqual(result["total_steps"], 672)
        self.assertLess(result["max_kcl_residual_a"], 2e-10)
        self.assertLessEqual(result["max_newton_iterations"], 8)
        for name in ("j7_v", "r21_wiper_v", "c2_right_v"):
            coarse = result["coarse_to_medium"][name]
            fine = result["medium_to_fine"][name]
            self.assertGreater(coarse["max_abs_error_v"],
                               fine["max_abs_error_v"])
            self.assertGreater(coarse["rms_error_v"],
                               fine["rms_error_v"])
            self.assertGreater(result["max_error_ratios"][name], 1.5)
            self.assertLess(result["max_error_ratios"][name], 2.2)


if __name__ == "__main__":
    unittest.main()
