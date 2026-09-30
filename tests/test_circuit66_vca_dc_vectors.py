import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from circuit66_vca_dc_vectors import OUTPUT, generate_vectors


class Circuit66VcaDc(unittest.TestCase):
    def test_independent_zero_source_roots_and_continuation_regenerate(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen,generate_vectors())
        self.assertEqual(len(frozen["cases"]),6)
        for case in frozen["cases"]:
            self.assertLess(case["max_kcl_a"],1e-11)
            self.assertLess(case["max_correction_v"],1e-8)
            self.assertEqual(len(case["stages"]),32)
            # Both independent paths arrive at the same nominal DC branch.
            self.assertIsNone(case["direct_error"])
            self.assertLess(max(abs(a-b) for a,b in zip(case["node_v"],case["direct_node_v"])),1e-6)
            for stage in case["stages"]:
                self.assertLess(stage["kcl_a"],1e-11)
                self.assertLess(stage["correction_v"],1e-8)


if __name__ == "__main__":
    unittest.main()
