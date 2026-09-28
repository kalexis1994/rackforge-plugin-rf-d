"""Coupled supply and base-current conservation across both VCA cores."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from vca_cascaded_dc_reference import DEVICE_NAMES, conditional_cascaded_vca_dc


PARAMS = dict(is_a={n: 1e-14 for n in DEVICE_NAMES},
              beta_forward={n: 100 for n in DEVICE_NAMES},
              beta_reverse={n: 5 for n in DEVICE_NAMES},
              temperature_k=298.15)


class CascadedVcaDcTest(unittest.TestCase):
    def solve(self, first=2, second=2, supply=9.5):
        return conditional_cascaded_vca_dc(
            upper_supply_v=supply,
            first_loudness_v=first, second_loudness_base_v=second,
            first_balance_left_ohm=12.5, second_balance_left_ohm=50,
            **PARAMS)

    def test_fifteen_kcl_rows_and_both_tail_currents(self):
        for first, second in ((0, 0), (0, 2), (1, 1), (2, 2), (3, 3)):
            with self.subTest(first=first, second=second):
                out = self.solve(first, second)
                self.assertEqual(len(out["nodes_v"]), 15)
                self.assertLess(out["max_kcl_residual_a"], 1e-12)
                q = out["devices"]
                self.assertAlmostEqual(q["Q16"]["emitter_a"] + q["Q15"]["emitter_a"],
                                       q["Q18"]["collector_a"], delta=1e-12)
                self.assertAlmostEqual(q["Q14"]["emitter_a"] + q["Q13"]["emitter_a"],
                                       q["Q21"]["collector_a"], delta=1e-12)
                self.assertEqual(out["first_to_second_base_currents_a"],
                                 (q["Q14"]["base_a"], q["Q13"]["base_a"]))

    def test_collector_loads_and_shared_supply_close(self):
        out = self.solve()
        v = out["nodes_v"]
        q = out["devices"]
        w1, w2 = v["FIRST_BAL_WIPER"], v["SECOND_BAL_WIPER"]
        self.assertAlmostEqual((w1 - v["Q16_COLLECTOR"]) / 112.5,
                               q["Q16"]["collector_a"] + q["Q14"]["base_a"],
                               delta=1e-12)
        self.assertAlmostEqual((w1 - v["Q15_COLLECTOR"]) / 112.5,
                               q["Q15"]["collector_a"] + q["Q13"]["base_a"],
                               delta=1e-12)
        self.assertAlmostEqual((9.5 - w2) / 150,
                               (w2 - w1) / 120
                               + q["Q14"]["collector_a"]
                               + q["Q13"]["collector_a"],
                               delta=1e-12)
        self.assertGreater(w2, w1)
        self.assertLess(w2, 9.5)

    def test_controls_shift_both_supply_nodes(self):
        off = self.solve(first=0, second=0)
        on = self.solve(first=2, second=2)
        self.assertGreater(off["nodes_v"]["FIRST_BAL_WIPER"],
                           on["nodes_v"]["FIRST_BAL_WIPER"])
        self.assertGreater(off["nodes_v"]["SECOND_BAL_WIPER"],
                           on["nodes_v"]["SECOND_BAL_WIPER"])
        self.assertGreater(on["devices"]["Q21"]["collector_a"],
                           off["devices"]["Q21"]["collector_a"])

    def test_incomplete_parameters_rejected(self):
        with self.assertRaises(ValueError):
            conditional_cascaded_vca_dc(
                upper_supply_v=9.5, first_loudness_v=2,
                second_loudness_base_v=2,
                first_balance_left_ohm=12.5,
                second_balance_left_ohm=50,
                is_a={"Q16": 1e-14},
                beta_forward=PARAMS["beta_forward"],
                beta_reverse=PARAMS["beta_reverse"],
                temperature_k=298.15)


if __name__ == "__main__":
    unittest.main()
