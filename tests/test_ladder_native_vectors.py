import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ladder_native_vectors import OUTPUT, generate_vectors


class LadderNativeVectors(unittest.TestCase):
    def test_frozen_vectors_regenerate(self):
        self.assertEqual(json.loads(OUTPUT.read_text(encoding="utf-8")),
                         generate_vectors())


if __name__ == "__main__":
    unittest.main()
