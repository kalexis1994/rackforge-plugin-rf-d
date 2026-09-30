"""Freeze a sustained four-cycle numerical signal comparison."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from vca1_output_vectors import generate_vectors  # noqa: E402


class Vca1AudioTraceTest(unittest.TestCase):
    def test_frozen_trace_matches_independent_oracle(self):
        path = ROOT / "evidence" / "vca1_audio_trace.json"
        expected = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(expected, generate_vectors(audio_trace=True))
        self.assertEqual(len(expected["case"]["steps"]), 192)


if __name__ == "__main__":
    unittest.main()
