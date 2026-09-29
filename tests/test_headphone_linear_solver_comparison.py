"""Optional dense algebra backend agrees with the portable reference."""

import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_dense_linear_reference import solve_headphone_linear
from headphone_linear_solver_comparison import compare_linear_solvers


class HeadphoneLinearSolverComparisonTest(unittest.TestCase):
    def test_method_and_singularity_domain(self):
        with self.assertRaises(ValueError):
            solve_headphone_linear([[1.0]], [1.0], method="other")
        if importlib.util.find_spec("numpy") is not None:
            with self.assertRaises(ValueError):
                solve_headphone_linear([[0.0]], [1.0], method="numpy")

    @unittest.skipUnless(importlib.util.find_spec("numpy") is not None,
                         "optional NumPy backend unavailable")
    def test_four_traces_match_portable_solver(self):
        result = compare_linear_solvers()
        self.assertEqual(result["scenario_count"], 4)
        self.assertEqual(result["step_count_per_solver"], 96)
        self.assertLess(result["max_node_difference_v"], 1e-9)
        self.assertLess(result["max_j7_difference_v"], 1e-9)
        self.assertLess(result["max_kcl_residual_a"], 1e-10)


if __name__ == "__main__":
    unittest.main()
