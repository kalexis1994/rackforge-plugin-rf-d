import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from circuit66_vca_jump_vectors import OUTPUT, generate_vectors


class Circuit66VcaJump(unittest.TestCase):
    def test_independent_abrupt_source_traces_regenerate(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen,generate_vectors())
        self.assertTrue(frozen["passed"])
        self.assertEqual(sum(len(c["rows"]) for c in frozen["cases"]),384)
        self.assertEqual(sum(row["direct_error"] is not None for c in frozen["cases"] for row in c["rows"]),8)
        for case in frozen["cases"]:
            for row in case["rows"]:
                for key,value in row["metrics"].items(): self.assertLess(value,frozen["gates"][key])


if __name__ == "__main__":
    unittest.main()
