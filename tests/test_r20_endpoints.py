import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from filter_panel_output_transient_reference import panel_load_reduction
from r20_endpoint_vectors import OUTPUT, explicit_panel, generate_vectors


class R20Endpoints(unittest.TestCase):
    def test_endpoint_reduction_matches_explicit_kcl_with_jack_loads(self):
        for lower in (0, 5000):
            for hi_load, lo_load in ((32, 32), (10000, 100000), (1e9, 1e9)):
                r = panel_load_reduction(r20_wiper_to_ground_ohm=lower,
                                         hi_load_ohm=hi_load, lo_load_ohm=lo_load)
                for c2 in (-10, -0.1, 0, 0.1, 10):
                    v = explicit_panel(c2, lower, True, hi_load, lo_load)
                    pin = c2*r["equivalent_main_load_ohm"]/(1000+r["equivalent_main_load_ohm"])
                    hi = pin*r["hi_to_pin21_ratio"]
                    lo = hi*r["lo_to_hi_ratio"]
                    self.assertAlmostEqual(pin, v["pin21_v"], delta=1e-12)
                    self.assertAlmostEqual(hi, v["hi_v"], delta=1e-12)
                    self.assertAlmostEqual(lo, v["lo_v"], delta=1e-12)
                    self.assertAlmostEqual((c2-pin)/1000, v["r75_a"], delta=1e-14)
                    if lower == 0:
                        self.assertEqual(hi, 0)
                        self.assertEqual(lo, 0)
                    else:
                        self.assertEqual(pin, hi)
        for lower in (-1, 5001, float("nan")):
            with self.assertRaises(ValueError):
                panel_load_reduction(r20_wiper_to_ground_ohm=lower, hi_load_ohm=1e4, lo_load_ohm=1e5)

    def test_full_fd_vectors_regenerate(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen, generate_vectors())
        self.assertEqual(sum(len(c["rows"]) for c in frozen["cases"]), 128)


if __name__ == "__main__":
    unittest.main()
