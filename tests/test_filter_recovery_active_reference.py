"""DC current conservation and AC loading of Q5-Q8 recovery."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc
from filter_recovery_active_small_signal_reference import coupled_matrices, active_recovery_small_signal
from filter_recovery_input_boundary_reference import loaded_small_signal_at_frequency


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class RecoveryActiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recovery = conditional_recovery_dc(
            is_a={name: 1e-14 for name in DEVICES},
            beta_forward={name: 100 for name in DEVICES},
            beta_reverse={name: 5 for name in DEVICES}, temperature_k=298.15)
        cls.ladders = {candidate: conditional_ladder_ebers_moll_dc(
            cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
            for candidate in (200, 200000)}

    def test_recovery_dc_closes_eight_kcls_and_device_currents(self):
        out = self.recovery
        self.assertLess(out["max_kcl_residual_a"], 1e-10)
        self.assertEqual(len(out["nodes_v"]), 8)
        for device in out["devices"].values():
            self.assertAlmostEqual(device["emitter_a"],
                                   device["collector_a"] + device["base_a"],
                                   delta=1e-14)
        v = out["nodes_v"]
        current_r6 = (10 - v["RECOVER_R6_R7"]) / 47
        current_r7 = (v["RECOVER_R6_R7"] - v["RECOVER_R7_R3"]) / 180
        current_r3 = (v["RECOVER_R7_R3"] - v["RECOVER_COLLECTOR"]) / 1000
        self.assertAlmostEqual(current_r6, current_r7, delta=1e-10)
        self.assertAlmostEqual(current_r7, current_r3, delta=1e-10)
        self.assertAlmostEqual(current_r3,
                               out["devices"]["Q8"]["collector_a"]
                               + out["devices"]["Q7"]["collector_a"], delta=1e-10)

    def test_active_ac_coupling_stamps_two_caps_and_c9(self):
        g, c, c27 = coupled_matrices(self.ladders[200], self.recovery)
        self.assertEqual(len(g), 24)
        self.assertAlmostEqual(c[11][16], -0.22e-6)
        self.assertAlmostEqual(c[15][17], -0.22e-6)
        self.assertAlmostEqual(c[23][23], 100e-6)
        self.assertEqual(c27, 10e-6)

    def test_ac_pickoff_is_blocked_at_dc_and_has_active_recovery_gain(self):
        for candidate, ladder in self.ladders.items():
            with self.subTest(r61=candidate):
                zero = active_recovery_small_signal(
                    ladder_dc=ladder, recovery_dc=self.recovery, frequency_hz=0)
                self.assertEqual(zero["emphasis_pickoff_r7_r3_v_per_bus_v"], 0)
                ac = active_recovery_small_signal(
                    ladder_dc=ladder, recovery_dc=self.recovery, frequency_hz=100)
                passive = loaded_small_signal_at_frequency(
                    dc_solution=ladder, frequency_hz=100)
                self.assertLess(ac["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
                self.assertGreater(abs(ac["emphasis_pickoff_r7_r3_v_per_bus_v"]),
                                   abs(passive["recovery_base_differential_v_per_bus_v"]))
                self.assertNotAlmostEqual(
                    abs(ac["ladder_top_differential_v_per_bus_v"]),
                    abs(passive["top_emitter_differential_v_per_bus_v"]),
                    delta=1e-3)

    def test_invalid_device_parameters_and_frequency_rejected(self):
        args = dict(is_a={name: 1e-14 for name in DEVICES},
                    beta_forward={name: 100 for name in DEVICES},
                    beta_reverse={name: 5 for name in DEVICES},
                    temperature_k=298.15)
        for change in (dict(is_a={name: 0 if name == "Q8" else 1e-14
                                    for name in DEVICES}),
                       dict(beta_reverse={name: math.nan if name == "Q5" else 5
                                          for name in DEVICES})):
            with self.subTest(change=change), self.assertRaises(ValueError):
                conditional_recovery_dc(**(args | change))
        with self.assertRaises(ValueError):
            active_recovery_small_signal(ladder_dc=self.ladders[200],
                                         recovery_dc=self.recovery,
                                         frequency_hz=math.inf)


if __name__ == "__main__":
    unittest.main()
