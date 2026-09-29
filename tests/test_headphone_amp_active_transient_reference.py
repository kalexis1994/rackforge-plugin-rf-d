"""Nonlinear output conduction, capacitor charge and loaded J7 KCL."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_diode_reference import diode_model_from_reference


class HeadphoneAmpActiveTransientTest(unittest.TestCase):
    def parameters(self):
        return dict(transistor_is_a=1e-14, beta_forward=160,
                    beta_reverse=5, temperature_k=300,
                    diode_model=diode_model_from_reference(
                        ideality=1.5, forward_voltage_at_100ma_v=0.7,
                        temperature_k=300))

    def test_dc_initialization_and_rest_are_charge_consistent(self):
        parameters = self.parameters()
        state = initial_headphone_amp_state(**parameters)
        rest = nonlinear_headphone_amp_step(
            previous_state=state, pin7_v=0, dt_s=1/48000,
            tip_load_ohm=32, ring_load_ohm=32, **parameters)
        self.assertLess(rest["max_charge_kcl_residual_a"], 1e-11)
        self.assertEqual(rest["j7_tip_v"], 0)
        self.assertEqual(rest["j7_ring_v"], 0)
        for name, voltage in state["capacitor_v"].items():
            self.assertAlmostEqual(rest["capacitor_v"][name], voltage,
                                   delta=1e-10)

    def test_loaded_signal_conducts_and_preserves_each_charge_kcl(self):
        parameters = self.parameters()
        state = initial_headphone_amp_state(**parameters)
        for input_v in (-1, -0.1, -0.01, 0.01, 0.1, 1):
            with self.subTest(input_v=input_v):
                result = nonlinear_headphone_amp_step(
                    previous_state=state, pin7_v=input_v,
                    dt_s=1/48000, tip_load_ohm=32,
                    ring_load_ohm=32, **parameters)
                self.assertLess(result["max_charge_kcl_residual_a"], 1e-10)
                self.assertEqual(result["j7_tip_v"], result["j7_ring_v"])
                self.assertAlmostEqual(
                    result["capacitor_currents_a"]["C21"],
                    (1/390+2/32)*result["j7_tip_v"], delta=1e-10)
                self.assertGreater(input_v*result["j7_tip_v"], 0)
        small = nonlinear_headphone_amp_step(
            previous_state=state, pin7_v=0.01, dt_s=1/48000,
            tip_load_ohm=32, ring_load_ohm=32, **parameters)
        large = nonlinear_headphone_amp_step(
            previous_state=state, pin7_v=1, dt_s=1/48000,
            tip_load_ohm=32, ring_load_ohm=32, **parameters)
        self.assertGreater(large["j7_tip_v"]/1,
                           4*small["j7_tip_v"]/0.01)

    def test_successive_steps_and_invalid_domain(self):
        parameters = self.parameters()
        state = initial_headphone_amp_state(**parameters)
        for _ in range(20):
            state = nonlinear_headphone_amp_step(
                previous_state=state, pin7_v=0.1,
                dt_s=1/48000, tip_load_ohm=32,
                ring_load_ohm=32, **parameters)
            self.assertLess(state["max_charge_kcl_residual_a"], 1e-10)
        with self.assertRaises(ValueError):
            nonlinear_headphone_amp_step(
                previous_state=state, pin7_v=0.1, dt_s=0, **parameters)
        with self.assertRaises(ValueError):
            nonlinear_headphone_amp_step(
                previous_state=state, pin7_v=0.1,
                dt_s=1/48000, tip_load_ohm=-32, **parameters)


if __name__ == "__main__":
    unittest.main()
