"""AC current closure for the documented C10/R14/R73/Q30 path."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_emphasis_loop_small_signal_reference import (  # noqa: E402
    coupled_emphasis_small_signal, series_return_admittance_s)
from filter_ladder_active_dc_reference import UPPER  # noqa: E402
from filter_ladder_ebers_moll_dc_reference import (  # noqa: E402
    DEVICE_NODES, conditional_ladder_ebers_moll_dc)
from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc  # noqa: E402
from filter_recovery_active_small_signal_reference import (  # noqa: E402
    active_recovery_small_signal, coupled_matrices)


class EmphasisLoopTests(unittest.TestCase):
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

    def test_series_path_dc_and_resistive_limit(self):
        self.assertEqual(series_return_admittance_s(
            frequency_hz=0, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500), 0)
        y = series_return_admittance_s(
            frequency_hz=1e8, r14_pin7_to_pin6_ohm=25000,
            r73_bottom_side_to_wiper_ohm=500)
        self.assertAlmostEqual(y.real, 1 / 25500, delta=1e-11)
        low = series_return_admittance_s(
            frequency_hz=30, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500, c10_farads=9e-6)
        high = series_return_admittance_s(
            frequency_hz=30, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500, c10_farads=15e-6)
        self.assertNotEqual(low, high)

    def test_open_and_closed_differ_and_c10_blocks_dc(self):
        for r61, ladder in self.ladders.items():
            with self.subTest(r61=r61):
                zero = coupled_emphasis_small_signal(
                    ladder_dc=ladder, recovery_dc=self.recovery,
                    frequency_hz=0, r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500)
                self.assertEqual(zero["recovery_tap_v_per_bus_v"], 0)
                self.assertEqual(zero["return_current_a_per_bus_v"], 0)
                open_loop = active_recovery_small_signal(
                    ladder_dc=ladder, recovery_dc=self.recovery,
                    frequency_hz=100)
                closed = coupled_emphasis_small_signal(
                    ladder_dc=ladder, recovery_dc=self.recovery,
                    frequency_hz=100, r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500)
                self.assertNotAlmostEqual(
                    abs(open_loop["emphasis_pickoff_r7_r3_v_per_bus_v"]),
                    abs(closed["recovery_tap_v_per_bus_v"]), delta=0.01)
                self.assertGreater(abs(closed["return_current_a_per_bus_v"]), 1e-8)
                self.assertLess(closed["max_linear_kcl_residual_a_per_bus_v"], 1e-11)

    def test_branch_current_balances_original_kcl_at_both_terminals(self):
        ladder = self.ladders[200]
        out = coupled_emphasis_small_signal(
            ladder_dc=ladder, recovery_dc=self.recovery,
            frequency_hz=100, r14_pin7_to_pin6_ohm=25000,
            r73_bottom_side_to_wiper_ohm=500)
        g, c, c27 = coupled_matrices(ladder, self.recovery)
        s = 2j * math.pi * 100
        v = out["node_v_per_bus_v"]
        def baseline_residual(row):
            rhs = -s * c27 if row == 6 else 0
            return sum((g[row][j] - s * c[row][j]) * v[j]
                       for j in range(24)) - rhs
        current = out["return_current_a_per_bus_v"]
        self.assertAlmostEqual(abs(baseline_residual(22) - current), 0, delta=1e-11)
        self.assertAlmostEqual(abs(baseline_residual(7) + current), 0, delta=1e-11)

    def test_rejects_mismatched_dc_trimmer_and_invalid_controls(self):
        args = dict(ladder_dc=self.ladders[200], recovery_dc=self.recovery,
                    frequency_hz=100, r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500)
        for override in (dict(r73_bottom_side_to_wiper_ohm=501),
                         dict(r14_pin7_to_pin6_ohm=-1),
                         dict(frequency_hz=math.nan),
                         dict(c10_farads=8e-6)):
            with self.subTest(override=override), self.assertRaises(ValueError):
                coupled_emphasis_small_signal(**(args | override))


if __name__ == "__main__":
    unittest.main()
