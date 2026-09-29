"""Manufacturer bounds, diode polarity and propagation through output oracles."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from output_diode_reference import diode_current_a, diode_model_from_reference
from semiconductor_ideal import thermal_voltage_v
from vca_output_conversion_dc_reference import (
    DEVICES, _evaluate as conversion_kcl, conditional_output_conversion_dc)
from vca_cascaded_output_dc_reference import (
    DEVICE_NAMES, conditional_cascaded_output_dc)
from filter_vca_output_small_signal_reference import filter_with_output
from filter_vca_output_transient_reference import (
    initial_output_state, nonlinear_output_step)


class OutputDiodeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.9,
            temperature_k=298.15)

    def test_manufacturer_bound_and_assumed_forward_point(self):
        vt = thermal_voltage_v(298.15)
        self.assertAlmostEqual(diode_current_a(
            0.9, model=self.model, vt=vt), 0.1, delta=1e-12)
        self.assertLess(abs(diode_current_a(
            -125, model=self.model, vt=vt)), 25e-9)
        self.assertLess(diode_current_a(0.5, model=self.model, vt=vt), 0.1)
        for voltage in (0, 1.01):
            with self.assertRaises(ValueError):
                diode_model_from_reference(
                    ideality=1.5, forward_voltage_at_100ma_v=voltage,
                    temperature_k=298.15)
        with self.assertRaises(ValueError):
            diode_model_from_reference(
                ideality=3, forward_voltage_at_100ma_v=0.9,
                temperature_k=298.15)

    def test_cr1_cr2_kcl_polarity_and_isolated_solution(self):
        params = dict(is_a={n: 1e-14 for n in DEVICES},
                      beta_forward={n: 100 for n in DEVICES},
                      beta_reverse={n: 5 for n in DEVICES},
                      temperature_k=298.15)
        dc = conditional_output_conversion_dc(
            q1_base_v=8.3, q12_base_v=7.75, q17_base_v=7.75,
            diode_model=self.model, **params)
        self.assertFalse(dc["diodes_assumed_open"])
        self.assertLess(dc["max_kcl_residual_a"], 1e-12)
        for q17_collector_v, q17_base_v, q17_emitter_v in (
                (-0.5, 0.0, 0.5), (10.5, 10.0, 10.5)):
            x = list(dc["nodes_v"].values())
            x[3] = q17_emitter_v
            x[5] = q17_collector_v
            with_diode, _ = conversion_kcl(
                x, **(dc["network_parameters"] | {
                    "q17_base_v": q17_base_v}))
            no_diode, _ = conversion_kcl(
                x, **(dc["network_parameters"] | {
                    "q17_base_v": q17_base_v, "diode_model": None}))
            vt = dc["network_parameters"]["vt"]
            cr1 = diode_current_a(q17_collector_v-10,
                                  model=self.model, vt=vt)
            cr2 = diode_current_a(-q17_collector_v,
                                  model=self.model, vt=vt)
            self.assertAlmostEqual(with_diode[5]-no_diode[5],
                                   -cr1+cr2, delta=1e-12)
            self.assertGreater(abs(with_diode[5]-no_diode[5]), 1e-7)

    def test_coupled_ac_and_transient_reuse_diode_bias(self):
        from test_filter_vca_output_small_signal_reference import FilterVcaOutputSmallSignalTest
        FilterVcaOutputSmallSignalTest.setUpClass()
        dc = conditional_cascaded_output_dc(
            first_loudness_v=2, second_loudness_base_v=2,
            first_balance_left_ohm=12.5, second_balance_left_ohm=50,
            is_a={n: 1e-14 for n in DEVICE_NAMES},
            beta_forward={n: 100 for n in DEVICE_NAMES},
            beta_reverse={n: 5 for n in DEVICE_NAMES},
            temperature_k=298.15, diode_model=self.model)
        self.assertLess(dc["max_kcl_residual_a"], 1e-12)
        fixture = FilterVcaOutputSmallSignalTest()
        ac = filter_with_output(
            ladder_dc=fixture.ladder, recovery_dc=fixture.recovery,
            cascaded_output_dc=dc, frequency_hz=100,
            r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500,
            main_load_ohm=10000, headphone_input_ohm=100000)
        self.assertFalse(ac["diodes_assumed_open"])
        self.assertLess(ac["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
        initial = initial_output_state(
            ladder_dc=fixture.ladder, recovery_dc=fixture.recovery,
            cascaded_output_dc=dc)
        step = nonlinear_output_step(
            ladder_dc=fixture.ladder, recovery_dc=fixture.recovery,
            cascaded_output_dc=dc, previous_node_v=initial["node_v"],
            previous_c10_capacitor_v=initial["c10_capacitor_v"],
            previous_bus_v=0, bus_v=0.1, dt_s=1/48000,
            r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500,
            main_load_ohm=10000, headphone_input_ohm=100000)
        self.assertFalse(step["diodes_assumed_open"])
        self.assertLess(step["max_charge_kcl_residual_a"], 1e-10)
        self.assertTrue(math.isfinite(step["main_pin21_v"]))


if __name__ == "__main__":
    unittest.main()
