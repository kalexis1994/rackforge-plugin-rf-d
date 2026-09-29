"""The independent Python panel oracle must reproduce its frozen fixture."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from headphone_panel_port_vectors import panel_vectors  # noqa: E402


class PanelPortVectorsTest(unittest.TestCase):
    def test_frozen_fixture_matches_oracle(self):
        expected = json.loads((ROOT / "evidence" /
                               "headphone_panel_port_vectors.json").read_text(
                                   encoding="utf-8"))
        self.assertEqual(panel_vectors(), expected)
        self.assertEqual(sum(len(case["steps"])
                             for case in expected["cases"]), 96)


if __name__ == "__main__":
    unittest.main()
