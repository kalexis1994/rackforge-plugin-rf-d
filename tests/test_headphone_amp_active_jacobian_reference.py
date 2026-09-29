"""Independent finite-difference audit of the exact board-3 DC tangent."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_amp_active_dc_reference import (
    NODES, conditional_headphone_amp_dc, evaluate_headphone_amp_dc,
    headphone_amp_dc_jacobian)
from output_diode_reference import diode_model_from_reference


class HeadphoneAmpActiveJacobianTest(unittest.TestCase):
    def test_all_entries_at_three_bias_points_and_offset_trials(self):
        step = 1e-5
        for forward_v, beta in ((0.65, 80), (0.7, 160), (0.75, 300)):
            parameters = dict(
                transistor_is_a=1e-14, beta_forward=beta,
                beta_reverse=5, temperature_k=300,
                diode_model=diode_model_from_reference(
                    ideality=1.5, forward_voltage_at_100ma_v=forward_v,
                    temperature_k=300))
            dc = conditional_headphone_amp_dc(**parameters)
            bias = [dc["node_v"][name] for name in NODES]
            for offset in (0.0, 0.001):
                with self.subTest(forward_v=forward_v, beta=beta,
                                  offset=offset):
                    x = [v+(offset if i % 3 == 0 else -offset/2)
                         for i, v in enumerate(bias)]
                    tangent = headphone_amp_dc_jacobian(x, **parameters)
                    self.assertEqual(len(tangent), len(NODES))
                    for column in range(len(NODES)):
                        plus, minus = x.copy(), x.copy()
                        plus[column] += step
                        minus[column] -= step
                        high, _ = evaluate_headphone_amp_dc(plus, **parameters)
                        low, _ = evaluate_headphone_amp_dc(minus, **parameters)
                        for row in range(len(NODES)):
                            finite = (high[row]-low[row])/(2*step)
                            self.assertTrue(math.isclose(
                                tangent[row][column], finite,
                                rel_tol=5e-7, abs_tol=2e-9),
                                (row, column, tangent[row][column], finite))

    def test_matches_residual_domain(self):
        parameters = dict(
            transistor_is_a=1e-14, beta_forward=160,
            beta_reverse=5, temperature_k=300,
            diode_model=diode_model_from_reference(
                ideality=1.5, forward_voltage_at_100ma_v=0.7,
                temperature_k=300))
        with self.assertRaises(ValueError):
            headphone_amp_dc_jacobian([0.0]*10, **parameters)
        with self.assertRaises(ValueError):
            headphone_amp_dc_jacobian([0.0]*len(NODES),
                                      **(parameters | {"temperature_k": 301}))


if __name__ == "__main__":
    unittest.main()
