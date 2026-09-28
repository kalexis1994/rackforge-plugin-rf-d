"""Loaded 27-node transient charge, KCL and AC-limit regressions."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, _solve_linear, conditional_ladder_ebers_moll_dc
from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc
from filter_vca1_loaded_small_signal_reference import loaded_matrices
from filter_vca1_passive_transient_reference import initial_loaded_state, nonlinear_loaded_step


class Vca1PassiveTransientTests(unittest.TestCase):
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

    def step(self, r61, bus, *, method="analytic", **changes):
        ladder = self.ladders[r61]
        initial = initial_loaded_state(ladder_dc=ladder, recovery_dc=self.recovery)
        args = dict(ladder_dc=ladder, recovery_dc=self.recovery,
                    previous_node_v=initial["node_v"],
                    previous_c10_capacitor_v=initial["c10_capacitor_v"],
                    previous_bus_v=0, bus_v=bus, dt_s=1/48000,
                    r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500,
                    jacobian_method=method)
        return initial, nonlinear_loaded_step(**(args | changes))

    def test_fixed_point_and_both_polarities_conserve_c6_and_global_charge(self):
        for r61 in self.ladders:
            initial, rest = self.step(r61, 0)
            self.assertEqual(rest["node_v"], initial["node_v"])
            self.assertEqual(rest["iterations"], 0)
            for bus in (-0.1, 0.1):
                with self.subTest(r61=r61, bus=bus):
                    before, out = self.step(r61, bus)
                    self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
                    self.assertAlmostEqual(out["r2_current_a"], out["c6_current_a"],
                                           delta=1e-11)
                    old, new = before["node_v"], out["node_v"]
                    expected = (220e-6 * (new[4] - old[4])
                                + 10e-6 * (new[6] - old[6] - bus)
                                + 100e-6 * (new[23] - old[23])
                                + 220e-6 * (new[26] - old[26]))
                    self.assertAlmostEqual(sum(out["charge_change_c"]),
                                           expected, delta=1e-15)

    def test_small_step_matches_linear_backward_euler(self):
        ladder = self.ladders[200]
        before, out = self.step(200, 1e-5)
        g, c, c27 = loaded_matrices(ladder_dc=ladder, recovery_dc=self.recovery)
        dt = 1/48000
        gc = 10e-6 / dt
        y = gc / (1 + gc * 500)
        matrix = [[g[i][j] - c[i][j] / dt for j in range(27)] for i in range(27)]
        for index in (7, 22):
            matrix[index][index] -= y
        matrix[7][22] += y
        matrix[22][7] += y
        rhs = [0.0] * 27
        rhs[6] = -c27 * 1e-5 / dt
        predicted = _solve_linear(matrix, rhs)
        for actual, linear, dc in zip(out["node_v"], predicted, before["node_v"]):
            self.assertAlmostEqual(actual - dc, linear,
                                   delta=max(1e-10, 0.01 * abs(linear)))

    def test_analytic_and_finite_difference_traces_agree(self):
        for r61, ladder in self.ladders.items():
            initial = initial_loaded_state(ladder_dc=ladder, recovery_dc=self.recovery)
            states = {method: initial for method in ("analytic", "finite_difference")}
            for sample in range(32):
                bus = 0.05 * math.sin(2 * math.pi * 220 * sample / 48000)
                outputs = {}
                for method, state in states.items():
                    out = nonlinear_loaded_step(
                        ladder_dc=ladder, recovery_dc=self.recovery,
                        previous_node_v=state["node_v"],
                        previous_c10_capacitor_v=state["c10_capacitor_v"],
                        previous_bus_v=state["bus_v"], bus_v=bus,
                        dt_s=1/48000, r14_pin7_to_pin6_ohm=0,
                        r73_bottom_side_to_wiper_ohm=500,
                        jacobian_method=method)
                    states[method] = {"node_v": out["node_v"],
                                      "c10_capacitor_v": out["c10_capacitor_v"],
                                      "bus_v": bus}
                    outputs[method] = out
                self.assertLess(max(abs(a - b) for a, b in zip(
                    outputs["analytic"]["node_v"],
                    outputs["finite_difference"]["node_v"])), 1e-6)

    def test_invalid_state_and_settings_rejected(self):
        for change in (dict(dt_s=0), dict(bus_v=math.inf),
                       dict(previous_node_v=(0,) * 26),
                       dict(r73_bottom_side_to_wiper_ohm=501)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.step(200, 0, **change)


if __name__ == "__main__":
    unittest.main()
