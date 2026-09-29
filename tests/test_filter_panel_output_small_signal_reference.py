"""Panel HI/LO divider, loading and full 50-node AC conservation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_panel_output_small_signal_reference import (
    _panel_parts, filter_with_panel_output, panel_output_matrices)
from filter_vca_output_small_signal_reference import filter_with_output


class FilterPanelOutputSmallSignalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca_output_small_signal_reference import FilterVcaOutputSmallSignalTest
        FilterVcaOutputSmallSignalTest.setUpClass()
        fixture = FilterVcaOutputSmallSignalTest()
        cls.ladder = fixture.ladder
        cls.recovery = fixture.recovery
        cls.output_dc = fixture.dc()

    def ac(self, frequency, hi_load=1e6, lo_load=1e6,
           r20_lower=2500):
        return filter_with_panel_output(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            frequency_hz=frequency, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500,
            r20_wiper_to_ground_ohm=r20_lower,
            hi_load_ohm=hi_load, lo_load_ohm=lo_load,
            headphone_input_ohm=100000)

    def test_documented_divider_stamped_with_kcl_sign(self):
        self.assertEqual(_panel_parts()["R57_PANEL"], 33000)
        self.assertEqual(_panel_parts()["R58_PANEL"], 1000)
        self.assertEqual(_panel_parts()["R20_PANEL"], 5000)
        g, c, _ = panel_output_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            r20_wiper_to_ground_ohm=2500,
            hi_load_ohm=1e6, lo_load_ohm=1e6,
            headphone_input_ohm=100000)
        self.assertEqual(len(g), 51)
        self.assertEqual(len(c), 51)
        self.assertAlmostEqual(g[49][50], 1/33000)
        self.assertAlmostEqual(g[50][50], -1/33000-1/1000-1/1e6)
        self.assertAlmostEqual(g[47][48], 1/1000)
        self.assertAlmostEqual(g[48][49], 1/2500)

    def test_hi_lo_ratio_and_zero_frequency(self):
        for frequency in (0, 30, 100, 1000):
            with self.subTest(frequency=frequency):
                out = self.ac(frequency)
                self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"],
                                1e-11)
                if frequency == 0:
                    self.assertEqual(out["j4_hi_v_per_bus_v"], 0)
                    self.assertEqual(out["j5_lo_v_per_bus_v"], 0)
                else:
                    effective_low = 1/(1/1000+1/1e6)
                    expected_ratio = effective_low/(33000+effective_low)
                    self.assertAlmostEqual(out["hi_to_lo_ratio"].real,
                                           expected_ratio, delta=1e-11)
                    self.assertAlmostEqual(out["hi_to_lo_ratio"].imag,
                                           0, delta=1e-11)

    def test_matches_equivalent_main_load(self):
        hi_load, lo_load = 10000, 100000
        low_shunt = 1/(1/1000+1/lo_load)
        hi_shunt = 1/(1/hi_load+1/(33000+low_shunt))
        wiper_shunt = 1/(1/2500+1/hi_shunt)
        equivalent = 2500+wiper_shunt
        panel = self.ac(100, hi_load=hi_load, lo_load=lo_load)
        simple = filter_with_output(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            frequency_hz=100, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500,
            main_load_ohm=equivalent,
            headphone_input_ohm=100000)
        self.assertAlmostEqual(panel["c2_right_v_per_bus_v"].real,
                               simple["c2_right_v_per_bus_v"].real,
                               delta=1e-10)
        self.assertAlmostEqual(panel["c2_right_v_per_bus_v"].imag,
                               simple["c2_right_v_per_bus_v"].imag,
                               delta=1e-10)
        self.assertAlmostEqual(panel["board4_pin21_v_per_bus_v"].real,
                               simple["main_pin21_v_per_bus_v"].real,
                               delta=1e-10)

    def test_r20_cursor_changes_hi_level_but_not_hi_lo_divider(self):
        low = self.ac(100, r20_lower=500)
        high = self.ac(100, r20_lower=4500)
        self.assertLess(abs(low["j4_hi_v_per_bus_v"]),
                        abs(high["j4_hi_v_per_bus_v"]))
        self.assertAlmostEqual(low["hi_to_lo_ratio"].real,
                               high["hi_to_lo_ratio"].real,
                               delta=1e-11)


if __name__ == "__main__":
    unittest.main()
