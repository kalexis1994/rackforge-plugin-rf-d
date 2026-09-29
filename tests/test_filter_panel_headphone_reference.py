"""R21 topology, AC/reduced equivalence and transient current conservation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_panel_headphone_reference import (
    _headphone_parts, filter_with_panel_and_headphone,
    headphone_load_reduction, nonlinear_panel_headphone_step,
    panel_with_headphone_matrices)
from filter_panel_output_small_signal_reference import filter_with_panel_output
from filter_vca_output_small_signal_reference import filter_with_output
from filter_vca_output_transient_reference import initial_output_state


class PanelHeadphoneTest(unittest.TestCase):
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
                    r21_wiper_to_ground_ohm=2000,
                    headphone_wiper_load_ohm=32000)

    def test_graph_and_explicit_ac_match_reduction(self):
        self.assertEqual(_headphone_parts()["R21_PANEL"], 5000)
        hp = headphone_load_reduction(
            r21_wiper_to_ground_ohm=2000,
            headphone_wiper_load_ohm=32000)
        g, c, _ = panel_with_headphone_matrices(**self.args())
        self.assertEqual(len(g), 53)
        self.assertEqual(len(c), 53)
        self.assertAlmostEqual(g[47][51], 1/1000)
        self.assertAlmostEqual(g[51][52], 1/3000)
        self.assertAlmostEqual(g[52][52], -1/3000-1/2000-1/32000)
        for frequency in (0, 100, 1000):
            with self.subTest(frequency=frequency):
                explicit = filter_with_panel_and_headphone(
                    **self.args(), frequency_hz=frequency,
                    r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500)
                reduced = filter_with_panel_output(
                    ladder_dc=self.ladder, recovery_dc=self.recovery,
                    cascaded_output_dc=self.output_dc,
                    frequency_hz=frequency, r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500,
                    r20_wiper_to_ground_ohm=2500,
                    hi_load_ohm=10000, lo_load_ohm=100000,
                    headphone_input_ohm=hp["equivalent_headphone_input_ohm"])
                self.assertLess(explicit["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
                for key in ("c2_right_v_per_bus_v", "j4_hi_v_per_bus_v",
                            "j5_lo_v_per_bus_v"):
                    self.assertAlmostEqual(explicit[key], reduced[key], delta=1e-10)
                self.assertAlmostEqual(
                    explicit["r21_wiper_v_per_bus_v"],
                    explicit["board4_pin22_v_per_bus_v"]
                    * hp["wiper_to_pin22_ratio"], delta=1e-10)

    def test_wiper_load_changes_shared_c2_node(self):
        args = self.args()
        quiet = filter_with_panel_and_headphone(
            **args, frequency_hz=100, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)
        args["headphone_wiper_load_ohm"] = 100
        loaded = filter_with_panel_and_headphone(
            **args, frequency_hz=100, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)
        self.assertGreater(abs(quiet["c2_right_v_per_bus_v"]
                               - loaded["c2_right_v_per_bus_v"]), 1e-6)

    def test_nonlinear_step_r21_kcl(self):
        initial = initial_output_state(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc)
        out = nonlinear_panel_headphone_step(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            previous_node_v=initial["node_v"],
            previous_c10_capacitor_v=initial["c10_capacitor_v"],
            previous_bus_v=0, bus_v=0.1, dt_s=1/48000,
            r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500,
            r20_wiper_to_ground_ohm=2500,
            hi_load_ohm=10000, lo_load_ohm=100000,
            r21_wiper_to_ground_ohm=2000,
            headphone_wiper_load_ohm=32000)
        self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
        self.assertAlmostEqual(out["headphone_pin22_current_a"],
                               out["r21_upper_current_a"], delta=1e-12)
        self.assertAlmostEqual(out["r21_upper_current_a"],
                               out["r21_lower_current_a"]
                               + out["headphone_wiper_load_current_a"],
                               delta=1e-12)
        self.assertAlmostEqual(out["c2_current_a"],
                               out["main_pin21_current_a"]
                               + out["headphone_pin22_current_a"],
                               delta=1e-10)

    def test_sw18_off_shunts_r20_wiper_and_silences_hi_lo(self):
        args = self.args()
        hp = headphone_load_reduction(
            r21_wiper_to_ground_ohm=2000,
            headphone_wiper_load_ohm=32000)
        g, _, _ = panel_with_headphone_matrices(**args, sw18_on=False)
        self.assertEqual(g[48][49], 0)
        self.assertEqual(g[49][48], 0)
        self.assertAlmostEqual(g[48][48], -1/1000-1/2500)
        off = filter_with_panel_and_headphone(
            **args, sw18_on=False, frequency_hz=100,
            r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500)
        simple = filter_with_output(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            frequency_hz=100, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500,
            main_load_ohm=2500,
            headphone_input_ohm=hp["equivalent_headphone_input_ohm"])
        self.assertEqual(off["j4_hi_v_per_bus_v"], 0)
        self.assertEqual(off["j5_lo_v_per_bus_v"], 0)
        self.assertAlmostEqual(off["c2_right_v_per_bus_v"],
                               simple["c2_right_v_per_bus_v"], delta=1e-10)
        self.assertLess(off["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
        initial = initial_output_state(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc)
        step = nonlinear_panel_headphone_step(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            previous_node_v=initial["node_v"],
            previous_c10_capacitor_v=initial["c10_capacitor_v"],
            previous_bus_v=0, bus_v=0.1, dt_s=1/48000,
            r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500,
            r20_wiper_to_ground_ohm=2500,
            hi_load_ohm=10000, lo_load_ohm=100000,
            r21_wiper_to_ground_ohm=2000,
            headphone_wiper_load_ohm=32000, sw18_on=False)
        self.assertEqual(step["j4_hi_v"], 0)
        self.assertEqual(step["j5_lo_v"], 0)
        self.assertAlmostEqual(step["main_pin21_current_a"],
                               step["r20_upper_current_a"], delta=1e-12)
        self.assertAlmostEqual(step["headphone_pin22_current_a"],
                               step["r21_upper_current_a"], delta=1e-12)
        self.assertLess(step["max_charge_kcl_residual_a"], 1e-10)


if __name__ == "__main__":
    unittest.main()
