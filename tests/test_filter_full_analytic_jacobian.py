"""Independent derivative and transient comparisons for the 24-node Jacobian."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_full_analytic_jacobian import analytic_dc_jacobian
from filter_full_nonlinear_transient_reference import initial_state, nonlinear_coupled_step
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, conditional_ladder_ebers_moll_dc, evaluate_nodal_kcl)
from filter_recovery_active_dc_reference import (
    DEVICES, _evaluate as recovery_kcl, conditional_recovery_dc)


class AnalyticJacobianTests(unittest.TestCase):
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

    def test_analytic_matches_central_difference_of_both_kcl_blocks(self):
        recovery = self.recovery
        for r61, ladder in self.ladders.items():
            for forward_bc in (False, True):
                with self.subTest(r61=r61, q8_base_collector_forward=forward_bc):
                    x = list(initial_state(ladder_dc=ladder, recovery_dc=recovery)["node_v"])
                    if forward_bc:
                        x[21] = -0.25  # exercises Q8 reverse junction derivative
                    self._compare_dc_derivatives(x, ladder, recovery)

    def _compare_dc_derivatives(self, x, ladder, recovery):
        lp, rp = ladder["network_parameters"], recovery["network_parameters"]
        exact = analytic_dc_jacobian(
            node_v=x, ladder_parameters=lp, recovery_parameters=rp)
        def residual(voltage):
            left, _ = evaluate_nodal_kcl(voltage[:16], **lp)
            right, _ = recovery_kcl(voltage[16:], **rp)
            return left + right
        h = 1e-6
        for column in range(24):
            high, low = x.copy(), x.copy()
            high[column] += h
            low[column] -= h
            plus, minus = residual(high), residual(low)
            for row in range(24):
                numeric = (plus[row] - minus[row]) / (2 * h)
                self.assertAlmostEqual(exact[row][column], numeric,
                                       delta=max(1e-9, 2e-5 * abs(numeric)))

    def test_multistep_analytic_and_finite_difference_agree(self):
        for r61, ladder in self.ladders.items():
            for r14 in (0, 50000):
                with self.subTest(r61=r61, r14=r14):
                    start = initial_state(ladder_dc=ladder, recovery_dc=self.recovery)
                    states = {method: start for method in ("analytic", "finite_difference")}
                    for sample in range(48):
                        bus = 0.05 * math.sin(2 * math.pi * 220 * sample / 48000)
                        outputs = {}
                        for method, state in states.items():
                            out = nonlinear_coupled_step(
                                ladder_dc=ladder, recovery_dc=self.recovery,
                                previous_node_v=state["node_v"],
                                previous_c10_capacitor_v=state["c10_capacitor_v"],
                                previous_bus_v=state["bus_v"], bus_v=bus,
                                dt_s=1/48000, r14_pin7_to_pin6_ohm=r14,
                                r73_bottom_side_to_wiper_ohm=500,
                                jacobian_method=method)
                            states[method] = {"node_v": out["node_v"],
                                              "c10_capacitor_v": out["c10_capacitor_v"],
                                              "bus_v": bus}
                            outputs[method] = out
                        self.assertLess(max(abs(a - b) for a, b in zip(
                            outputs["analytic"]["node_v"],
                            outputs["finite_difference"]["node_v"])), 1e-6)
                        self.assertLess(outputs["analytic"]["max_charge_kcl_residual_a"],
                                        1e-10)

    def test_invalid_jacobian_method_rejected(self):
        ladder = self.ladders[200]
        state = initial_state(ladder_dc=ladder, recovery_dc=self.recovery)
        with self.assertRaises(ValueError):
            nonlinear_coupled_step(
                ladder_dc=ladder, recovery_dc=self.recovery,
                previous_node_v=state["node_v"],
                previous_c10_capacitor_v=state["c10_capacitor_v"],
                previous_bus_v=0, bus_v=0, dt_s=1/48000,
                r14_pin7_to_pin6_ohm=0,
                r73_bottom_side_to_wiper_ohm=500,
                jacobian_method="invented")


if __name__ == "__main__":
    unittest.main()
