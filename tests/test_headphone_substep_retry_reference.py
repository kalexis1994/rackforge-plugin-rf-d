"""Retry semantics, failure atomicity and changed time discretization."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_coupled_transient_reference import (
    HeadphoneStepConvergenceError, initial_coupled_headphone_state,
    nonlinear_coupled_headphone_step)
from headphone_substep_retry_reference import retry_headphone_step, retry_example
from headphone_transient_stress_reference import _scenario, reference_dc


class HeadphoneSubstepRetryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scenario = _scenario()
        cls.base = reference_dc(scenario)
        cls.panel = dict(
            r14_pin7_to_pin6_ohm=scenario["r14_pin7_to_pin6_ohm"],
            r73_bottom_side_to_wiper_ohm=scenario["r73_bottom_side_to_wiper_ohm"],
            r20_wiper_to_ground_ohm=scenario["r20_wiper_to_ground_ohm"],
            r21_wiper_to_ground_ohm=scenario["r21_wiper_to_ground_ohm"],
            hi_load_ohm=scenario["hi_load_ohm"],
            lo_load_ohm=scenario["lo_load_ohm"],
            tip_load_ohm=32, ring_load_ohm=32)

    def test_full_failure_and_two_manual_halves(self):
        prior = initial_coupled_headphone_state(**self.base)
        original = copy.deepcopy(prior)
        budget = dict(newton_max_iterations=10,
                      line_search_max_halvings=4)
        with self.assertRaises(HeadphoneStepConvergenceError):
            nonlinear_coupled_headphone_step(
                **self.base, **self.panel, **budget,
                previous_state=prior, bus_v=-3, dt_s=1/480)
        retried = retry_headphone_step(
            **self.base, **self.panel, **budget,
            previous_state=prior, bus_v=-3, dt_s=1/480,
            max_subdivision_depth=1)
        first = nonlinear_coupled_headphone_step(
            **self.base, **self.panel, **budget,
            previous_state=prior, bus_v=-3, dt_s=1/960)
        second = nonlinear_coupled_headphone_step(
            **self.base, **self.panel, **budget,
            previous_state=first, bus_v=-3, dt_s=1/960)
        self.assertEqual(retried["node_v"], second["node_v"])
        self.assertEqual(retried["solver_attempt_count"], 3)
        self.assertEqual(retried["accepted_substeps"], 2)
        self.assertEqual(retried["subdivision_depth_used"], 1)
        self.assertLess(retried["max_charge_kcl_residual_a"], 1e-10)
        self.assertEqual(prior, original)
        full = nonlinear_coupled_headphone_step(
            **self.base, **self.panel, previous_state=prior,
            bus_v=-3, dt_s=1/480)
        self.assertGreater(abs(retried["j7_tip_v"]-full["j7_tip_v"]), 1e-4)

    def test_no_retry_and_exhaustion_remain_explicit(self):
        prior = initial_coupled_headphone_state(**self.base)
        original = copy.deepcopy(prior)
        easy = retry_headphone_step(
            **self.base, **self.panel, previous_state=prior,
            bus_v=0, dt_s=1/48000)
        self.assertEqual(easy["solver_attempt_count"], 1)
        self.assertEqual(easy["accepted_substeps"], 1)
        self.assertEqual(easy["subdivision_depth_used"], 0)
        with self.assertRaises(HeadphoneStepConvergenceError):
            retry_headphone_step(
                **self.base, **self.panel, previous_state=prior,
                bus_v=-3, dt_s=1/480, max_subdivision_depth=0,
                newton_max_iterations=10, line_search_max_halvings=4)
        self.assertEqual(prior, original)
        for depth in (-1, 5, True, 1.5):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                retry_headphone_step(
                    **self.base, **self.panel, previous_state=prior,
                    bus_v=0, dt_s=1/48000,
                    max_subdivision_depth=depth)

    def test_evidence_example(self):
        example = retry_example()
        self.assertEqual(example["retry_attempt_count"], 3)
        self.assertEqual(example["accepted_substeps"], 2)
        self.assertLess(example["retry_max_kcl_residual_a"], 1e-10)
        self.assertGreater(abs(example["j7_difference_due_to_discretization_v"]),
                           1e-4)


if __name__ == "__main__":
    unittest.main()
