"""Verify the constrained current reference and ideal pair ratio, not audio."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_ideal_pair_reference import (  # noqa: E402
    conditional_qb_collector_current_a,
    ideal_qa_current_and_frequency_ratio,
    thermal_voltage_v,
    unloaded_neg4_reference_v,
)


class IdealPairTests(unittest.TestCase):
    def test_ic3_reference_sets_qb_load_current_only_conditionally(self) -> None:
        self.assertAlmostEqual(conditional_qb_collector_current_a(), 4 / 39000)
        unloaded = unloaded_neg4_reference_v()
        self.assertAlmostEqual(unloaded, -10 * 3900 / (6200 + 3900))
        self.assertNotAlmostEqual(unloaded, -4)
        self.assertAlmostEqual(conditional_qb_collector_current_a(unloaded), -unloaded / 39000)

    def test_one_keyboard_volt_brackets_an_octave_at_25_c(self) -> None:
        low = ideal_qa_current_and_frequency_ratio({"KEYBOARD": 1}, 0)
        high = ideal_qa_current_and_frequency_ratio({"KEYBOARD": 1}, 1)
        self.assertAlmostEqual(low, math.exp((1000 / 51100) * (1000 / 1133) / thermal_voltage_v(298.15)))
        self.assertLess(low, 2)
        self.assertGreater(high, 2)
        self.assertAlmostEqual(ideal_qa_current_and_frequency_ratio({"KEYBOARD": 0}, 0.5), 1)

    def test_reverse_keyboard_step_has_reciprocal_ratio(self) -> None:
        up = ideal_qa_current_and_frequency_ratio({"KEYBOARD": 1}, 0.5)
        down = ideal_qa_current_and_frequency_ratio({"KEYBOARD": -1}, 0.5)
        self.assertAlmostEqual(up * down, 1)

    def test_invalid_temperature_is_rejected(self) -> None:
        for value in (0, -1, math.nan, math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                thermal_voltage_v(value)


if __name__ == "__main__":
    unittest.main()
