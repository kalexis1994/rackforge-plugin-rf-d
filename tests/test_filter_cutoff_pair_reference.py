"""Load-line, current-ratio and headroom checks for imposed device data."""

import math
import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_cutoff_pair_reference import conditional_cutoff_current
from semiconductor_ideal import thermal_voltage_v


class FilterCutoffPairReferenceTests(unittest.TestCase):
    def test_graphs_keep_r60_between_tail_and_q28_collector(self):
        evidence = Path(__file__).resolve().parents[1] / "evidence"
        input_graph = json.loads((evidence / "filter_input_board4.json").read_text(encoding="utf-8"))
        pair_graph = json.loads((evidence / "filter_input_pair.json").read_text(encoding="utf-8"))
        cutoff_graph = json.loads((evidence / "filter_cutoff_q26_q28.json").read_text(encoding="utf-8"))
        self.assertEqual(input_graph["parts"]["R60"]["between"],
                         ["TAIL", "Q28 collector"])
        self.assertEqual(pair_graph["connections"]["R60"]["between"],
                         ["TAIL", "Q28_COLLECTOR"])
        self.assertEqual(pair_graph["connections"]["Q28"]["base"],
                         "SHARED_Q26_EMITTER")
        self.assertEqual(cutoff_graph["parts"]["R60"]["between"],
                         ["Q28_COLLECTOR", "TAIL"])
        self.assertEqual(cutoff_graph["parts"]["Q26"]["emitter"],
                         cutoff_graph["parts"]["Q28"]["base"])

    def scenario(self, **changes):
        values = dict(range_fraction_from_ground=0.1, q26_base_v=0,
                      is26_a=1e-14, is28_a=1e-14,
                      temperature_k=298.15, tail_v=2)
        return conditional_cutoff_current(**(values | changes))

    def test_loaded_range_wiper_and_kcl(self):
        out = self.scenario(range_fraction_from_ground=0.5)
        self.assertAlmostEqual(out["range_thevenin_v"], 5)
        self.assertAlmostEqual(out["range_thevenin_ohm"], 2500)
        self.assertAlmostEqual(out["source_total_ohm"], 70500)
        self.assertAlmostEqual(out["loadline_residual_a"], 0, delta=1e-14)
        self.assertGreater(out["range_thevenin_v"], out["shared_node_v"])

    def test_matched_ideal_devices_have_exponential_current_ratio(self):
        for base_v in (-0.025, 0, 0.025):
            out = self.scenario(q26_base_v=base_v)
            ratio = out["q28_collector_current_a_candidate_a"] / out["q26_collector_current_a"]
            self.assertAlmostEqual(ratio, math.exp(base_v / thermal_voltage_v(298.15)),
                                   delta=1e-10)
        mismatched = self.scenario(q26_base_v=0, is28_a=2e-14)
        self.assertAlmostEqual(mismatched["q28_collector_current_a_candidate_a"]
                               / mismatched["q26_collector_current_a"], 2)

    def test_range_trim_changes_absolute_candidate_but_not_pair_ratio(self):
        low = self.scenario(range_fraction_from_ground=0.1)
        high = self.scenario(range_fraction_from_ground=0.2)
        self.assertGreater(high["q28_collector_current_a_candidate_a"],
                           low["q28_collector_current_a_candidate_a"])
        for out in (low, high):
            self.assertAlmostEqual(out["q28_collector_current_a_candidate_a"],
                                   out["q26_collector_current_a"], delta=1e-14)

    def test_collector_headroom_is_explicit_boundary(self):
        good = self.scenario()
        low_tail = self.scenario(tail_v=0.1)
        self.assertTrue(good["q26_forward_active_candidate"])
        self.assertTrue(good["q28_forward_active_candidate"])
        self.assertFalse(low_tail["q28_forward_active_candidate"])
        self.assertAlmostEqual(good["q28_collector_current_a_candidate_a"],
                               low_tail["q28_collector_current_a_candidate_a"])

    def test_invalid_boundaries_rejected(self):
        for change in ({"range_fraction_from_ground": -0.1},
                       {"range_fraction_from_ground": 1.1},
                       {"is26_a": 0}, {"is28_a": -1e-14},
                       {"temperature_k": math.nan}, {"q26_base_v": math.inf}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.scenario(**change)


if __name__ == "__main__":
    unittest.main()
