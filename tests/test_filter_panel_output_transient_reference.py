"""Exact panel reduction and nonlinear charge/current consistency."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_panel_output_transient_reference import (
    nonlinear_panel_output_step, panel_load_reduction)
from filter_vca_output_transient_reference import initial_output_state


class FilterPanelOutputTransientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca_output_small_signal_reference import FilterVcaOutputSmallSignalTest
        FilterVcaOutputSmallSignalTest.setUpClass()
        fixture = FilterVcaOutputSmallSignalTest()
        cls.ladder = fixture.ladder
        cls.recovery = fixture.recovery
        cls.output_dc = fixture.dc()

    def step(self, bus, state=None, hi_load=10000, lo_load=100000):
        if state is None:
            state = initial_output_state(
                ladder_dc=self.ladder, recovery_dc=self.recovery,
                cascaded_output_dc=self.output_dc)
        return nonlinear_panel_output_step(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            previous_node_v=state["node_v"],
            previous_c10_capacitor_v=state["c10_capacitor_v"],
            previous_bus_v=state["bus_v"], bus_v=bus,
            dt_s=1/48000, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500,
            r20_wiper_to_ground_ohm=2500,
            hi_load_ohm=hi_load, lo_load_ohm=lo_load,
            headphone_input_ohm=100000)

    def test_reduction_and_current_conservation(self):
        reduction = panel_load_reduction(
            r20_wiper_to_ground_ohm=2500,
            hi_load_ohm=10000, lo_load_ohm=100000)
        self.assertGreater(reduction["equivalent_main_load_ohm"], 0)
        self.assertLess(reduction["equivalent_main_load_ohm"], 10000)
        out = self.step(0.1)
        self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
        self.assertAlmostEqual(out["main_pin21_current_a"],
                               out["r20_upper_current_a"], delta=1e-12)
        self.assertAlmostEqual(out["r20_upper_current_a"],
                               out["r20_lower_current_a"]
                               + out["j4_hi_external_current_a"]
                               + out["r57_current_a"], delta=1e-12)
        self.assertAlmostEqual(out["r57_current_a"],
                               out["r58_current_a"]
                               + out["j5_lo_external_current_a"],
                               delta=1e-12)
        self.assertAlmostEqual(out["c2_current_a"],
                               out["main_pin21_current_a"]
                               + out["headphone_pin22_current_a"],
                               delta=1e-10)

    def test_trace_reaches_both_panel_jacks(self):
        state = initial_output_state(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc)
        hi, lo = [], []
        for sample in range(12):
            bus = 0.1*math.sin(2*math.pi*220*sample/48000)
            out = self.step(bus, state)
            hi.append(out["j4_hi_v"])
            lo.append(out["j5_lo_v"])
            state = out
        self.assertGreater(max(hi)-min(hi), 1e-8)
        self.assertGreater(max(lo)-min(lo), 1e-10)
        self.assertLess(max(abs(v) for v in lo),
                        max(abs(v) for v in hi))


if __name__ == "__main__":
    unittest.main()
