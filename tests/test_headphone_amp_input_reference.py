"""Board-3 passive headphone input and its coupled AC boundary."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from headphone_amp_input_reference import (
    Q16_BASE, _input_parts, filter_with_passive_headphone_input,
    passive_amp_input_matrices, passive_input_impedance_ohm)


class HeadphoneAmpInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca_output_small_signal_reference import FilterVcaOutputSmallSignalTest
        FilterVcaOutputSmallSignalTest.setUpClass()
        fixture = FilterVcaOutputSmallSignalTest()
        cls.ladder = fixture.ladder
        cls.recovery = fixture.recovery
        cls.output_dc = fixture.dc()

    def args(self):
        return dict(ladder_dc=self.ladder, recovery_dc=self.recovery,
                    cascaded_output_dc=self.output_dc,
                    r20_wiper_to_ground_ohm=2500,
                    hi_load_ohm=10000, lo_load_ohm=100000,
                    r21_wiper_to_ground_ohm=2000)

    def solve(self, frequency, sw18_on=True):
        return filter_with_passive_headphone_input(
            **self.args(), frequency_hz=frequency, sw18_on=sw18_on,
            r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500)

    def test_schematic_values_and_passive_input_impedance(self):
        self.assertEqual(_input_parts(), (2.5e-6, 6200, 24000))
        self.assertIsNone(passive_input_impedance_ohm(0))
        bias = 1/(1/6200+1/24000)
        for frequency in (30, 100, 1000):
            with self.subTest(frequency=frequency):
                expected = bias+1/(2j*math.pi*frequency*2.5e-6)
                self.assertAlmostEqual(passive_input_impedance_ohm(frequency),
                                       expected, delta=1e-12)
        for invalid in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                passive_input_impedance_ohm(invalid)

    def test_capacitor_and_bias_kcl_stamps(self):
        g, c, _ = passive_amp_input_matrices(**self.args())
        self.assertEqual(len(g), 54)
        self.assertAlmostEqual(g[Q16_BASE][Q16_BASE], -1/6200-1/24000)
        self.assertAlmostEqual(g[52][52], -1/3000-1/2000, delta=1e-15)
        self.assertEqual(g[52][Q16_BASE], 0)
        self.assertAlmostEqual(c[52][Q16_BASE], -2.5e-6)
        self.assertAlmostEqual(c[Q16_BASE][52], -2.5e-6)
        self.assertAlmostEqual(c[Q16_BASE][Q16_BASE], 2.5e-6)

    def test_q16_base_is_passive_high_pass_boundary(self):
        bias = 1/(1/6200+1/24000)
        for frequency in (0, 30, 100, 1000):
            with self.subTest(frequency=frequency):
                out = self.solve(frequency)
                self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
                if frequency == 0:
                    self.assertEqual(out["q16_base_v_per_bus_v"], 0)
                else:
                    expected = bias/(bias+1/(2j*math.pi*frequency*2.5e-6))
                    self.assertAlmostEqual(
                        out["q16_base_v_per_bus_v"]
                        / out["r21_wiper_v_per_bus_v"], expected, delta=1e-11)
        off = self.solve(100, sw18_on=False)
        self.assertEqual(off["j4_hi_v_per_bus_v"], 0)
        self.assertEqual(off["j5_lo_v_per_bus_v"], 0)
        self.assertGreater(abs(off["q16_base_v_per_bus_v"]), 1e-6)


if __name__ == "__main__":
    unittest.main()
