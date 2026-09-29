"""Full declared panel grid, KCL, switch state and cross-loading effects."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from output_panel_sensitivity_reference import panel_sensitivity_grid


class OutputPanelSensitivityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grid = panel_sensitivity_grid()

    def test_complete_grid_and_conservation(self):
        grid = self.grid
        self.assertEqual(grid["scenario_count"], 54)
        self.assertFalse(grid["parameter_distribution_assumed"])
        keys = {(row["sw18_on"], row["r20_wiper_to_ground_ohm"],
                 row["r21_wiper_to_ground_ohm"],
                 row["headphone_wiper_load_ohm"])
                for row in grid["rows"]}
        self.assertEqual(len(keys), 54)
        self.assertLess(grid["max_dc_kcl_residual_a"], 1e-12)
        self.assertLess(grid["max_ac_kcl_residual_a_per_v"], 1e-11)
        off = [row for row in grid["rows"] if not row["sw18_on"]]
        self.assertTrue(all(row["hi_magnitude_v_per_bus_v"] == 0
                            and row["lo_magnitude_v_per_bus_v"] == 0
                            and row["r21_wiper_magnitude_v_per_bus_v"] > 0
                            for row in off))

    def test_both_cursors_affect_a_shared_c2_source(self):
        rows = self.grid["rows"]
        selected = [row for row in rows
                    if row["r21_wiper_to_ground_ohm"] == 2500
                    and row["headphone_wiper_load_ohm"] == 32000]
        on = sorted((r for r in selected if r["sw18_on"]),
                    key=lambda r: r["r20_wiper_to_ground_ohm"])
        off = sorted((r for r in selected if not r["sw18_on"]),
                     key=lambda r: r["r20_wiper_to_ground_ohm"])
        self.assertLess(on[0]["hi_magnitude_v_per_bus_v"],
                        on[1]["hi_magnitude_v_per_bus_v"])
        self.assertLess(on[1]["hi_magnitude_v_per_bus_v"],
                        on[2]["hi_magnitude_v_per_bus_v"])
        self.assertNotEqual(off[0]["r21_wiper_magnitude_v_per_bus_v"],
                            off[2]["r21_wiper_magnitude_v_per_bus_v"])
        self.assertNotEqual(on[0]["c2_right_magnitude_v_per_bus_v"],
                            on[2]["c2_right_magnitude_v_per_bus_v"])


if __name__ == "__main__":
    unittest.main()
