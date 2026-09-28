"""Charge and four-cell asymptote checks for the conditional AC ladder core."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_ladder_small_signal_reference import _capacitances, small_signal_at_frequency


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class LadderSmallSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solutions = {
            candidate: conditional_ladder_ebers_moll_dc(
                cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
                beta29=100, beta30=100,
                upper_is_a={name: 1e-14 for name in UPPER},
                upper_beta={name: 100 for name in UPPER},
                reverse_beta={name: 5 for name in DEVICE_NODES},
                r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
            for candidate in (200, 200000)}

    def test_documentary_four_cells_and_input_capacitors(self):
        edges, c24, c27 = _capacitances()
        self.assertEqual(len(edges), 4)
        self.assertTrue(all(value == 68e-9 for _, _, value in edges))
        self.assertEqual(c24, 220e-6)
        self.assertEqual(c27, 10e-6)
        self.assertEqual({(left, right) for left, right, _ in edges},
                         {(8, 12), (9, 13), (10, 14), (11, 15)})

    def test_c27_blocks_dc_for_both_r61_scenarios(self):
        for candidate, dc in self.solutions.items():
            with self.subTest(r61=candidate):
                out = small_signal_at_frequency(dc_solution=dc, frequency_hz=0)
                self.assertEqual(out["top_differential_v_per_bus_v"], 0)
                self.assertEqual(out["input_admittance_s"], 0)
                self.assertEqual(out["max_linear_kcl_residual_a_per_bus_v"], 0)

    def test_frequency_kcl_and_interstage_charge_balance(self):
        for candidate, dc in self.solutions.items():
            with self.subTest(r61=candidate):
                out = small_signal_at_frequency(dc_solution=dc, frequency_hz=1000)
                self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
                nodes = out["node_v_per_bus_v"]
                for ref, left, right in (("C16", "L_Q29C_Q23E", "R_Q30C_Q24E"),
                                         ("C11", "L_Q23C_Q19E", "R_Q24C_Q20E"),
                                         ("C7", "L_Q19C_Q10E", "R_Q20C_Q11E"),
                                         ("C3", "L_Q10C_Q2E", "R_Q11C_Q3E")):
                    current = out["interstage_capacitor_currents_a_per_bus_v"][ref]
                    self.assertAlmostEqual(abs(current + 1j * 2 * math.pi * 1000
                                                * 68e-9 * (nodes[right] - nodes[left])),
                                           0, delta=1e-14)

    def test_high_frequency_top_differential_has_four_cell_asymptote(self):
        for candidate, dc in self.solutions.items():
            with self.subTest(r61=candidate):
                at10k = small_signal_at_frequency(dc_solution=dc, frequency_hz=10000)
                at100k = small_signal_at_frequency(dc_solution=dc, frequency_hz=100000)
                ratio = (at10k["top_differential_magnitude"]
                         / at100k["top_differential_magnitude"])
                self.assertGreater(ratio, 9000)
                self.assertLess(ratio, 11000)

    def test_invalid_frequency_rejected(self):
        dc = self.solutions[200]
        for frequency in (-1, math.nan, math.inf):
            with self.subTest(frequency=frequency), self.assertRaises(ValueError):
                small_signal_at_frequency(dc_solution=dc, frequency_hz=frequency)


if __name__ == "__main__":
    unittest.main()
