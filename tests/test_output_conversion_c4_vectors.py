"""Regenerate the independent nine-variable C4/C2 fixture."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from output_conversion_c4_vectors import generate_vectors  # noqa: E402


class OutputConversionC4VectorsTest(unittest.TestCase):
    def test_frozen_fixture_matches_oracle(self):
        path = ROOT / "evidence" / "output_conversion_c4_vectors.json"
        expected = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(expected, generate_vectors())
        self.assertEqual(sum(len(c["steps"]) for c in expected["cases"]), 28)


if __name__ == "__main__":
    unittest.main()
