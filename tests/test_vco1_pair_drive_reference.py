"""Check the DC divider limits before coupling IC1 to transistor equations."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_pair_drive_reference import ideal_pair_base_delta_v, ideal_pair_base_gain  # noqa: E402


class PairDriveTests(unittest.TestCase):
    def test_endpoints_and_monotonic_wiper_position(self) -> None:
        low = ideal_pair_base_gain(0)
        mid = ideal_pair_base_gain(0.5)
        high = ideal_pair_base_gain(1)
        self.assertAlmostEqual(low, 1000 / 1133)
        self.assertAlmostEqual(high, 1100 / 1133)
        self.assertLess(low, mid)
        self.assertLess(mid, high)

    def test_keyboard_increment_stops_before_current_or_frequency(self) -> None:
        delta = ideal_pair_base_delta_v({"KEYBOARD": 1.0}, 0.5)
        self.assertAlmostEqual(delta, -(1000 / 51100) * (1050 / 1133))
        self.assertTrue(-0.020 < delta < -0.017)

    def test_invalid_wiper_position_is_rejected(self) -> None:
        for value in (-0.1, 1.1, math.nan, math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ideal_pair_base_gain(value)


if __name__ == "__main__":
    unittest.main()
