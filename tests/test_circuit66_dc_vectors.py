import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from circuit66_dc_vectors import OUTPUT, generate_vectors


class Circuit66Dc(unittest.TestCase):
    def test_fourteen_full_fd_dc_points_regenerate(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen, generate_vectors())
        self.assertEqual(len(frozen["cases"]), 14)
        for c in frozen["cases"]:
            self.assertLess(c["max_kcl_a"], 1e-11)
            self.assertEqual(len(c["node_v"]), 66)
            for i in (47, 48, 49, 61):
                self.assertLess(abs(c["node_v"][i]), 1e-12)


if __name__ == "__main__":
    unittest.main()
