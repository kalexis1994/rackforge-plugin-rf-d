"""Finite-beta base loading and two-node KCL for conditional Q26/Q28 DC."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_cutoff_coupled_dc_reference import conditional_coupled_cutoff_dc
from filter_cutoff_pair_reference import conditional_cutoff_current
from filter_cutoff_panel_reference import conditional_panel_q26_base
from semiconductor_ideal import thermal_voltage_v


PANEL = dict(cutoff_fraction_from_neg10=0.5, scale_active_ohm=250,
             contour_pin16_v=0)


class FilterCutoffCoupledDCReferenceTests(unittest.TestCase):
    def scenario(self, **changes):
        defaults = dict(panel_inputs=PANEL, range_fraction_from_ground=0.1,
                        is26_a=1e-14, is28_a=1e-14, beta26=100, beta28=100,
                        temperature_k=298.15, tail_v=2)
        return conditional_coupled_cutoff_dc(**(defaults | changes))

    def test_finite_beta_kcl_base_sign_and_bjt_law(self):
        out = self.scenario()
        self.assertLess(out["q26_base_current_signed_from_node_a"], 0)
        self.assertGreater(out["q28_base_current_a"], 0)
        self.assertGreater(out["q26_base_v"], out["q26_base_unloaded_v"])
        self.assertAlmostEqual(out["q26_emitter_current_a"],
                               out["q26_collector_current_a"]
                               - out["q26_base_current_signed_from_node_a"], delta=1e-18)
        self.assertAlmostEqual(out["range_source_current_a"],
                               out["q26_emitter_current_a"]
                               + out["q28_base_current_a"], delta=1e-18)
        self.assertAlmostEqual(out["shared_kcl_residual_a"], 0, delta=1e-18)
        self.assertAlmostEqual(out["base_kcl_residual_a"], 0, delta=1e-18)
        self.assertAlmostEqual(out["base_coupling_residual_v"], 0, delta=1e-15)
        self.assertAlmostEqual(out["q26_exponential_residual_v"], 0, delta=1e-15)
        self.assertTrue(out["q26_forward_active_candidate"])
        self.assertTrue(out["q28_forward_active_candidate"])

    def test_infinite_beta_recovers_existing_conditional_pair(self):
        ideal = self.scenario(beta26=math.inf, beta28=math.inf)
        panel = conditional_panel_q26_base(**PANEL)
        pair = conditional_cutoff_current(range_fraction_from_ground=0.1,
                                          q26_base_v=panel["q26_base_v"],
                                          is26_a=1e-14, is28_a=1e-14,
                                          temperature_k=298.15, tail_v=2)
        self.assertEqual(ideal["q26_base_current_signed_from_node_a"], 0)
        self.assertEqual(ideal["q28_base_current_a"], 0)
        self.assertAlmostEqual(ideal["q26_base_v"], panel["q26_base_v"])
        self.assertAlmostEqual(ideal["shared_node_v"], pair["shared_node_v"], delta=1e-13)
        self.assertAlmostEqual(ideal["q26_collector_current_a"],
                               pair["q26_collector_current_a"], delta=1e-16)
        self.assertAlmostEqual(ideal["q28_collector_current_a_candidate"],
                               pair["q28_collector_current_a_candidate_a"], delta=1e-16)

    def test_collector_ratio_still_cancels_shared_node_at_finite_beta(self):
        out = self.scenario(panel_inputs=PANEL | {"cutoff_fraction_from_neg10": 0.7},
                            beta26=40, beta28=70)
        observed = out["q28_collector_current_a_candidate"] / out["q26_collector_current_a"]
        expected = math.exp(out["q26_base_v"] / thermal_voltage_v(298.15))
        self.assertAlmostEqual(observed, expected, delta=1e-10)

    def test_panel_sources_and_tail_headroom_are_explicit(self):
        off = self.scenario()
        keyboard = self.scenario(panel_inputs=PANEL | dict(keyboard_1_3_on=True,
                                                        keyboard_cv_v=2))
        self.assertGreater(keyboard["q26_base_v"], off["q26_base_v"])
        low_tail = self.scenario(tail_v=0.1)
        self.assertFalse(low_tail["q28_forward_active_candidate"])
        self.assertAlmostEqual(low_tail["q28_collector_current_a_candidate"],
                               off["q28_collector_current_a_candidate"])

    def test_electrical_range_and_cutoff_edges_remain_balanced(self):
        for range_fraction in (0, 1):
            for cutoff_fraction in (0, 1):
                with self.subTest(range_fraction=range_fraction,
                                  cutoff_fraction=cutoff_fraction):
                    out = self.scenario(
                        range_fraction_from_ground=range_fraction,
                        panel_inputs=PANEL | {"cutoff_fraction_from_neg10": cutoff_fraction},
                        beta26=20, beta28=20)
                    self.assertGreater(out["q26_collector_current_a"], 0)
                    self.assertAlmostEqual(out["shared_kcl_residual_a"], 0, delta=1e-17)
                    self.assertAlmostEqual(out["base_kcl_residual_a"], 0, delta=1e-17)

    def test_invalid_parameters_and_owned_base_current_rejected(self):
        for changes in ({"beta26": 1}, {"beta28": -5},
                        {"beta26": math.nan}, {"is26_a": 0},
                        {"temperature_k": 0},
                        {"panel_inputs": PANEL | {"q26_base_current_a": 0}},
                        {"panel_inputs": PANEL | {"step_s": 1e-6}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.scenario(**changes)


if __name__ == "__main__":
    unittest.main()
