"""Verify R13 supply boundary and its interaction with first VCA bias."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from vca1_active_core_dc_reference import DEVICES, conditional_vca1_dc
from vca1_balance_supply_dc_reference import conditional_vca1_supplied_dc


PARAMS = dict(is_a={n: 1e-14 for n in DEVICES},
              beta_forward={n: 100 for n in DEVICES},
              beta_reverse={n: 5 for n in DEVICES}, temperature_k=298.15)


class Vca1BalanceSupplyDcTest(unittest.TestCase):
    def solve(self, second=9, loudness=2, trim=12.5):
        return conditional_vca1_supplied_dc(
            second_wiper_v=second, loudness_v=loudness,
            balance_left_ohm=trim, **PARAMS)

    def test_supply_and_bias_currents_close(self):
        for control in (0, 0.5, 2, 3):
            with self.subTest(control=control):
                out = self.solve(loudness=control)
                self.assertLess(out["max_kcl_residual_a"], 1e-12)
                node = out["nodes_v"]
                supply = (9 - node["FIRST_BAL_WIPER"]) / 120
                bias = (node["FIRST_BAL_WIPER"] - node["Q15_BASE"]) / 120
                q16 = out["devices"]["Q16"]["collector_a"]
                q15 = out["devices"]["Q15"]["collector_a"]
                self.assertAlmostEqual(supply, bias + q16 + q15, delta=1e-12)
                self.assertGreater(node["FIRST_BAL_WIPER"], 0)
                self.assertLess(node["FIRST_BAL_WIPER"], 9)

    def test_reduces_to_eight_node_core_at_solved_cursor(self):
        supplied = self.solve()
        fixed = conditional_vca1_dc(
            wiper_v=supplied["nodes_v"]["FIRST_BAL_WIPER"],
            loudness_v=2, balance_left_ohm=12.5, **PARAMS)
        for name, voltage in fixed["nodes_v"].items():
            self.assertAlmostEqual(voltage, supplied["nodes_v"][name],
                                   delta=1e-8)

    def test_second_boundary_and_balance_alter_solution(self):
        low, high = self.solve(second=8), self.solve(second=10)
        self.assertLess(low["nodes_v"]["FIRST_BAL_WIPER"],
                        high["nodes_v"]["FIRST_BAL_WIPER"])
        left, right = self.solve(trim=0), self.solve(trim=25)
        self.assertNotAlmostEqual(left["nodes_v"]["Q16_COLLECTOR"],
                                  right["nodes_v"]["Q16_COLLECTOR"],
                                  delta=1e-4)

    def test_invalid_source_rejected(self):
        with self.assertRaises(ValueError):
            self.solve(second=float("nan"))


if __name__ == "__main__":
    unittest.main()
