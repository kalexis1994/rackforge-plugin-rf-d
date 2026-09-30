import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from circuit66_r21_vectors import OUTPUT, generate_vectors


class Circuit66R21(unittest.TestCase):
    def test_independent_dc_and_complete_endpoint_traces_regenerate(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen,generate_vectors())
        self.assertTrue(frozen["passed"])
        self.assertEqual(sum(len(c["rows"]) for c in frozen["cases"]),128)
        for case in frozen["cases"]:
            for row in case["rows"]:
                if row["r21_lower_ohm"] == 0:
                    self.assertEqual(row["node_v"][49],0)
                elif row["r21_lower_ohm"] == 5000:
                    self.assertEqual(row["node_v"][49],row["node_v"][48])
                for key,value in row["metrics"].items():
                    self.assertLess(value,frozen["gates"][key])


if __name__ == "__main__":
    unittest.main()
