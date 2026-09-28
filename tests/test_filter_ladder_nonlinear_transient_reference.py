"""Nonlinear charge balance and linear-limit regressions for the ladder."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import NODE_NAMES, DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_ladder_linear_transient_reference import linear_step
from filter_ladder_nonlinear_transient_reference import nonlinear_step


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class LadderNonlinearTransientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dc = {candidate: conditional_ladder_ebers_moll_dc(
            cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
            for candidate in (200, 200000)}

    def initial(self, candidate):
        return tuple(self.dc[candidate]["nodes_v"][name] for name in NODE_NAMES)

    def test_resting_dc_state_is_fixed_point(self):
        for candidate, dc in self.dc.items():
            with self.subTest(r61=candidate):
                initial = self.initial(candidate)
                out = nonlinear_step(dc_solution=dc, dt_s=1/48000,
                                     previous_node_v=initial,
                                     previous_bus_v=0, bus_v=0)
                self.assertEqual(out["iterations"], 0)
                self.assertLess(out["max_charge_kcl_residual_a"], 1e-11)
                for before, after in zip(initial, out["node_v"]):
                    self.assertEqual(before, after)

    def test_both_polarities_and_r61_candidates_conserve_charge(self):
        for candidate, dc in self.dc.items():
            for bus in (-0.1, 0.1):
                with self.subTest(r61=candidate, bus=bus):
                    initial = self.initial(candidate)
                    out = nonlinear_step(dc_solution=dc, dt_s=1/48000,
                                         previous_node_v=initial,
                                         previous_bus_v=0, bus_v=bus)
                    self.assertLess(out["max_charge_kcl_residual_a"], 1e-10)
                    self.assertGreater(out["iterations"], 0)
                    self.assertTrue(all(math.isfinite(value)
                                        for value in out["node_v"]))
                    # The four interstage capacitor charges cancel in the
                    # global sum; only C24 and the driven C27 remain.
                    expected = (220e-6 * (out["node_v"][4] - initial[4])
                                + 10e-6 * ((out["node_v"][6] - initial[6]) - bus))
                    self.assertAlmostEqual(sum(out["charge_change_c"].values()),
                                           expected, delta=1e-16)

    def test_small_step_follows_linear_reference_and_large_step_depends_on_amplitude(self):
        for candidate, dc in self.dc.items():
            with self.subTest(r61=candidate):
                initial = self.initial(candidate)
                results = {}
                for bus in (0.001, 0.1):
                    nonlinear_state, linear_state = initial, (0.0,) * 16
                    old_bus = 0.0
                    for _ in range(200):
                        nl = nonlinear_step(dc_solution=dc, dt_s=1/48000,
                                            previous_node_v=nonlinear_state,
                                            previous_bus_v=old_bus, bus_v=bus)
                        li = linear_step(dc_solution=dc, dt_s=1/48000,
                                         previous_node_delta_v=linear_state,
                                         previous_bus_delta_v=old_bus,
                                         bus_delta_v=bus)
                        nonlinear_state, linear_state = nl["node_v"], li["node_delta_v"]
                        old_bus = bus
                    nl_top = ((nonlinear_state[11] - nonlinear_state[15])
                              - (initial[11] - initial[15]))
                    li_top = linear_state[11] - linear_state[15]
                    results[bus] = (nl_top, li_top)
                    self.assertLess(nl["max_charge_kcl_residual_a"], 1e-10)
                small_nl, small_li = results[0.001]
                large_nl, large_li = results[0.1]
                self.assertAlmostEqual(small_nl / small_li, 1, delta=0.02)
                self.assertLess(abs(large_nl / large_li), 0.7)

    def test_invalid_step_boundaries_rejected(self):
        dc = self.dc[200]
        common = dict(dc_solution=dc, dt_s=1/48000,
                      previous_node_v=self.initial(200),
                      previous_bus_v=0, bus_v=0)
        for change in (dict(dt_s=0), dict(dt_s=math.nan),
                       dict(previous_node_v=(0,) * 15),
                       dict(bus_v=math.inf)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                nonlinear_step(**(common | change))


if __name__ == "__main__":
    unittest.main()
