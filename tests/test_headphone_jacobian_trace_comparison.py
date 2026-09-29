"""Both 62-node Newton paths follow the same bipolar switch/load sequence."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_jacobian_trace_comparison import compare_traces


class HeadphoneJacobianTraceComparisonTest(unittest.TestCase):
    def test_four_matched_traces_remain_numerically_equivalent(self):
        result = compare_traces()
        self.assertEqual(result["scenario_count"], 4)
        self.assertEqual(result["step_count_per_method"], 96)
        self.assertLess(result["max_node_difference_v"], 1e-6)
        self.assertLess(result["max_j7_difference_v"], 1e-8)
        self.assertLess(result["max_kcl_residual_a"], 1e-10)
        for row in result["rows"]:
            self.assertEqual(row["steps"], 24)
            self.assertLessEqual(row["max_newton_iterations"]["hybrid"], 20)
            self.assertLessEqual(row["max_newton_iterations"]["finite_difference"], 20)


if __name__ == "__main__":
    unittest.main()
