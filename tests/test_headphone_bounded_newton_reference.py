"""Finite Newton budgets either close KCL or fail without changing state."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_bounded_newton_reference import bounded_grid
from headphone_coupled_transient_reference import (
    HeadphoneStepConvergenceError, initial_coupled_headphone_state,
    nonlinear_coupled_headphone_step)
from headphone_transient_stress_reference import _scenario, reference_dc


class HeadphoneBoundedNewtonTest(unittest.TestCase):
    def test_all_declared_grids_close_with_budget(self):
        result = bounded_grid()
        self.assertEqual(result["scenario_count"], 38)
        self.assertEqual(result["step_count"], 3136)
        self.assertLessEqual(result["max_newton_iterations"], 15)
        self.assertLess(result["max_halvings_used"], 16)
        self.assertLess(result["max_kcl_residual_a"], 1e-10)
        self.assertEqual(result["convergence"]["total_steps"], 672)
        for ratio in result["convergence"]["max_error_ratios"].values():
            self.assertGreater(ratio, 1.5)
        self.assertEqual(result["semiconductors"]["total_steps"], 1440)
        self.assertAlmostEqual(
            result["semiconductors"]["baseline_j7_rms_v"],
            0.0064834403251276046, delta=1e-6)

    def test_exhausted_budget_does_not_mutate_input_state(self):
        scenario = _scenario()
        base = reference_dc(scenario)
        state = initial_coupled_headphone_state(**base)
        original = copy.deepcopy(state)
        with self.assertRaises(HeadphoneStepConvergenceError) as caught:
            nonlinear_coupled_headphone_step(
                **base, previous_state=state,
                bus_v=1.0, dt_s=1/48000,
                r14_pin7_to_pin6_ohm=scenario["r14_pin7_to_pin6_ohm"],
                r73_bottom_side_to_wiper_ohm=scenario["r73_bottom_side_to_wiper_ohm"],
                r20_wiper_to_ground_ohm=scenario["r20_wiper_to_ground_ohm"],
                r21_wiper_to_ground_ohm=scenario["r21_wiper_to_ground_ohm"],
                hi_load_ohm=scenario["hi_load_ohm"],
                lo_load_ohm=scenario["lo_load_ohm"],
                tip_load_ohm=32, ring_load_ohm=32,
                newton_max_iterations=1)
        self.assertEqual(caught.exception.reason,
                         "Newton iteration budget exhausted")
        self.assertEqual(state, original)

    def test_invalid_budget_is_rejected(self):
        scenario = _scenario()
        base = reference_dc(scenario)
        state = initial_coupled_headphone_state(**base)
        panel = dict(
            r14_pin7_to_pin6_ohm=scenario["r14_pin7_to_pin6_ohm"],
            r73_bottom_side_to_wiper_ohm=scenario["r73_bottom_side_to_wiper_ohm"],
            r20_wiper_to_ground_ohm=scenario["r20_wiper_to_ground_ohm"],
            r21_wiper_to_ground_ohm=scenario["r21_wiper_to_ground_ohm"],
            hi_load_ohm=scenario["hi_load_ohm"],
            lo_load_ohm=scenario["lo_load_ohm"])
        for invalid in (0, 81, True, 1.5):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                nonlinear_coupled_headphone_step(
                    **base, **panel, previous_state=state,
                    bus_v=0, dt_s=1/48000,
                    newton_max_iterations=invalid)
        for invalid in (0, 33, False, 2.5):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                nonlinear_coupled_headphone_step(
                    **base, **panel, previous_state=state,
                    bus_v=0, dt_s=1/48000,
                    line_search_max_halvings=invalid)


if __name__ == "__main__":
    unittest.main()
