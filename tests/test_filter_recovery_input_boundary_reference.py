"""Two documented output-coupling branches and their ladder loading."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_ladder_small_signal_reference import small_signal_at_frequency
from filter_recovery_input_boundary_reference import loaded_matrices, loaded_small_signal_at_frequency


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class RecoveryInputBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solutions = {candidate: conditional_ladder_ebers_moll_dc(
            cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
            for candidate in (200, 200000)}

    def test_two_capacitor_edges_and_shunts_are_stamped(self):
        g, c, c27 = loaded_matrices(self.solutions[200])
        self.assertEqual(len(g), 18)
        self.assertEqual(len(c), 18)
        self.assertAlmostEqual(c[11][16], -0.22e-6)
        self.assertAlmostEqual(c[15][17], -0.22e-6)
        self.assertAlmostEqual(c[16][11], c[11][16])
        self.assertAlmostEqual(c[17][15], c[15][17])
        self.assertAlmostEqual(g[16][16], -1/47000)
        self.assertAlmostEqual(g[17][17], -1/47000)
        self.assertEqual(c27, 10e-6)

    def test_zero_frequency_is_blocked_and_ac_kcl_closes(self):
        for candidate, dc in self.solutions.items():
            with self.subTest(r61=candidate):
                zero = loaded_small_signal_at_frequency(dc_solution=dc, frequency_hz=0)
                self.assertEqual(zero["recovery_base_differential_v_per_bus_v"], 0)
                for frequency in (100, 1000, 10000):
                    out = loaded_small_signal_at_frequency(
                        dc_solution=dc, frequency_hz=frequency)
                    self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"], 1e-11)

    def test_documented_rc_branch_and_loading_change_core_transfer(self):
        frequency = 100
        expected_ratio = (1j * 2 * math.pi * frequency * 0.22e-6 * 47000
                          / (1 + 1j * 2 * math.pi * frequency * 0.22e-6 * 47000))
        for candidate, dc in self.solutions.items():
            with self.subTest(r61=candidate):
                loaded = loaded_small_signal_at_frequency(
                    dc_solution=dc, frequency_hz=frequency)
                open_core = small_signal_at_frequency(dc_solution=dc,
                                                      frequency_hz=frequency)
                top = loaded["top_emitter_differential_v_per_bus_v"]
                base = loaded["recovery_base_differential_v_per_bus_v"]
                self.assertAlmostEqual(abs(base / top - expected_ratio), 0,
                                       delta=1e-10)
                self.assertLess(abs(top), abs(open_core["top_differential_v_per_bus_v"]))
                self.assertGreater(abs(top), 0)

    def test_invalid_frequency_rejected(self):
        for frequency in (-1, math.nan, math.inf):
            with self.subTest(frequency=frequency), self.assertRaises(ValueError):
                loaded_small_signal_at_frequency(dc_solution=self.solutions[200],
                                                 frequency_hz=frequency)


if __name__ == "__main__":
    unittest.main()
