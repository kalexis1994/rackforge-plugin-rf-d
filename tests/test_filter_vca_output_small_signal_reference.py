"""Forty-eight-node AC from filter bus to loaded board-4 output pins."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_vca_output_small_signal_reference import (
    filter_with_output, loaded_output_matrices)
from vca_cascaded_output_dc_reference import (DEVICE_NAMES,
                                               conditional_cascaded_output_dc)


class FilterVcaOutputSmallSignalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca1_active_small_signal_reference import FilterVca1ActiveSmallSignalTest
        FilterVca1ActiveSmallSignalTest.setUpClass()
        cls.ladder = FilterVca1ActiveSmallSignalTest.ladder
        cls.recovery = FilterVca1ActiveSmallSignalTest.recovery

    def dc(self, control=2):
        return conditional_cascaded_output_dc(
            first_loudness_v=control, second_loudness_base_v=control,
            first_balance_left_ohm=12.5, second_balance_left_ohm=50,
            is_a={n: 1e-14 for n in DEVICE_NAMES},
            beta_forward={n: 100 for n in DEVICE_NAMES},
            beta_reverse={n: 5 for n in DEVICE_NAMES},
            temperature_k=298.15)

    def ac(self, frequency, load=10000):
        return filter_with_output(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.dc(), frequency_hz=frequency,
            r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500,
            main_load_ohm=load, headphone_input_ohm=100000)

    def test_coupling_and_supply_capacitance_stamps(self):
        g, c, _ = loaded_output_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.dc(),
            main_load_ohm=10000, headphone_input_ohm=100000)
        self.assertEqual(len(g), 48)
        self.assertAlmostEqual(c[40][40], 220e-6)
        self.assertAlmostEqual(c[46][47], -10e-6)
        self.assertAlmostEqual(c[47][46], -10e-6)
        self.assertAlmostEqual(g[47][47], -1/11000 - 1/101000)

    def test_dc_blocking_and_loaded_signal(self):
        for frequency in (0, 30, 100, 1000):
            with self.subTest(frequency=frequency):
                out = self.ac(frequency)
                self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"],
                                1e-11)
                if frequency == 0:
                    self.assertEqual(out["main_pin21_v_per_bus_v"], 0)
                else:
                    self.assertGreater(abs(out["main_pin21_v_per_bus_v"]), 0)
                    self.assertLess(abs(out["main_pin21_v_per_bus_v"]),
                                    abs(out["c2_right_v_per_bus_v"]))

    def test_declared_load_changes_output(self):
        high = self.ac(100, load=100000)
        low = self.ac(100, load=1000)
        self.assertGreater(abs(high["main_pin21_v_per_bus_v"]),
                           abs(low["main_pin21_v_per_bus_v"]))


if __name__ == "__main__":
    unittest.main()
