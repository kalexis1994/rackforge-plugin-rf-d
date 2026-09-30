import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from cutoff_j7_vectors import OUTPUT, generate_vectors, setup, oracle_step
from headphone_coupled_transient_reference import (
    HeadphoneStepConvergenceError, nonlinear_coupled_headphone_step)


class CutoffJ7Vectors(unittest.TestCase):
    def test_128_monolithic_steps_regenerate_and_tail_responds_to_controls(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen, generate_vectors())
        for case in frozen["cases"]:
            self.assertLess(case["initial_dc_kcl_residual_a"], 1e-11)
            self.assertTrue(all(len(row["node_v"]) == 66 for row in case["rows"]))
            self.assertLess(max(row["max_kcl_residual_a"] for row in case["rows"]), 1e-10)
            currents = [row["tail_current_a"] for row in case["rows"]]
            self.assertGreater(max(currents)-min(currents), 1e-6)
            for row in case["rows"]:
                self.assertEqual(row["c18_v"], row["node_v"][62])
                self.assertAlmostEqual(row["tail_current_a"],
                    (row["node_v"][5]-row["node_v"][65])/680, places=15)

    def test_failed_monolithic_step_preserves_every_history(self):
        values = setup()
        ladder, recovery, output, headphone, controls, state, _ = values
        previous = copy.deepcopy(state)
        with self.assertRaises(HeadphoneStepConvergenceError):
            nonlinear_coupled_headphone_step(
                ladder_dc=ladder, recovery_dc=recovery, cascaded_output_dc=output,
                previous_state=state, bus_v=0.02, dt_s=1/48000,
                r14_pin7_to_pin6_ohm=0, r73_bottom_side_to_wiper_ohm=500,
                r20_wiper_to_ground_ohm=2500, hi_load_ohm=10000, lo_load_ohm=100000,
                r21_wiper_to_ground_ohm=2000, tip_load_ohm=32, ring_load_ohm=32,
                jacobian_method="finite_difference", cutoff_inputs=controls,
                newton_max_iterations=1, **headphone)
        self.assertEqual(state, previous)
        invalid = copy.deepcopy(state)
        invalid["c18_v"] = float("nan")
        with self.assertRaises(ValueError):
            oracle_step(values, invalid, controls["panel"], 0.1, 0, 0)


if __name__ == "__main__":
    unittest.main()
