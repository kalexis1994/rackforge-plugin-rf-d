"""Discrete charge balance, scaling, and AC/time consistency tests."""

import cmath
import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_ladder_linear_transient_reference import linear_step
from filter_ladder_small_signal_reference import small_signal_at_frequency


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class LadderLinearTransientTests(unittest.TestCase):
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

    def test_quiet_boundary_stays_at_operating_point(self):
        for candidate, dc in self.solutions.items():
            with self.subTest(r61=candidate):
                out = linear_step(dc_solution=dc, dt_s=1/48000,
                                  previous_node_delta_v=(0,) * 16,
                                  previous_bus_delta_v=0, bus_delta_v=0)
                self.assertEqual(out["node_delta_v"], (0,) * 16)
                self.assertEqual(out["board_input_current_delta_a"], 0)

    def test_small_step_is_linear_and_charge_balanced(self):
        dc = self.solutions[200]
        args = dict(dc_solution=dc, dt_s=1/48000,
                    previous_node_delta_v=(0,) * 16,
                    previous_bus_delta_v=0)
        one = linear_step(**args, bus_delta_v=0.001)
        two = linear_step(**args, bus_delta_v=0.002)
        self.assertLess(one["max_discrete_kcl_residual_a"], 1e-11)
        for v_one, v_two in zip(one["node_delta_v"], two["node_delta_v"]):
            self.assertAlmostEqual(v_two, 2 * v_one, delta=1e-12)
        self.assertAlmostEqual(two["board_input_current_delta_a"],
                               2 * one["board_input_current_delta_a"], delta=1e-12)

    def test_sinusoid_matches_small_signal_magnitude_with_be_error(self):
        sample_rate = 4800
        sample_count = 480  # ten cycles at 100 Hz
        for candidate, dc in self.solutions.items():
            with self.subTest(r61=candidate):
                previous = (0.0,) * 16
                old_bus = 0.0
                last_cycle = []
                for index in range(sample_count):
                    bus = 0.001 * math.sin(2 * math.pi * 100 * (index + 1)
                                           / sample_rate)
                    out = linear_step(dc_solution=dc, dt_s=1/sample_rate,
                                      previous_node_delta_v=previous,
                                      previous_bus_delta_v=old_bus,
                                      bus_delta_v=bus)
                    previous, old_bus = out["node_delta_v"], bus
                    self.assertLess(out["max_discrete_kcl_residual_a"], 1e-11)
                    if index >= sample_count - 48:
                        last_cycle.append(out["top_differential_delta_v"])
                coefficient = (2 / 48 * sum(value * cmath.exp(-1j * 2 * math.pi * index / 48)
                                             for index, value in enumerate(last_cycle)))
                measured = abs(coefficient) / 0.001
                analytical = small_signal_at_frequency(dc_solution=dc, frequency_hz=100)[
                    "top_differential_magnitude"]
                # Backward Euler at only 48 samples/cycle damps the response.
                self.assertGreater(measured / analytical, 0.85)
                self.assertLess(measured / analytical, 1.01)

    def test_invalid_step_boundaries_rejected(self):
        dc = self.solutions[200]
        common = dict(dc_solution=dc, dt_s=1/48000,
                      previous_node_delta_v=(0,) * 16,
                      previous_bus_delta_v=0, bus_delta_v=0)
        for change in (dict(dt_s=0), dict(dt_s=math.nan),
                       dict(previous_node_delta_v=(0,) * 15),
                       dict(bus_delta_v=math.inf)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                linear_step(**(common | change))


if __name__ == "__main__":
    unittest.main()
