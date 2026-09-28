"""Verify VCA Jacobian insertion and BUS-to-first-VCA small signal."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_recovery_active_dc_reference import DEVICES as RECOVERY_DEVICES, conditional_recovery_dc
from filter_vca1_active_small_signal_reference import active_loaded_matrices, filter_with_active_vca1
from filter_vca1_loaded_small_signal_reference import filter_with_passive_vca1, loaded_matrices
from vca1_active_core_dc_reference import DEVICES as VCA_DEVICES, conditional_vca1_dc


class FilterVca1ActiveSmallSignalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recovery = conditional_recovery_dc(
            is_a={n: 1e-14 for n in RECOVERY_DEVICES},
            beta_forward={n: 100 for n in RECOVERY_DEVICES},
            beta_reverse={n: 5 for n in RECOVERY_DEVICES}, temperature_k=298.15)
        cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                        scale_active_ohm=250, contour_pin16_v=0),
                      range_fraction_from_ground=0.1,
                      is26_a=1e-14, is28_a=1e-14,
                      beta26=100, beta28=100, temperature_k=298.15)
        cls.ladder = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={n: 1e-14 for n in UPPER},
            upper_beta={n: 100 for n in UPPER},
            reverse_beta={n: 5 for n in DEVICE_NODES},
            r61_ohm=200, r73_bottom_side_to_wiper_ohm=500)

    def vca(self, loudness):
        return conditional_vca1_dc(
            wiper_v=5, loudness_v=loudness, balance_left_ohm=12.5,
            is_a={n: 1e-14 for n in VCA_DEVICES},
            beta_forward={n: 100 for n in VCA_DEVICES},
            beta_reverse={n: 5 for n in VCA_DEVICES}, temperature_k=298.15)

    def solve(self, loudness, frequency):
        return filter_with_active_vca1(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            vca_dc=self.vca(loudness), frequency_hz=frequency,
            r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500)

    def test_no_duplicate_r34_r36_stamp(self):
        vca = self.vca(2)
        g, c, bus_c = active_loaded_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery, vca_dc=vca)
        old_g, old_c, old_bus_c = loaded_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery)
        self.assertEqual(len(g), 33)
        self.assertEqual(bus_c, old_bus_c)
        for row in (25, 26):
            for col in (25, 26):
                self.assertAlmostEqual(g[row][col],
                    old_g[row][col] + vca["conductance_matrix_s"][row - 25][col - 25]
                    + ({(25, 25): 1/820, (25, 26): -1/820,
                        (26, 25): -1/820, (26, 26): 1/820 + 1/510}[(row, col)]),
                    delta=1e-12)
                self.assertEqual(c[row][col], old_c[row][col])

    def test_envelope_changes_differential_collector_and_load(self):
        off = self.solve(0, 100)
        on = self.solve(2, 100)
        self.assertEqual(len(on["node_v_per_bus_v"]), 33)
        self.assertLess(off["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
        self.assertLess(on["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
        self.assertLess(abs(off["first_vca_differential_collector_v_per_bus_v"]), 1e-6)
        self.assertGreater(abs(on["first_vca_differential_collector_v_per_bus_v"]), 0.05)
        self.assertGreater(abs(off["q16_base_v_per_bus_v"]
                               - on["q16_base_v_per_bus_v"]), 0.001)
        passive = filter_with_passive_vca1(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            frequency_hz=100, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)
        self.assertGreater(abs(passive["q16_base_v_per_bus_v"]
                               - on["q16_base_v_per_bus_v"]), 0.001)

    def test_dc_is_blocked_and_frequencies_close_kcl(self):
        for frequency in (0, 30, 100, 1000):
            with self.subTest(frequency=frequency):
                out = self.solve(2, frequency)
                self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
                if frequency == 0:
                    self.assertEqual(out["first_vca_differential_collector_v_per_bus_v"], 0)
                    self.assertEqual(out["r2_current_a_per_bus_v"], 0)

    def test_mismatched_r73_rejected(self):
        with self.assertRaises(ValueError):
            filter_with_active_vca1(
                ladder_dc=self.ladder, recovery_dc=self.recovery,
                vca_dc=self.vca(2), frequency_hz=100,
                r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=501)


if __name__ == "__main__":
    unittest.main()
