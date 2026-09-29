"""Declared parameter grid and electrical conservation for output study."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from vca_output_sensitivity_reference import sensitivity_grid


class OutputSensitivityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grid = sensitivity_grid()

    def test_all_scenarios_close_and_respect_open_diode_domain(self):
        result = self.grid
        self.assertEqual(result["scenario_count"], 81)
        self.assertFalse(result["parameter_distribution_assumed"])
        self.assertLess(result["max_dc_kcl_residual_a"], 1e-12)
        self.assertLess(result["max_ac_kcl_residual_a_per_v"], 1e-11)
        self.assertTrue(all(0 <= row["q17_collector_dc_v"] <= 10
                            for row in result["rows"]))

    def test_balance_and_load_change_the_transfer(self):
        rows = self.grid["rows"]
        nominal = [r for r in rows if r["q17_is_ratio"] == 1
                   and r["q17_beta_forward"] == 100]
        low_load = next(r for r in nominal
                        if r["second_balance_left_ohm"] == 50
                        and r["main_load_ohm"] == 1000)
        high_load = next(r for r in nominal
                         if r["second_balance_left_ohm"] == 50
                         and r["main_load_ohm"] == 100000)
        self.assertGreater(high_load["main_pin21_magnitude_v_per_bus_v"],
                           low_load["main_pin21_magnitude_v_per_bus_v"])
        self.assertNotEqual(min(r["q17_collector_dc_v"] for r in nominal),
                            max(r["q17_collector_dc_v"] for r in nominal))


if __name__ == "__main__":
    unittest.main()
