"""Charge conservation, equilibrium and local AC limit of 17-BJT step."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_vca1_active_small_signal_reference import active_loaded_matrices
from filter_vca1_active_transient_reference import initial_active_state, nonlinear_active_step


class FilterVca1ActiveTransientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca1_active_small_signal_reference import FilterVca1ActiveSmallSignalTest
        FilterVca1ActiveSmallSignalTest.setUpClass()
        cls.ladder = FilterVca1ActiveSmallSignalTest.ladder
        cls.recovery = FilterVca1ActiveSmallSignalTest.recovery
        cls.vca = FilterVca1ActiveSmallSignalTest().vca(2)

    def step(self, bus, state=None):
        if state is None:
            state = initial_active_state(ladder_dc=self.ladder,
                                         recovery_dc=self.recovery,
                                         vca_dc=self.vca)
        return state, nonlinear_active_step(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            vca_dc=self.vca, previous_node_v=state["node_v"],
            previous_c10_capacitor_v=state["c10_capacitor_v"],
            previous_bus_v=state["bus_v"], bus_v=bus,
            dt_s=1/48000, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)

    def test_equilibrium_and_both_polarities_conserve_charge(self):
        before, rest = self.step(0)
        self.assertEqual(rest["iterations"], 0)
        self.assertEqual(rest["node_v"], before["node_v"])
        for bus in (-0.1, 0.1):
            with self.subTest(bus=bus):
                previous, out = self.step(bus)
                self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
                self.assertAlmostEqual(out["r2_current_a"], out["c6_current_a"],
                                       delta=1e-11)
                old, new = previous["node_v"], out["node_v"]
                expected = (220e-6 * (new[4] - old[4])
                            + 10e-6 * (new[6] - old[6] - bus)
                            + 100e-6 * (new[23] - old[23])
                            + 220e-6 * (new[26] - old[26]))
                self.assertAlmostEqual(sum(out["charge_change_c"]),
                                       expected, delta=1e-15)

    def test_small_step_matches_33_node_backward_euler_limit(self):
        previous, out = self.step(1e-5)
        g, c, bus_c = active_loaded_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery, vca_dc=self.vca)
        dt = 1/48000
        gc = 10e-6 / dt
        y = gc / (1 + gc * 500)
        matrix = [[g[i][j] - c[i][j] / dt for j in range(33)] for i in range(33)]
        for index in (7, 22):
            matrix[index][index] -= y
        matrix[7][22] += y
        matrix[22][7] += y
        rhs = [0.0] * 33
        rhs[6] = -bus_c * 1e-5 / dt
        linear = _solve_linear(matrix, rhs)
        for actual, predicted, dc in zip(out["node_v"], linear, previous["node_v"]):
            self.assertAlmostEqual(actual - dc, predicted,
                                   delta=max(1e-9, 0.015 * abs(predicted)))

    def test_short_nonzero_trace(self):
        state = initial_active_state(ladder_dc=self.ladder,
                                     recovery_dc=self.recovery, vca_dc=self.vca)
        outputs = []
        for sample in range(16):
            bus = 0.1 * math.sin(2 * math.pi * 220 * sample / 48000)
            _, out = self.step(bus, state)
            self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
            outputs.append(out["first_vca_differential_collector_v"])
            state = out
        self.assertGreater(max(outputs) - min(outputs), 1e-8)

    def test_invalid_state_rejected(self):
        state = initial_active_state(ladder_dc=self.ladder,
                                     recovery_dc=self.recovery, vca_dc=self.vca)
        with self.assertRaises(ValueError):
            nonlinear_active_step(
                ladder_dc=self.ladder, recovery_dc=self.recovery,
                vca_dc=self.vca, previous_node_v=state["node_v"][:-1],
                previous_c10_capacitor_v=state["c10_capacitor_v"],
                previous_bus_v=0, bus_v=0, dt_s=1/48000,
                r14_pin7_to_pin6_ohm=0,
                r73_bottom_side_to_wiper_ohm=500)


if __name__ == "__main__":
    unittest.main()
