"""Conditional class-AB bias, device currents and KCL of board-3 circuit 11."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_amp_active_dc_reference import (
    NODES, conditional_headphone_amp_dc, evaluate_headphone_amp_dc)
from output_diode_reference import diode_model_from_reference


class HeadphoneAmpActiveDcTest(unittest.TestCase):
    def parameters(self, forward_v=0.7, beta=160):
        return dict(transistor_is_a=1e-14, beta_forward=beta,
                    beta_reverse=5, temperature_k=300,
                    diode_model=diode_model_from_reference(
                        ideality=1.5, forward_voltage_at_100ma_v=forward_v,
                        temperature_k=300))

    def test_coupled_point_obeys_kcl_and_device_direction(self):
        result = conditional_headphone_amp_dc(**self.parameters())
        node = result["node_v"]
        parts = result["parts"]
        self.assertEqual(len(node), 11)
        self.assertLess(result["max_kcl_residual_a"], 1e-11)
        self.assertTrue(result["c19_c15_c21_dc_open"])
        self.assertGreater(node["Q16_EMITTER_DIODE_TOP"], node["Q16_BASE"])
        self.assertGreater(node["DIODE_MIDDLE"], node["Q16_EMITTER_DIODE_TOP"])
        self.assertGreater(node["DIODE_BOTTOM"], node["DIODE_MIDDLE"])
        self.assertGreater(parts["diode_anode_to_cathode_a"]["CR1"], 0)
        self.assertGreater(parts["diode_anode_to_cathode_a"]["CR2"], 0)
        self.assertGreater(parts["transistor_currents_npn_sign_a"]["Q16"]["collector_a"], 0)
        self.assertAlmostEqual(parts["resistor_currents_a"]["R33"],
                               parts["resistor_currents_a"]["R32"], delta=1e-11)
        self.assertAlmostEqual(node["Q16_BASE"], -7.7957119232373975,
                               delta=1e-6)

    def test_bias_scenario_grid_remains_solved_without_vintage_claim(self):
        output_nodes = []
        for forward_v in (0.65, 0.7, 0.75):
            for beta in (80, 160, 300):
                with self.subTest(forward_v=forward_v, beta=beta):
                    result = conditional_headphone_amp_dc(
                        **self.parameters(forward_v, beta))
                    self.assertLess(result["max_kcl_residual_a"], 1e-11)
                    output_nodes.append(result["node_v"]["AMP_OUTPUT_BEFORE_C21"])
        self.assertGreater(max(output_nodes)-min(output_nodes), 0.25)

    def test_temperature_and_node_domain_are_explicit(self):
        parameters = self.parameters()
        with self.assertRaises(ValueError):
            evaluate_headphone_amp_dc([0]*len(NODES),
                                      **(parameters | {"temperature_k": 301}))
        with self.assertRaises(ValueError):
            evaluate_headphone_amp_dc([0]*10, **parameters)
        with self.assertRaises(ValueError):
            conditional_headphone_amp_dc(**(parameters | {"beta_forward": 0}))


if __name__ == "__main__":
    unittest.main()
