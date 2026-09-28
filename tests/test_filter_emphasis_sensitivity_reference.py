"""Documented grid covers R61 ambiguity and R14/R73/C10 electrical ranges."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_emphasis_sensitivity_reference import sensitivity_grid


class EmphasisSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = sensitivity_grid()

    def test_full_grid_closes_and_keeps_scenario_identity(self):
        out = self.result
        self.assertEqual(out["scenario_count"], 162)
        self.assertEqual(len(out["rows"]), 162)
        self.assertEqual(len({(row["r61_ohm"], row["r73_left_ohm"],
                               row["frequency_hz"], row["r14_e_ohm"],
                               row["c10_farads"]) for row in out["rows"]}), 162)
        self.assertLess(out["maximum_kcl_residual_a_per_v"], 1e-11)
        self.assertFalse(out["parameter_distribution_assumed"])

    def test_r61_and_feedback_settings_change_100hz_transfer(self):
        summary = {row["r61_ohm"]: row for row in self.result["summaries"]
                   if row["frequency_hz"] == 100}
        self.assertGreater(summary[200]["maximum"]["tap_magnitude_v_per_v"], 4)
        self.assertLess(summary[200]["minimum"]["tap_magnitude_v_per_v"], 1.1)
        self.assertGreater(summary[200000]["maximum"]["tap_magnitude_v_per_v"], 1)
        self.assertLess(summary[200000]["minimum"]["tap_magnitude_v_per_v"], 0.75)


if __name__ == "__main__":
    unittest.main()
