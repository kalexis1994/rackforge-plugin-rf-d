"""Regenerate the independent fifteen-variable VCA2/output fixture."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from vca2_output_vectors import generate_vectors  # noqa: E402


class Vca2OutputVectorsTest(unittest.TestCase):
    def test_frozen_fixture_matches_oracle(self):
        path = ROOT / "evidence" / "vca2_output_vectors.json"
        expected = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(expected, generate_vectors())
        self.assertEqual(len(expected["case"]["steps"]), 16)


if __name__ == "__main__":
    unittest.main()
