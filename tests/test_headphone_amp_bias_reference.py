"""DC source, bias current and KCL for the unsolved Q16 input."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_amp_bias_reference import q16_base_bias


class HeadphoneAmpBiasTest(unittest.TestCase):
    def test_open_base_and_imposed_current_are_distinct_boundaries(self):
        open_base = q16_base_bias()
        self.assertAlmostEqual(open_base["base_v"], -10*24000/(6200+24000))
        self.assertTrue(open_base["c19_dc_open"])
        self.assertLess(open_base["kcl_residual_a"], 1e-15)
        self.assertAlmostEqual(open_base["thevenin_resistance_ohm"],
                               1/(1/6200+1/24000))
        for current in (-100e-6, 10e-6, 100e-6):
            with self.subTest(current=current):
                driven = q16_base_bias(base_current_leaving_node_a=current)
                self.assertLess(driven["kcl_residual_a"], 1e-15)
                self.assertAlmostEqual(
                    driven["base_v"]-open_base["base_v"],
                    -current*open_base["thevenin_resistance_ohm"], delta=1e-12)
        self.assertAlmostEqual(
            q16_base_bias(base_current_leaving_node_a=10e-6)["base_v"]
            - open_base["base_v"], -0.04927152317880795, delta=1e-12)

    def test_reject_nonfinite_current(self):
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(ValueError):
                q16_base_bias(base_current_leaving_node_a=bad)


if __name__ == "__main__":
    unittest.main()
