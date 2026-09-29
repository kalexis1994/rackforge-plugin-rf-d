"""C21/R56 high-pass and shared stereo pin 8, with imposed active drive."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_output_coupling_reference import (
    _output_parts, output_ac, output_backward_euler_step, output_corner_hz)


class HeadphoneOutputCouplingTest(unittest.TestCase):
    def test_values_and_stereo_load_topology(self):
        self.assertEqual(_output_parts(), (400e-6, 390))
        for tip, ring in ((None, None), (32, None), (32, 32), (16, 64)):
            with self.subTest(tip=tip, ring=ring):
                conductance = 1/390 + (0 if tip is None else 1/tip) + (0 if ring is None else 1/ring)
                self.assertAlmostEqual(output_corner_hz(tip_load_ohm=tip,
                                                        ring_load_ohm=ring),
                                       conductance/(2*math.pi*400e-6))
                at_corner = output_ac(frequency_hz=output_corner_hz(
                    tip_load_ohm=tip, ring_load_ohm=ring),
                    tip_load_ohm=tip, ring_load_ohm=ring)
                self.assertAlmostEqual(abs(at_corner["j7_tip_v_per_pre_c21_v"]),
                                       1/math.sqrt(2), delta=1e-12)
                self.assertEqual(at_corner["j7_tip_v_per_pre_c21_v"],
                                 at_corner["j7_ring_v_per_pre_c21_v"])
                self.assertLess(at_corner["max_linear_kcl_residual_a_per_pre_c21_v"], 1e-14)

    def test_dc_open_and_loading_changes_corner(self):
        self.assertEqual(output_ac(frequency_hz=0)["j7_tip_v_per_pre_c21_v"], 0)
        self.assertLess(output_corner_hz(),
                        output_corner_hz(tip_load_ohm=32))
        self.assertLess(output_corner_hz(tip_load_ohm=32),
                        output_corner_hz(tip_load_ohm=32, ring_load_ohm=32))

    def test_backward_euler_step_and_relaxation(self):
        dt = 1/48000
        cap_state = 0.0
        previous_jack = float("inf")
        for _ in range(5000):
            out = output_backward_euler_step(
                previous_capacitor_pre_minus_jack_v=cap_state,
                pre_c21_v=1, dt_s=dt,
                tip_load_ohm=32, ring_load_ohm=32)
            self.assertLess(out["max_charge_kcl_residual_a"], 1e-12)
            self.assertLess(out["j7_tip_v"], previous_jack)
            self.assertEqual(out["j7_tip_v"], out["j7_ring_v"])
            previous_jack = out["j7_tip_v"]
            cap_state = out["capacitor_pre_minus_jack_v"]
        self.assertLess(abs(out["j7_tip_v"]), 0.002)
        self.assertAlmostEqual(cap_state, 1, delta=0.002)

    def test_reject_invalid_domain(self):
        for invalid in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                output_ac(frequency_hz=invalid)
        for invalid in (0, -32, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                output_corner_hz(tip_load_ohm=invalid)
        with self.assertRaises(ValueError):
            output_backward_euler_step(previous_capacitor_pre_minus_jack_v=0,
                                       pre_c21_v=1, dt_s=0)


if __name__ == "__main__":
    unittest.main()
