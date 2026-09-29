"""Charge, fixed point and AC-limit checks for 48-node nonlinear oracle."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_vca_output_small_signal_reference import loaded_output_matrices
from filter_vca_output_transient_reference import (initial_output_state,
                                                   nonlinear_output_step)


class FilterVcaOutputTransientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca_output_small_signal_reference import FilterVcaOutputSmallSignalTest
        FilterVcaOutputSmallSignalTest.setUpClass()
        fixture = FilterVcaOutputSmallSignalTest()
        cls.ladder = fixture.ladder
        cls.recovery = fixture.recovery
        cls.output_dc = fixture.dc()

    def step(self, bus, state=None, main_load=10000, headphone_load=100000):
        if state is None:
            state = initial_output_state(
                ladder_dc=self.ladder, recovery_dc=self.recovery,
                cascaded_output_dc=self.output_dc)
        return state, nonlinear_output_step(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            previous_node_v=state["node_v"],
            previous_c10_capacitor_v=state["c10_capacitor_v"],
            previous_bus_v=state["bus_v"], bus_v=bus,
            dt_s=1/48000, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500,
            main_load_ohm=main_load,
            headphone_input_ohm=headphone_load)

    def test_dc_fixed_point_and_charge_conservation(self):
        initial, rest = self.step(0)
        self.assertEqual(rest["iterations"], 0)
        self.assertEqual(rest["node_v"], initial["node_v"])
        for bus in (-0.1, 0.1):
            with self.subTest(bus=bus):
                before, out = self.step(bus)
                self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
                self.assertAlmostEqual(out["r2_current_a"],
                                       out["c6_current_a"], delta=1e-11)
                self.assertAlmostEqual(out["c2_current_a"],
                                       out["main_pin21_current_a"]
                                       + out["headphone_pin22_current_a"],
                                       delta=1e-10)
                self.assertTrue(all(math.isfinite(v) for v in out["node_v"]))

    def test_small_step_matches_linear_backward_euler(self):
        for main_load, headphone_load in ((10000, 100000), (100, 100)):
            with self.subTest(main_load=main_load):
                initial, out = self.step(
                    1e-5, main_load=main_load,
                    headphone_load=headphone_load)
                g, c, bus_c = loaded_output_matrices(
                    ladder_dc=self.ladder, recovery_dc=self.recovery,
                    cascaded_output_dc=self.output_dc,
                    main_load_ohm=main_load,
                    headphone_input_ohm=headphone_load)
                dt = 1/48000
                gc = 10e-6/dt
                y = gc/(1 + gc*500)
                matrix = [[g[i][j]-c[i][j]/dt for j in range(48)]
                          for i in range(48)]
                for index in (7, 22):
                    matrix[index][index] -= y
                matrix[7][22] += y
                matrix[22][7] += y
                rhs = [0.0]*48
                rhs[6] = -bus_c*1e-5/dt
                linear = _solve_linear(matrix, rhs)
                for actual, predicted, dc in zip(out["node_v"], linear,
                                                 initial["node_v"]):
                    self.assertAlmostEqual(actual-dc, predicted,
                                           delta=max(1e-9,
                                                     0.005*abs(predicted)))

    def test_short_trace_reaches_output_pin(self):
        state = initial_output_state(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc)
        outputs = []
        for sample in range(16):
            bus = 0.1*math.sin(2*math.pi*220*sample/48000)
            _, out = self.step(bus, state)
            self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
            outputs.append(out["main_pin21_v"])
            state = out
        self.assertGreater(max(outputs)-min(outputs), 1e-8)


if __name__ == "__main__":
    unittest.main()
