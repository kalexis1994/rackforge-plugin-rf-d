"""The independent six-node DC oracle must reproduce its fixture."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from output_conversion_dc_vectors import generate_vectors  # noqa: E402


class OutputConversionVectorsTest(unittest.TestCase):
    def test_frozen_fixture_matches_oracle(self):
        expected = json.loads((ROOT / "evidence" /
                               "output_conversion_dc_vectors.json").read_text(
                                   encoding="utf-8"))
        self.assertEqual(generate_vectors(), expected)
        self.assertEqual(len(expected["cases"]), 3)


if __name__ == "__main__":
    unittest.main()
