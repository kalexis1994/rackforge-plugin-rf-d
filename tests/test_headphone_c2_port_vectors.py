"""The independent 2D Newton oracle must reproduce its frozen fixture."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from headphone_c2_port_vectors import generate_vectors  # noqa: E402


class C2PortVectorsTest(unittest.TestCase):
    def test_frozen_fixture_matches_oracle(self):
        expected = json.loads((ROOT / "evidence" /
                               "headphone_c2_port_vectors.json").read_text(
                                   encoding="utf-8"))
        self.assertEqual(generate_vectors(), expected)
        self.assertEqual(sum(len(case["steps"])
                             for case in expected["cases"]), 96)


if __name__ == "__main__":
    unittest.main()
