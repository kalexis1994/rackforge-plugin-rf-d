"""Charge conservation and linear limit of the coupled filter transient."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_full_nonlinear_transient_reference import initial_state, nonlinear_coupled_step
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, _solve_linear, conditional_ladder_ebers_moll_dc)
from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc
from filter_recovery_active_small_signal_reference import coupled_matrices


class FullNonlinearTransientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recovery = conditional_recovery_dc(
            is_a={name: 1e-14 for name in DEVICES},
            beta_forward={name: 100 for name in DEVICES},
            beta_reverse={name: 5 for name in DEVICES}, temperature_k=298.15)
        cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                        scale_active_ohm=250, contour_pin16_v=0),
                      range_fraction_from_ground=0.1,
                      is26_a=1e-14, is28_a=1e-14,
                      beta26=100, beta28=100, temperature_k=298.15)
        cls.ladders = {r61: conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)
            for r61 in (200, 200000)}

    def step(self, r61, bus, *, r14=0, **changes):
        ladder = self.ladders[r61]
        initial = initial_state(ladder_dc=ladder, recovery_dc=self.recovery)
        args = dict(ladder_dc=ladder, recovery_dc=self.recovery,
                    previous_node_v=initial["node_v"],
                    previous_c10_capacitor_v=initial["c10_capacitor_v"],
                    previous_bus_v=0, bus_v=bus, dt_s=1/48000,
                    r14_pin7_to_pin6_ohm=r14,
                    r73_bottom_side_to_wiper_ohm=500)
        return initial, nonlinear_coupled_step(**(args | changes))

    def test_dc_fixed_point_for_both_r61_scenarios(self):
        for candidate in self.ladders:
            with self.subTest(r61=candidate):
                initial, out = self.step(candidate, 0)
                self.assertEqual(out["node_v"], initial["node_v"])
                self.assertEqual(out["iterations"], 0)
                self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
                self.assertAlmostEqual(out["return_current_a"], 0, delta=1e-14)

    def test_excitation_conserves_charge_and_c10_current(self):
        for candidate in self.ladders:
            for bus in (-0.1, 0.1):
                with self.subTest(r61=candidate, bus=bus):
                    initial, out = self.step(candidate, bus)
                    self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
                    self.assertTrue(all(math.isfinite(v) for v in out["node_v"]))
                    self.assertAlmostEqual(out["return_current_a"],
                                           out["return_capacitor_current_a"], delta=1e-11)
                    after, before = out["node_v"], initial["node_v"]
                    expected = (220e-6 * (after[4] - before[4])
                                + 10e-6 * (after[6] - before[6] - bus)
                                + 100e-6 * (after[23] - before[23]))
                    self.assertAlmostEqual(sum(out["charge_change_c"].values()),
                                           expected, delta=1e-15)

    def test_small_excitation_matches_linear_backward_euler_network(self):
        ladder = self.ladders[200]
        initial, out = self.step(200, 1e-5, r14=25000)
        g, c, c27 = coupled_matrices(ladder, self.recovery)
        dt = 1/48000
        gc = 10e-6 / dt
        y = gc / (1 + gc * 25500)
        matrix = [[g[i][j] - c[i][j] / dt for j in range(24)] for i in range(24)]
        for i in (7, 22):
            matrix[i][i] -= y
        matrix[7][22] += y
        matrix[22][7] += y
        rhs = [0.0] * 24
        rhs[6] = -c27 * 1e-5 / dt
        linear = _solve_linear(matrix, rhs)
        for actual, predicted, base in zip(out["node_v"], linear, initial["node_v"]):
            self.assertAlmostEqual(actual - base, predicted,
                                   delta=max(1e-10, 0.01 * abs(predicted)))

    def test_multistep_response_changes_with_level(self):
        ladder = self.ladders[200]
        initial = initial_state(ladder_dc=ladder, recovery_dc=self.recovery)
        tap_changes = {}
        for bus in (0.001, 0.1):
            state = initial
            for _ in range(32):
                out = nonlinear_coupled_step(
                    ladder_dc=ladder, recovery_dc=self.recovery,
                    previous_node_v=state["node_v"],
                    previous_c10_capacitor_v=state["c10_capacitor_v"],
                    previous_bus_v=state["bus_v"], bus_v=bus,
                    dt_s=1/48000, r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500)
                state = {"node_v": out["node_v"],
                         "c10_capacitor_v": out["c10_capacitor_v"],
                         "bus_v": bus}
            self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
            tap_changes[bus] = out["node_v"][22] - initial["node_v"][22]
        self.assertLess(abs(tap_changes[0.1] / (100 * tap_changes[0.001])), 0.7)

    def test_invalid_step_and_mismatched_trimmer_rejected(self):
        for change in (dict(dt_s=0), dict(bus_v=math.inf),
                       dict(r14_pin7_to_pin6_ohm=-1),
                       dict(r73_bottom_side_to_wiper_ohm=501)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.step(200, 0, **change)


if __name__ == "__main__":
    unittest.main()
