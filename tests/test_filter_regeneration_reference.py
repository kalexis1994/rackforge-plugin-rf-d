import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_regeneration_reference import passive_return


class FilterRegenerationReferenceTest(unittest.TestCase):
    def test_dc_is_blocked_by_c10(self):
        for r14 in (0, 50000):
            for trim in (0, 1000):
                result = passive_return(frequency_hz=0, r14_pin7_to_pin6_ohm=r14,
                                        r73_bottom_side_to_wiper_ohm=trim)
                self.assertEqual(result["q30_base_per_recovery_tap"], 0j)

    def test_high_frequency_limit_and_trim_partition(self):
        for trim in (0, 250, 1000):
            out = passive_return(frequency_hz=1e9, r14_pin7_to_pin6_ohm=12000,
                                 r73_bottom_side_to_wiper_ohm=trim)
            expected = (330 + trim) / (12000 + 1000 + 330)
            self.assertAlmostEqual(out["high_frequency_gain"], expected)
            self.assertAlmostEqual(out["magnitude"], expected, delta=1e-8)
            self.assertAlmostEqual(out["conditional_corner_hz"],
                                   1 / (2 * math.pi * 10e-6 * 13330))

    def test_panel_resistance_reduces_feedback_and_moves_conditional_pole(self):
        open_panel = passive_return(frequency_hz=1000, r14_pin7_to_pin6_ohm=0,
                                    r73_bottom_side_to_wiper_ohm=500)
        attenuated = passive_return(frequency_hz=1000, r14_pin7_to_pin6_ohm=50000,
                                    r73_bottom_side_to_wiper_ohm=500)
        self.assertGreater(open_panel["magnitude"], attenuated["magnitude"])
        self.assertGreater(open_panel["conditional_corner_hz"], attenuated["conditional_corner_hz"])

    def test_invalid_electrical_positions_rejected(self):
        for r14, trim in ((-1, 500), (50001, 500), (0, -1), (0, 1001)):
            with self.assertRaises(ValueError):
                passive_return(frequency_hz=1000, r14_pin7_to_pin6_ohm=r14,
                               r73_bottom_side_to_wiper_ohm=trim)


if __name__ == "__main__":
    unittest.main()
