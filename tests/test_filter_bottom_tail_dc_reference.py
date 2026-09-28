"""TAIL KCL, current split and Q28 headroom for conditional lower pair."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_bottom_tail_dc_reference import conditional_bottom_tail_dc
from filter_cutoff_coupled_dc_reference import conditional_coupled_cutoff_dc
from filter_input_pair_reference import ideal_current_split
from semiconductor_ideal import thermal_voltage_v


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class FilterBottomTailDCTests(unittest.TestCase):
    def scenario(self, **changes):
        defaults = dict(cutoff_inputs=CUTOFF, q29_base_v=1.1, q30_base_v=1.1,
                        is29_a=1e-14, is30_a=1e-14, beta29=100, beta30=100)
        return conditional_bottom_tail_dc(**(defaults | changes))

    def test_tail_and_r60_kcl_with_finite_beta(self):
        out = self.scenario()
        self.assertAlmostEqual(out["q29_emitter_current_a"]
                               + out["q30_emitter_current_a"],
                               out["cutoff"]["q28_collector_current_a_candidate"], delta=1e-18)
        self.assertAlmostEqual(out["tail_kcl_residual_a"], 0, delta=1e-18)
        self.assertAlmostEqual(out["r60_voltage_residual_v"], 0, delta=1e-15)
        self.assertAlmostEqual(out["q29_emitter_current_a"],
                               out["q29_collector_current_a_candidate"]
                               + out["q29_base_current_a"], delta=1e-18)
        self.assertAlmostEqual(out["q30_emitter_current_a"],
                               out["q30_collector_current_a_candidate"]
                               + out["q30_base_current_a"], delta=1e-18)
        self.assertTrue(out["q28_forward_active_candidate"])
        self.assertTrue(out["q29_be_forward_biased_candidate"])
        self.assertFalse(out["q29_q30_collector_headroom_known"])

    def test_equal_pair_splits_emitter_current_and_swap_exchanges_collectors(self):
        equal = self.scenario()
        self.assertAlmostEqual(equal["q29_emitter_current_a"],
                               equal["q30_emitter_current_a"], delta=1e-18)
        left = self.scenario(q29_base_v=1.125, q30_base_v=1.1)
        right = self.scenario(q29_base_v=1.1, q30_base_v=1.125)
        self.assertAlmostEqual(left["q29_collector_current_a_candidate"],
                               right["q30_collector_current_a_candidate"], delta=1e-18)
        self.assertAlmostEqual(left["tail_v"], right["tail_v"], delta=1e-15)

    def test_mismatched_saturation_currents_follow_both_exponential_laws(self):
        out = self.scenario(is29_a=2e-14, is30_a=1e-14,
                            q29_base_v=1.125, q30_base_v=1.1)
        vt = thermal_voltage_v(298.15)
        self.assertAlmostEqual(out["q29_collector_current_a_candidate"],
                               2e-14 * math.exp((1.125 - out["tail_v"]) / vt),
                               delta=1e-18)
        self.assertAlmostEqual(out["q30_collector_current_a_candidate"],
                               1e-14 * math.exp((1.1 - out["tail_v"]) / vt),
                               delta=1e-18)

    def test_infinite_beta_recovers_fixed_tail_ideal_split(self):
        out = self.scenario(beta29=math.inf, beta30=math.inf,
                            q29_base_v=1.125)
        old = ideal_current_split(q29_base_v=1.125, q30_base_v=1.1,
                                  tail_current_a=out["tail_current_a"],
                                  temperature_k=298.15)
        self.assertEqual(out["q29_base_current_a"], 0)
        self.assertAlmostEqual(out["q29_collector_current_a_candidate"],
                               old["q29_collector_current_a"], delta=1e-18)
        self.assertAlmostEqual(out["q30_collector_current_a_candidate"],
                               old["q30_collector_current_a"], delta=1e-18)

    def test_tail_solves_headroom_not_previous_imposed_tail(self):
        good = self.scenario()
        bad = self.scenario(q29_base_v=0.9, q30_base_v=0.9)
        self.assertGreater(good["tail_v"], bad["tail_v"])
        self.assertTrue(good["q28_forward_active_candidate"])
        self.assertFalse(bad["q28_forward_active_candidate"])
        self.assertIsNone(good["cutoff"]["q28_forward_active_candidate"])
        self.assertIsNone(good["cutoff"]["q28_collector_v_candidate"])
        without_tail = conditional_coupled_cutoff_dc(**CUTOFF)
        self.assertIsNone(without_tail["tail_v_imposed"])
        self.assertAlmostEqual(without_tail["q28_collector_current_a_candidate"],
                               good["tail_current_a"], delta=1e-18)

    def test_exponential_split_remains_finite_for_large_base_difference(self):
        out = self.scenario(q29_base_v=2, q30_base_v=0)
        self.assertTrue(math.isfinite(out["tail_v"]))
        self.assertGreater(out["q29_collector_current_a_candidate"], 0)
        self.assertGreaterEqual(out["q30_collector_current_a_candidate"], 0)
        self.assertAlmostEqual(out["tail_kcl_residual_a"], 0, delta=1e-18)

    def test_invalid_boundaries_rejected(self):
        for changes in ({"cutoff_inputs": CUTOFF | {"tail_v": 1}},
                        {"q29_base_v": math.nan}, {"is30_a": 0},
                        {"beta29": 1}, {"beta30": math.nan}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.scenario(**changes)


if __name__ == "__main__":
    unittest.main()
