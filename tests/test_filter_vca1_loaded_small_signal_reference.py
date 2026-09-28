"""Loaded recovery collector and passive first-VCA input consistency."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_emphasis_loop_small_signal_reference import coupled_emphasis_small_signal
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc
from filter_vca1_loaded_small_signal_reference import filter_with_passive_vca1
from vca1_input_boundary_reference import passive_vca1_input


class FilterVca1LoadedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recovery = conditional_recovery_dc(
            is_a={name: 1e-14 for name in DEVICES},
            beta_forward={name: 100 for name in DEVICES},
            beta_reverse={name: 5 for name in DEVICES}, temperature_k=298.15)
        cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                        scale_active_ohm=250, contour_pin16_v=0),
                      range_fraction_from_ground=0.1,
                      is26_a=1e-14, is28_a=1e-14,
                      beta26=100, beta28=100, temperature_k=298.15)
        cls.ladders = {r61: conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)
            for r61 in (200, 200000)}

    def test_loaded_network_matches_isolated_input_ratio_and_kcl(self):
        for r61, ladder in self.ladders.items():
            for frequency in (30, 100, 1000):
                with self.subTest(r61=r61, frequency=frequency):
                    out = filter_with_passive_vca1(
                        ladder_dc=ladder, recovery_dc=self.recovery,
                        frequency_hz=frequency, r14_pin7_to_pin6_ohm=0,
                        r73_bottom_side_to_wiper_ohm=500)
                    isolated = passive_vca1_input(frequency_hz=frequency)
                    ratio = (out["q16_base_v_per_bus_v"]
                             / out["recovery_collector_v_per_bus_v"])
                    self.assertAlmostEqual(abs(
                        ratio - isolated["q16_base_v_per_recovery_v"]),
                        0, delta=1e-10)
                    v = out["node_v_per_bus_v"]
                    self.assertAlmostEqual(abs(out["r2_current_a_per_bus_v"]
                                               - 2j * 3.141592653589793 * frequency
                                               * 0.33e-6 * (v[24] - v[25])),
                                           0, delta=1e-11)
                    self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"], 1e-11)

    def test_passive_input_loads_recovery_and_blocks_dc(self):
        ladder = self.ladders[200]
        zero = filter_with_passive_vca1(
            ladder_dc=ladder, recovery_dc=self.recovery,
            frequency_hz=0, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)
        self.assertEqual(zero["q16_base_v_per_bus_v"], 0)
        loaded = filter_with_passive_vca1(
            ladder_dc=ladder, recovery_dc=self.recovery,
            frequency_hz=100, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)
        open_loop = coupled_emphasis_small_signal(
            ladder_dc=ladder, recovery_dc=self.recovery,
            frequency_hz=100, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)
        self.assertNotAlmostEqual(
            abs(loaded["recovery_collector_v_per_bus_v"]),
            abs(open_loop["recovery_collector_v_per_bus_v"]), delta=1e-4)

    def test_mismatched_trimmer_rejected(self):
        with self.assertRaises(ValueError):
            filter_with_passive_vca1(
                ladder_dc=self.ladders[200], recovery_dc=self.recovery,
                frequency_hz=100, r14_pin7_to_pin6_ohm=0,
                r73_bottom_side_to_wiper_ohm=501)


if __name__ == "__main__":
    unittest.main()
