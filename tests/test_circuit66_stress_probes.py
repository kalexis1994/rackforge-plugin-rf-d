import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from circuit66_stress_probes import OUTPUT, generate_vectors


class StressProbes(unittest.TestCase):
    def test_192_independent_steps_regenerate_with_open_c10_and_switched_loads(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen, generate_vectors())
        self.assertEqual(len(frozen["windows"]), 48)
        self.assertEqual(sum(len(w["rows"]) for w in frozen["windows"]), 192)
        self.assertEqual({w["sample_rate_hz"] for w in frozen["windows"]}, {44100,48000,96000})
        self.assertEqual({w["r61_ohm"] for w in frozen["windows"]}, {200,200000})
        for window in frozen["windows"]:
            previous_c10 = window["initial"]["c10_v"]
            for row in window["rows"]:
                self.assertLess(row["max_kcl_a"], 1e-10)
                if row["boundary"]["r14_ohm"] is None:
                    self.assertEqual(row["c10_v"], previous_c10)
                previous_c10 = row["c10_v"]


if __name__ == "__main__":
    unittest.main()
