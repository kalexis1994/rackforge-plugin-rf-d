"""Simultaneous board-4/R21/board-3 charge conservation and split-oracle check."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_panel_output_transient_reference import panel_load_reduction
from filter_vca_output_transient_reference import nonlinear_output_step
from headphone_amp_active_transient_reference import nonlinear_headphone_amp_step
from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from output_diode_reference import diode_model_from_reference


class HeadphoneCoupledTransientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca_output_small_signal_reference import FilterVcaOutputSmallSignalTest
        FilterVcaOutputSmallSignalTest.setUpClass()
        fixture = FilterVcaOutputSmallSignalTest()
        cls.ladder = fixture.ladder
        cls.recovery = fixture.recovery
        cls.output_dc = fixture.dc()

    def device(self):
        return dict(transistor_is_a=1e-14, beta_forward=160,
                    beta_reverse=5, temperature_k=300,
                    diode_model=diode_model_from_reference(
                        ideality=1.5, forward_voltage_at_100ma_v=0.7,
                        temperature_k=300))

    def args(self):
        return dict(ladder_dc=self.ladder, recovery_dc=self.recovery,
                    cascaded_output_dc=self.output_dc,
                    r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500,
                    r20_wiper_to_ground_ohm=2500,
                    hi_load_ohm=10000, lo_load_ohm=100000,
                    r21_wiper_to_ground_ohm=2000,
                    tip_load_ohm=32, ring_load_ohm=32, **self.device())

    def initial(self):
        return initial_coupled_headphone_state(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc, **self.device())

    def test_rest_and_loaded_steps_preserve_62_node_kcl(self):
        state = self.initial()
        for input_v in (0, 0.01, 0.1):
            with self.subTest(input_v=input_v):
                result = nonlinear_coupled_headphone_step(
                    **self.args(), previous_state=state,
                    bus_v=input_v, dt_s=1/48000)
                self.assertEqual(len(result["node_v"]), 62)
                self.assertLess(result["max_charge_kcl_residual_a"], 1e-10)
                self.assertAlmostEqual(result["r77_current_a"],
                                       result["r21_upper_current_a"], delta=1e-10)
                self.assertAlmostEqual(
                    result["r21_upper_current_a"],
                    result["r21_lower_current_a"]+result["c19_current_a"],
                    delta=1e-10)
                self.assertAlmostEqual(result["c21_current_a"],
                                       (1/390+2/32)*result["j7_tip_v"],
                                       delta=1e-10)
                self.assertEqual(result["j7_tip_v"], result["j7_ring_v"])
                if input_v == 0:
                    self.assertEqual(result["j7_tip_v"], 0)

    def test_split_board_oracles_agree_at_monolithic_solution(self):
        state = self.initial()
        args = self.args()
        result = nonlinear_coupled_headphone_step(
            **args, previous_state=state, bus_v=0.1, dt_s=1/48000)
        amp_previous = {"node_v": state["node_v"][50:62],
                        "capacitor_v": state["amp_capacitor_v"],
                        "previous_pin7_v": 0}
        isolated_amp = nonlinear_headphone_amp_step(
            previous_state=amp_previous, pin7_v=result["r21_wiper_v"],
            dt_s=1/48000, tip_load_ohm=32, ring_load_ohm=32,
            **self.device())
        self.assertAlmostEqual(isolated_amp["j7_tip_v"], result["j7_tip_v"],
                               delta=1e-10)
        for actual, expected in zip(result["node_v"][50:62],
                                    isolated_amp["node_v"]):
            self.assertAlmostEqual(actual, expected, delta=1e-9)
        # At this particular step, the solved R21/C19 branch is equivalent
        # to a positive instantaneous resistance seen from C2_RIGHT.
        equivalent_headphone_ohm = (
            result["c2_right_v"]/result["r77_current_a"]-1000)
        self.assertGreater(equivalent_headphone_ohm, 0)
        main = panel_load_reduction(
            r20_wiper_to_ground_ohm=2500,
            hi_load_ohm=10000, lo_load_ohm=100000)
        isolated_output = nonlinear_output_step(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            previous_node_v=state["node_v"][:48],
            previous_c10_capacitor_v=state["c10_capacitor_v"],
            previous_bus_v=0, bus_v=0.1, dt_s=1/48000,
            r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500,
            main_load_ohm=main["equivalent_main_load_ohm"],
            headphone_input_ohm=equivalent_headphone_ohm)
        for actual, expected in zip(result["node_v"][:48],
                                    isolated_output["node_v"]):
            self.assertAlmostEqual(actual, expected, delta=1e-9)

    def test_sw18_off_and_state_progress(self):
        state = self.initial()
        args = self.args()
        for step in range(10):
            state = nonlinear_coupled_headphone_step(
                **args, previous_state=state, bus_v=0.1,
                dt_s=1/48000, sw18_on=False)
            self.assertEqual(state["j4_hi_v"], 0)
            self.assertEqual(state["j5_lo_v"], 0)
            self.assertLess(state["max_charge_kcl_residual_a"], 1e-10)
        self.assertGreater(abs(state["j7_tip_v"]), 0)
        with self.assertRaises(ValueError):
            nonlinear_coupled_headphone_step(
                **args, previous_state=state, bus_v=0.1, dt_s=0)
        with self.assertRaises(ValueError):
            nonlinear_coupled_headphone_step(
                **args, previous_state=state, bus_v=0.1,
                dt_s=1/48000, jacobian_method="unknown")


if __name__ == "__main__":
    unittest.main()
