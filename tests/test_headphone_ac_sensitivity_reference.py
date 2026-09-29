"""Conditional AC envelope and load response over the declared 324 points."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_ac_sensitivity_reference import sensitivity_grid


class HeadphoneAcSensitivityTest(unittest.TestCase):
    def test_full_grid_is_solved_and_loaded_pairs_attenuate_j7(self):
        result = sensitivity_grid()
        self.assertEqual(result["scenario_count"], 324)
        self.assertEqual(len(result["envelopes"]), 6)
        self.assertLess(result["max_kcl_residual_a_per_bus_v"], 1e-11)
        rows = result["rows"]
        by_key = {
            (row["frequency_hz"], row["r21_wiper_to_ground_ohm"],
             row["board3_beta_forward"],
             row["diode_forward_voltage_at_100ma_v"],
             row["sw18_on"], row["tip_ring_ohm"]): row
            for row in rows}
        self.assertEqual(len(by_key), 324)
        for key in {entry[:-1] for entry in by_key}:
            self.assertGreater(by_key[key+(None,)]["abs_j7_v_per_bus_v"],
                               by_key[key+(32,)]["abs_j7_v_per_bus_v"])
        self.assertTrue(all(row["abs_hi_v_per_bus_v"] == 0
                            for row in rows if not row["sw18_on"]))
        loaded_100 = [row["abs_j7_v_per_bus_v"] for row in rows
                      if row["frequency_hz"] == 100
                      and row["tip_ring_ohm"] == 32]
        self.assertLess(min(loaded_100), 0.003)
        self.assertGreater(max(loaded_100), 0.5)


if __name__ == "__main__":
    unittest.main()
