"""Circuit boundaries, KCL and C18 dynamics for the Q26 base path."""

import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from filter_cutoff_base_reference import conditional_q26_base
from filter_cutoff_pair_reference import conditional_cutoff_current


class Q26BaseReferenceTests(unittest.TestCase):
    def scenario(self, **changes):
        values = dict(cutoff_fraction_from_neg10=0.5, scale_active_ohm=250,
                      contour_pin16_v=0)
        return conditional_q26_base(**(values | changes))

    def test_cross_document_pin_and_trimmer_topology(self):
        base = json.loads((ROOT / "evidence/filter_cutoff_base_network.json").read_text())
        pair = json.loads((ROOT / "evidence/filter_cutoff_q26_q28.json").read_text())
        self.assertEqual(base["parts"]["R74"]["between"],
                         ["BOARD4_PIN16_AMT_OF_CONTOUR", "CONTROL_BASE"])
        self.assertEqual(pair["parts"]["R74"]["between"], base["parts"]["R74"]["between"])
        self.assertEqual(base["parts"]["R49"]["wiper"], "CONTROL_BASE")
        self.assertEqual(base["parts"]["Q26"]["node"], pair["parts"]["Q26"]["base"])
        self.assertIn("BOARD4_PIN5_CONTROL_NODE", base["direct_connection"])

    def test_loaded_wiper_dc_kcl_and_control_direction(self):
        mid = self.scenario()
        self.assertEqual(mid["cutoff_wiper_thevenin_v"], 0)
        self.assertAlmostEqual(mid["cutoff_wiper_thevenin_ohm"], 1250)
        self.assertAlmostEqual(mid["cutoff_path_total_ohm"], 201250)
        self.assertAlmostEqual(mid["scale_to_ground_ohm"], 2050)
        self.assertAlmostEqual(mid["resistive_kcl_residual_a"], 0, delta=1e-18)
        self.assertLess(self.scenario(cutoff_fraction_from_neg10=0)["q26_base_v"],
                        mid["q26_base_v"])
        self.assertGreater(self.scenario(cutoff_fraction_from_neg10=1)["q26_base_v"],
                           mid["q26_base_v"])

    def test_imposed_panel_branch_and_base_current_have_expected_signs(self):
        base = self.scenario()
        driven = self.scenario(other_branches=((1, 100000),))
        sink = self.scenario(q26_base_current_a=1e-6)
        self.assertGreater(driven["q26_base_v"], base["q26_base_v"])
        self.assertLess(sink["q26_base_v"], base["q26_base_v"])
        self.assertAlmostEqual(driven["resistive_kcl_residual_a"], 0, delta=1e-18)
        self.assertAlmostEqual(sink["resistive_kcl_residual_a"], 0, delta=1e-18)

    def test_c18_exact_held_input_step(self):
        dc = self.scenario(contour_pin16_v=1)
        tau = dc["c18_time_constant_s"]
        initial = self.scenario(contour_pin16_v=1, previous_base_v=0, step_s=0)
        one_tau = self.scenario(contour_pin16_v=1, previous_base_v=0, step_s=tau)
        self.assertEqual(initial["q26_base_v"], 0)
        self.assertAlmostEqual(one_tau["q26_base_v"],
                               dc["q26_base_v"] * (1 - math.exp(-1)))
        self.assertAlmostEqual(one_tau["resistive_kcl_residual_a"]
                               + one_tau["c18_current_a"], 0, delta=1e-18)

    def test_base_voltage_can_feed_conditional_pair_without_claiming_calibration(self):
        base = self.scenario()
        pair = conditional_cutoff_current(range_fraction_from_ground=0.1,
                                          q26_base_v=base["q26_base_v"],
                                          is26_a=1e-14, is28_a=1e-14,
                                          temperature_k=298.15, tail_v=2)
        self.assertTrue(pair["q26_forward_active_candidate"])
        self.assertAlmostEqual(pair["q28_collector_current_a_candidate_a"]
                               / pair["q26_collector_current_a"],
                               math.exp(base["q26_base_v"] / (1.380649e-23 * 298.15
                                                                  / 1.602176634e-19)),
                               delta=1e-10)

    def test_invalid_boundaries_rejected(self):
        for change in ({"cutoff_fraction_from_neg10": -0.01},
                       {"scale_active_ohm": 501},
                       {"contour_pin16_v": math.nan},
                       {"other_branches": ((1, 0),)},
                       {"previous_base_v": 0},
                       {"previous_base_v": 0, "step_s": -1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.scenario(**change)


if __name__ == "__main__":
    unittest.main()
