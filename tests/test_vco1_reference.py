"""Circuit relations and numerical invariants for the partial C1 reference."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_reference import IdealTimingCapacitor  # noqa: E402


class TimingCapacitorTests(unittest.TestCase):
    def test_manual_voltage_bounds_and_current_derived_frequency(self) -> None:
        osc = IdealTimingCapacitor()
        current = 17.6e-6  # inferred from C=10 nF and 4 V swing at 440 Hz
        self.assertAlmostEqual(osc.frequency_hz(current), 440.0)
        at_start = osc.snapshot()
        self.assertEqual((at_start.capacitor_v, at_start.q3_nominal_v), (0.0, 4.0))
        half = osc.advance(1.0 / (2.0 * 440.0), current)
        self.assertEqual(half.resets, 0)
        self.assertAlmostEqual(half.capacitor_v, -2.0)
        self.assertAlmostEqual(half.q3_nominal_v, 0.0)
        after = osc.advance(1.0 / (2.0 * 440.0), current)
        self.assertEqual(after.resets, 1)
        self.assertAlmostEqual(after.capacitor_v, 0.0)

    def test_octave_current_and_long_step_wraps(self) -> None:
        osc = IdealTimingCapacitor()
        self.assertEqual([osc.frequency_hz(i * 1e-6) for i in (8.8, 17.6, 35.2)],
                         [220.0, 440.0, 880.0])
        result = osc.advance(0.1, 17.6e-6)
        self.assertEqual(result.resets, 44)
        self.assertEqual(osc.total_resets, 44)

    def test_documented_replacement_capacitor_tolerance_at_fixed_current(self) -> None:
        current = 17.6e-6
        low = IdealTimingCapacitor(10e-9 * 1.02).frequency_hz(current)
        high = IdealTimingCapacitor(10e-9 * 0.98).frequency_hz(current)
        self.assertAlmostEqual(low, 431.37254901960785)
        self.assertAlmostEqual(high, 448.9795918367347)

    def test_time_partition_and_paused_current(self) -> None:
        one = IdealTimingCapacitor()
        many = IdealTimingCapacitor()
        one.advance(0.109, 17.6e-6)
        for _ in range(109):
            many.advance(0.001, 17.6e-6)
        self.assertEqual(one.total_resets, many.total_resets)
        self.assertTrue(math.isclose(one.snapshot().capacitor_v,
                                     many.snapshot().capacitor_v, abs_tol=1e-11))
        paused = many.snapshot()
        many.advance(5.0, 0.0)
        self.assertEqual(many.snapshot().capacitor_v, paused.capacitor_v)

    def test_invalid_physical_inputs_are_rejected(self) -> None:
        osc = IdealTimingCapacitor()
        for invalid in (-1.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                osc.advance(0.01, invalid)
            with self.assertRaises(ValueError):
                osc.advance(invalid, 1e-6)
        with self.assertRaises(ValueError):
            IdealTimingCapacitor(0.0)


if __name__ == "__main__":
    unittest.main()
