"""Coupled R10 supply, both multipliers and PNP conversion."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from vca_cascaded_output_dc_reference import (DEVICE_NAMES,
                                               conditional_cascaded_output_dc)


PARAMS = dict(is_a={n: 1e-14 for n in DEVICE_NAMES},
              beta_forward={n: 100 for n in DEVICE_NAMES},
              beta_reverse={n: 5 for n in DEVICE_NAMES},
              temperature_k=298.15)


class CascadedOutputDcTest(unittest.TestCase):
    def solve(self, first=2, second=2):
        return conditional_cascaded_output_dc(
            first_loudness_v=first, second_loudness_base_v=second,
            first_balance_left_ohm=12.5,
            second_balance_left_ohm=50, **PARAMS)

    def test_twenty_two_nodes_and_closed_supply(self):
        out = self.solve()
        self.assertEqual(len(out["nodes_v"]), 22)
        self.assertEqual(len(out["conductance_matrix_s"]), 22)
        self.assertLess(out["max_kcl_residual_a"], 1e-12)
        v, q = out["nodes_v"], out["devices"]
        self.assertAlmostEqual((10-v["Q1_BASE"])/120 + q["Q1"]["base_a"],
                               (v["Q1_BASE"]-v["SECOND_BAL_WIPER"])/150,
                               delta=1e-12)
        self.assertAlmostEqual((v["Q1_BASE"]-v["SECOND_BAL_WIPER"])/150,
                               (v["SECOND_BAL_WIPER"]-v["FIRST_BAL_WIPER"])/120
                               + q["Q14"]["collector_a"]
                               + q["Q13"]["collector_a"]
                               - q["Q12"]["base_a"]
                               - q["Q17"]["base_a"], delta=1e-12)
        self.assertAlmostEqual((v["SECOND_BAL_WIPER"]-v["Q14_COLLECTOR"])/380
                               + q["Q12"]["base_a"],
                               q["Q14"]["collector_a"], delta=1e-12)
        self.assertAlmostEqual((v["SECOND_BAL_WIPER"]-v["Q13_COLLECTOR"])/380
                               + q["Q17"]["base_a"],
                               q["Q13"]["collector_a"], delta=1e-12)
        self.assertTrue(0 < out["q17_collector_output_v"] < 10)

    def test_control_changes_output_conversion_bias(self):
        off = self.solve(first=0, second=0)
        on = self.solve(first=2, second=2)
        self.assertNotAlmostEqual(off["nodes_v"]["Q1_BASE"],
                                  on["nodes_v"]["Q1_BASE"], delta=0.01)
        self.assertNotAlmostEqual(off["q17_collector_output_v"],
                                  on["q17_collector_output_v"], delta=0.01)


if __name__ == "__main__":
    unittest.main()
