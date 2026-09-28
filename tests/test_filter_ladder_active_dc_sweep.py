"""Grid completeness and headroom classification regressions."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_active_dc_sweep import sweep, summary


class LadderActiveSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = sweep()

    def test_cartesian_grid_and_documentary_candidates(self):
        self.assertEqual(self.data["cases_per_r61"], 36)
        self.assertEqual(set(self.data["results"]), {"200", "200000"})
        for cases in self.data["results"].values():
            self.assertEqual(len(cases), 36)
            self.assertEqual(len({(case["range_fraction"], case["beta"], case["is_a"])
                                  for case in cases}), 36)

    def test_outcomes_are_classified_and_margin_sign_matches_nominal_model(self):
        result = summary(self.data)["counts"]
        for candidate in ("200", "200000"):
            counts = result[candidate]
            self.assertEqual(sum(counts[label] for label in (
                "active_candidate", "headroom_or_bias_failure", "solver_domain_error")), 36)
        self.assertEqual(result["200"]["active_candidate"], 36)
        self.assertGreater(result["200"]["minimum_margin_v"], 0)
        self.assertEqual(result["200000"]["headroom_or_bias_failure"], 36)
        self.assertLess(result["200000"]["maximum_margin_v"], 0)


if __name__ == "__main__":
    unittest.main()
