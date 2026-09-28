"""Active-stack current accounting and conditional headroom tests."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_reference import UPPER, conditional_ladder_active_dc


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class LadderActiveDCTests(unittest.TestCase):
    def scenario(self, r61=200, beta=100):
        return conditional_ladder_active_dc(
            cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: beta for name in UPPER},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)

    def test_each_tap_withdrawal_is_sum_of_two_base_currents(self):
        out = self.scenario()
        pairs = (("Q2", "Q3"), ("Q10", "Q11"),
                 ("Q19", "Q20"), ("Q23", "Q24"))
        for pair, withdrawal in zip(pairs, out["tap_withdrawals_a_derived"]):
            self.assertAlmostEqual(withdrawal,
                                   sum(out["upper_devices"][name]["base_a"]
                                       for name in pair), delta=1e-20)
        self.assertAlmostEqual(out["spine"]["bottom_voltage_residual_v"], 0,
                               delta=1e-14)
        self.assertAlmostEqual(out["lower"]["bottom_kcl_residual_a"], 0,
                               delta=1e-17)

    def test_each_serial_connection_conserves_current_and_voltage(self):
        out = self.scenario()
        for lower, higher in (("Q29", "Q23"), ("Q23", "Q19"),
                              ("Q19", "Q10"), ("Q10", "Q2"),
                              ("Q30", "Q24"), ("Q24", "Q20"),
                              ("Q20", "Q11"), ("Q11", "Q3")):
            higher_device = out["upper_devices"][higher]
            lower_collector = (out["lower"]["lower_pair"]["q29_collector_current_a_candidate"]
                               if lower == "Q29" else
                               out["lower"]["lower_pair"]["q30_collector_current_a_candidate"]
                               if lower == "Q30" else
                               out["upper_devices"][lower]["collector_a"])
            self.assertAlmostEqual(higher_device["emitter_a"], lower_collector,
                                   delta=1e-19)
            if lower not in ("Q29", "Q30"):
                self.assertAlmostEqual(out["upper_devices"][lower]["collector_v"],
                                       higher_device["emitter_v"], delta=1e-14)

    def test_candidate_headroom_flags_do_not_select_physical_r61(self):
        low = self.scenario(200)
        high = self.scenario(200000)
        self.assertTrue(low["all_ten_forward_active_candidates"])
        self.assertFalse(high["all_ten_forward_active_candidates"])
        self.assertTrue(any(v < 0 for v in high["v_cb_margins_v"].values()))
        self.assertTrue(low["physical_r61_unresolved"])
        self.assertTrue(high["physical_r61_unresolved"])

    def test_infinite_upper_beta_removes_spine_base_loads(self):
        out = self.scenario(beta=math.inf)
        self.assertEqual(out["tap_withdrawals_a_derived"], (0, 0, 0, 0))
        for name in UPPER:
            self.assertEqual(out["upper_devices"][name]["base_a"], 0)
        self.assertAlmostEqual(out["bottom_injection_a"],
                               out["spine"]["bottom_injection_a"])

    def test_missing_or_invalid_upper_device_parameters_rejected(self):
        args = dict(cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
                    beta29=100, beta30=100,
                    upper_is_a={name: 1e-14 for name in UPPER},
                    upper_beta={name: 100 for name in UPPER},
                    r61_ohm=200, r73_bottom_side_to_wiper_ohm=500)
        for changed in (dict(upper_is_a={name: 1e-14 for name in UPPER[:-1]}),
                        dict(upper_beta={name: math.nan if name == "Q2" else 100
                                         for name in UPPER}),
                        dict(upper_is_a={name: 0 if name == "Q3" else 1e-14
                                         for name in UPPER})):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                conditional_ladder_active_dc(**(args | changed))


if __name__ == "__main__":
    unittest.main()
