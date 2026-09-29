"""Frozen vectors and rejection behavior for a future independent DSP port."""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from headphone_port_vectors import EVIDENCE, compare_candidate, generate_vectors


def candidate_from_reference(reference):
    return {"schema": "rf-d/headphone-port-candidate/v1",
            "cases": [{"id": case["id"],
                       "steps": [copy.deepcopy(step["expected"])
                                 for step in case["steps"]]}
                      for case in reference["cases"]]}


class HeadphonePortVectorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_frozen_vectors_match_oracle_and_names(self):
        regenerated = generate_vectors()
        self.assertEqual(len(regenerated["node_order"]), 62)
        self.assertEqual(len(set(regenerated["node_order"])), 62)
        self.assertEqual(len(regenerated["cases"]), 3)
        self.assertEqual(sum(len(case["steps"]) for case in regenerated["cases"]), 96)
        result = compare_candidate(
            self.reference, candidate_from_reference(regenerated))
        self.assertTrue(result["passed"])
        self.assertEqual(result["steps"], 96)
        self.assertLess(result["max_checkpoint_node_error_v"], 1e-7)

    def test_candidate_gate_rejects_output_state_and_kcl_errors(self):
        baseline = candidate_from_reference(self.reference)
        self.assertTrue(compare_candidate(self.reference, baseline)["passed"])
        altered = copy.deepcopy(baseline)
        altered["cases"][0]["steps"][0]["j7_tip_v"] += 0.001
        with self.assertRaisesRegex(ValueError, "j7_tip_v"):
            compare_candidate(self.reference, altered)
        altered = copy.deepcopy(baseline)
        altered["cases"][0]["steps"][0]["amp_capacitor_v"]["C19"] += 0.1
        with self.assertRaisesRegex(ValueError, "capacitor state"):
            compare_candidate(self.reference, altered)
        altered = copy.deepcopy(baseline)
        altered["cases"][0]["steps"][0]["max_kcl_residual_a"] = 1e-8
        with self.assertRaisesRegex(ValueError, "KCL"):
            compare_candidate(self.reference, altered)
        altered = copy.deepcopy(baseline)
        altered["cases"][0]["steps"].pop()
        with self.assertRaisesRegex(ValueError, "step count"):
            compare_candidate(self.reference, altered)


if __name__ == "__main__":
    unittest.main()
