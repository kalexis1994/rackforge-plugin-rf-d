"""AC tangent of the same nonlinear DC point, through C19/C15/C21 and J7."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_amp_active_ac_reference import conditional_headphone_amp_ac
from headphone_output_coupling_reference import output_ac
from output_diode_reference import diode_model_from_reference


class HeadphoneAmpActiveAcTest(unittest.TestCase):
    def params(self):
        return dict(transistor_is_a=1e-14, beta_forward=160,
                    beta_reverse=5, temperature_k=300,
                    diode_model=diode_model_from_reference(
                        ideality=1.5, forward_voltage_at_100ma_v=0.7,
                        temperature_k=300))

    def test_dc_open_and_loaded_ac_kcl(self):
        for frequency in (0, 30, 100, 1000, 10000):
            with self.subTest(frequency=frequency):
                result = conditional_headphone_amp_ac(
                    **self.params(), frequency_hz=frequency,
                    tip_load_ohm=32, ring_load_ohm=32)
                self.assertLess(result["max_linear_kcl_residual_a_per_pin7_v"], 1e-12)
                self.assertLess(result["dc_max_kcl_residual_a"], 1e-11)
                self.assertTrue(result["linearized_at_same_dc_parameters"])
                self.assertEqual(result["j7_tip_v_per_pin7_v"],
                                 result["j7_ring_v_per_pin7_v"])
                if frequency == 0:
                    self.assertEqual(result["pre_c21_v_per_pin7_v"], 0)
                    self.assertEqual(result["j7_tip_v_per_pin7_v"], 0)
                else:
                    isolated = output_ac(frequency_hz=frequency,
                                         tip_load_ohm=32, ring_load_ohm=32)
                    self.assertAlmostEqual(
                        result["j7_tip_v_per_pin7_v"]
                        / result["pre_c21_v_per_pin7_v"],
                        isolated["j7_tip_v_per_pre_c21_v"], delta=1e-11)

    def test_external_load_alters_active_stage_not_only_c21_ratio(self):
        unloaded = conditional_headphone_amp_ac(
            **self.params(), frequency_hz=100)
        one_driver = conditional_headphone_amp_ac(
            **self.params(), frequency_hz=100, tip_load_ohm=32)
        two_drivers = conditional_headphone_amp_ac(
            **self.params(), frequency_hz=100,
            tip_load_ohm=32, ring_load_ohm=32)
        self.assertGreater(abs(unloaded["pre_c21_v_per_pin7_v"]),
                           abs(one_driver["pre_c21_v_per_pin7_v"]))
        self.assertGreater(abs(one_driver["pre_c21_v_per_pin7_v"]),
                           abs(two_drivers["pre_c21_v_per_pin7_v"]))
        self.assertAlmostEqual(abs(two_drivers["j7_tip_v_per_pin7_v"]),
                               0.0667312360095879, delta=1e-6)

    def test_reject_nonfinite_frequency_and_nonphysical_load(self):
        for invalid in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                conditional_headphone_amp_ac(
                    **self.params(), frequency_hz=invalid)
        with self.assertRaises(ValueError):
            conditional_headphone_amp_ac(
                **self.params(), frequency_hz=100, tip_load_ohm=0)


if __name__ == "__main__":
    unittest.main()
