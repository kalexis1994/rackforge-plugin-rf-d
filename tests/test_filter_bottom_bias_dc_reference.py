"""DC base loading, R61 alternatives and passive-network consistency."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_bottom_bias_dc_reference import conditional_bottom_bias_dc
from filter_input_reference import step


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class FilterBottomBiasDCTests(unittest.TestCase):
    def scenario(self, **changes):
        defaults = dict(cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
                        beta29=100, beta30=100, r61_ohm=200,
                        r73_bottom_side_to_wiper_ohm=500,
                        ladder_bottom_injection_a=5.5e-3)
        return conditional_bottom_bias_dc(**(defaults | changes))

    def test_both_r61_candidates_close_three_base_node_kcls(self):
        for r61, injection in ((200, 5.5e-3), (200000, 5.5e-6)):
            with self.subTest(r61=r61):
                out = self.scenario(r61_ohm=r61,
                                    ladder_bottom_injection_a=injection)
                for residual in ("q29_base_kcl_residual_a", "q30_base_kcl_residual_a",
                                 "bottom_kcl_residual_a", "q29_current_coupling_residual_a",
                                 "q30_current_coupling_residual_a"):
                    self.assertAlmostEqual(out[residual], 0, delta=1e-17)
                self.assertAlmostEqual(out["split_log_residual"], 0, delta=1e-12)
                self.assertAlmostEqual(out["tail_v"], out["lower_pair"]["tail_v"])
                self.assertTrue(out["q28_forward_active_candidate"])
                self.assertLess(out["q29_base_v"], out["bottom_v"])
                self.assertLess(out["q30_base_v"], out["bottom_v"])

    def test_same_imposed_injection_exposes_r61_scale_without_selecting_it(self):
        low = self.scenario(r61_ohm=200, ladder_bottom_injection_a=5.5e-6)
        high = self.scenario(r61_ohm=200000, ladder_bottom_injection_a=5.5e-6)
        self.assertFalse(low["q28_forward_active_candidate"])
        self.assertTrue(high["q28_forward_active_candidate"])
        self.assertGreater(high["bottom_v"], low["bottom_v"])
        self.assertEqual(low["r61_ohm_selected"], 200)
        self.assertEqual(high["r61_ohm_selected"], 200000)

    def test_infinite_beta_removes_base_loading_and_r73_dc_effect(self):
        left = self.scenario(beta29=math.inf, beta30=math.inf,
                             r73_bottom_side_to_wiper_ohm=0)
        right = self.scenario(beta29=math.inf, beta30=math.inf,
                              r73_bottom_side_to_wiper_ohm=1000)
        for out in (left, right):
            self.assertEqual(out["q29_base_current_a"], 0)
            self.assertEqual(out["q30_base_current_a"], 0)
            self.assertAlmostEqual(out["bottom_v"], 200 * 5.5e-3)
            self.assertAlmostEqual(out["q29_base_v"], out["bottom_v"])
            self.assertAlmostEqual(out["q30_base_v"], out["bottom_v"])
        self.assertAlmostEqual(left["tail_v"], right["tail_v"], delta=1e-15)

    def test_loaded_r73_segment_changes_q30_base_and_current_split(self):
        near = self.scenario(r73_bottom_side_to_wiper_ohm=0, beta29=10, beta30=10)
        far = self.scenario(r73_bottom_side_to_wiper_ohm=1000, beta29=10, beta30=10)
        self.assertNotAlmostEqual(near["q30_base_v"], far["q30_base_v"],
                                  delta=1e-7)
        self.assertNotAlmostEqual(near["q29_emitter_current_fraction"],
                                  far["q29_emitter_current_fraction"], delta=1e-7)

    def test_settled_passive_input_reference_has_same_base_and_bottom(self):
        out = self.scenario()
        passive = step(dt_s=1e-3, bus_v=2, previous_bus_v=2,
                       previous_base_v=out["q29_base_v"],
                       previous_bottom_v=out["bottom_v"], r61_ohm=200,
                       q29_base_current_a=out["q29_base_current_a"],
                       ladder_bottom_current_a=(out["q30_base_current_a"]
                                                - out["ladder_bottom_injection_a_imposed"]))
        self.assertAlmostEqual(passive["base_v"], out["q29_base_v"], delta=1e-12)
        self.assertAlmostEqual(passive["bottom_v"], out["bottom_v"], delta=1e-12)
        self.assertAlmostEqual(passive["board_input_current_a"], 0, delta=1e-12)

    def test_invalid_documentary_and_current_boundaries_rejected(self):
        for change in ({"r61_ohm": 470},
                       {"r73_bottom_side_to_wiper_ohm": -1},
                       {"r73_bottom_side_to_wiper_ohm": 1001},
                       {"ladder_bottom_injection_a": math.nan},
                       {"beta30": 1}, {"is29_a": 0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.scenario(**change)


if __name__ == "__main__":
    unittest.main()
