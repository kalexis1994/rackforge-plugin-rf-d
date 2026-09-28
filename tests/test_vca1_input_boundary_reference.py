"""C6/R34/C15/R36 passive input charge and KCL checks."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vca1_input_boundary_reference import passive_vca1_input


class Vca1InputBoundaryTests(unittest.TestCase):
    def test_c6_blocks_dc_and_audio_nodes_close_kcl(self):
        zero = passive_vca1_input(frequency_hz=0)
        self.assertEqual(zero["q16_base_v_per_recovery_v"], 0)
        for frequency in (30, 100, 300, 1000, 10000):
            with self.subTest(frequency=frequency):
                out = passive_vca1_input(frequency_hz=frequency)
                self.assertLess(out["max_linear_kcl_residual_a_per_v"], 1e-12)
                self.assertGreater(abs(out["differential_base_v_per_recovery_v"]), 0)
                self.assertLessEqual(abs(out["differential_base_v_per_recovery_v"]), 1)

    def test_three_branch_currents_balance_q15_base(self):
        out = passive_vca1_input(frequency_hz=100)
        s = 2j * math.pi * 100
        left, right = (out["q16_base_v_per_recovery_v"],
                       out["q15_base_v_per_recovery_v"])
        from_r34 = (left - right) / 820
        to_ground = right / 510 + s * 220e-6 * right
        self.assertAlmostEqual(abs(from_r34 - to_ground), 0, delta=1e-12)
        from_c6 = s * 0.33e-6 * (1 - left)
        self.assertAlmostEqual(abs(from_c6 - from_r34), 0, delta=1e-12)

    def test_conditional_rolloff_and_invalid_frequency(self):
        low = passive_vca1_input(frequency_hz=30)
        high = passive_vca1_input(frequency_hz=10000)
        self.assertLess(abs(low["q16_base_v_per_recovery_v"]), 0.06)
        self.assertGreater(abs(high["q16_base_v_per_recovery_v"]), 0.99)
        for frequency in (-1, math.nan, math.inf):
            with self.subTest(frequency=frequency), self.assertRaises(ValueError):
                passive_vca1_input(frequency_hz=frequency)


if __name__ == "__main__":
    unittest.main()
