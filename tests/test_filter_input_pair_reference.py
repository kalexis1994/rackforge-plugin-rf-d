"""Physical invariants and numeric stability of the conditional pair law."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_input_pair_reference import ideal_current_split
from semiconductor_ideal import thermal_voltage_v


class FilterInputPairReferenceTests(unittest.TestCase):
    def test_equal_bases_split_tail_and_have_maximum_slope(self):
        tail = 0.001
        out = ideal_current_split(q29_base_v=0.1, q30_base_v=0.1,
                                  tail_current_a=tail, temperature_k=298.15)
        self.assertAlmostEqual(out["q29_collector_current_a"], tail / 2)
        self.assertAlmostEqual(out["q30_collector_current_a"], tail / 2)
        self.assertAlmostEqual(out["differential_transconductance_s"],
                               tail / (2 * thermal_voltage_v(298.15)))

    def test_swapping_bases_swaps_rails_and_preserves_tail(self):
        for difference in (0.001, 0.025, 0.1, 2):
            positive = ideal_current_split(q29_base_v=difference, q30_base_v=0,
                                           tail_current_a=0.0002, temperature_k=300)
            negative = ideal_current_split(q29_base_v=0, q30_base_v=difference,
                                           tail_current_a=0.0002, temperature_k=300)
            self.assertAlmostEqual(positive["q29_collector_current_a"],
                                   negative["q30_collector_current_a"])
            self.assertAlmostEqual(positive["q30_collector_current_a"],
                                   negative["q29_collector_current_a"])
            self.assertAlmostEqual(positive["q29_collector_current_a"]
                                   + positive["q30_collector_current_a"], 0.0002)
            self.assertGreaterEqual(positive["q30_collector_current_a"], 0)

    def test_reported_transconductance_matches_finite_difference(self):
        def differential(v):
            return ideal_current_split(q29_base_v=v, q30_base_v=0,
                                       tail_current_a=0.0004, temperature_k=310)

        center = differential(0.015)
        finite_difference = (differential(0.015001)["left_minus_right_current_a"]
                             - differential(0.014999)["left_minus_right_current_a"]) / 2e-6
        self.assertAlmostEqual(center["differential_transconductance_s"],
                               finite_difference, delta=1e-10)

    def test_invalid_boundaries_rejected(self):
        valid = dict(q29_base_v=0, q30_base_v=0, tail_current_a=1e-3,
                     temperature_k=298.15)
        for key, value in (("q29_base_v", math.nan), ("q30_base_v", math.inf),
                           ("tail_current_a", 0), ("tail_current_a", -1),
                           ("temperature_k", 0), ("temperature_k", math.inf)):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                ideal_current_split(**(valid | {key: value}))


if __name__ == "__main__":
    unittest.main()
