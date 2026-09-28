"""Conservation and limiting cases for the conditional ladder DC spine."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_spine_dc_reference import conditional_spine_bottom_dc, conditional_spine_dc


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class LadderSpineDCTests(unittest.TestCase):
    def coupled(self, r61, withdrawals=(0, 0, 0, 0), beta=100):
        return conditional_spine_bottom_dc(
            cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
            beta29=beta, beta30=beta, r61_ohm=r61,
            r73_bottom_side_to_wiper_ohm=500,
            tap_withdrawals_a=withdrawals)

    def test_series_and_four_tap_kcls_with_signed_loads(self):
        withdrawals = (1e-4, -2e-5, 3e-5, 5e-5)
        out = conditional_spine_dc(bottom_v=1.5, tap_withdrawals_a=withdrawals)
        self.assertEqual(out["total_spine_ohm"], 820)
        self.assertEqual(out["tap_drop_weights_ohm"], (220, 370, 520, 670))
        self.assertAlmostEqual(out["bottom_injection_a"],
                               (10 - 1.5 - sum(w * i for w, i in zip(
                                   (220, 370, 520, 670), withdrawals))) / 820)
        self.assertAlmostEqual(out["bottom_voltage_residual_v"], 0, delta=1e-14)
        for residual in out["tap_kcl_residuals_a"]:
            self.assertAlmostEqual(residual, 0, delta=1e-17)
        self.assertEqual(len(out["resistor_currents_top_to_bottom_a"]), 5)

    def test_unloaded_spine_has_ohms_law_current(self):
        out = conditional_spine_dc(bottom_v=2, tap_withdrawals_a=(0, 0, 0, 0))
        self.assertAlmostEqual(out["bottom_injection_a"], 8 / 820)
        for current in out["resistor_currents_top_to_bottom_a"]:
            self.assertAlmostEqual(current, 8 / 820)

    def test_coupled_spine_closes_for_both_documentary_r61_values(self):
        for r61 in (200, 200000):
            with self.subTest(r61=r61):
                out = self.coupled(r61, withdrawals=(1e-5, 2e-5, -1e-5, 3e-5))
                self.assertAlmostEqual(out["spine_lower_coupling_residual_a"], 0,
                                       delta=1e-17)
                self.assertAlmostEqual(out["base_current_sum_shift_residual_a"], 0,
                                       delta=1e-17)
                self.assertAlmostEqual(out["lower"]["bottom_kcl_residual_a"], 0,
                                       delta=1e-17)
                self.assertAlmostEqual(out["spine"]["bottom_voltage_residual_v"], 0,
                                       delta=1e-14)

    def test_infinite_beta_recovers_simple_rail_divider(self):
        for r61 in (200, 200000):
            with self.subTest(r61=r61):
                out = self.coupled(r61, beta=math.inf)
                self.assertAlmostEqual(out["bottom_injection_a"], 10 / (820 + r61))
                self.assertAlmostEqual(out["bottom_v"], 10 * r61 / (820 + r61))

    def test_positive_tap_load_reduces_injection_at_fixed_bottom(self):
        unloaded = conditional_spine_dc(bottom_v=1, tap_withdrawals_a=(0,) * 4)
        for index, weight in enumerate((220, 370, 520, 670)):
            withdrawals = [0.] * 4
            withdrawals[index] = 1e-4
            loaded = conditional_spine_dc(bottom_v=1,
                                          tap_withdrawals_a=tuple(withdrawals))
            self.assertAlmostEqual(unloaded["bottom_injection_a"]
                                   - loaded["bottom_injection_a"], weight * 1e-4 / 820)

    def test_rejects_invalid_boundaries(self):
        for kwargs in (dict(bottom_v=math.nan, tap_withdrawals_a=(0,) * 4),
                       dict(bottom_v=1, tap_withdrawals_a=(0,) * 3),
                       dict(bottom_v=1, tap_withdrawals_a=(0, 0, math.inf, 0))):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                conditional_spine_dc(**kwargs)


if __name__ == "__main__":
    unittest.main()
