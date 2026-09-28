"""Second VCA current conservation and explicit interstage loading."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from vca2_active_core_dc_reference import DEVICES, conditional_vca2_dc


PARAMS = dict(is_a={n: 1e-14 for n in DEVICES},
              beta_forward={n: 100 for n in DEVICES},
              beta_reverse={n: 5 for n in DEVICES}, temperature_k=298.15)


class Vca2ActiveCoreDcTest(unittest.TestCase):
    def solve(self, control=2, trim=50):
        return conditional_vca2_dc(
            q14_base_v=7.5256, q13_base_v=7.5252,
            q21_base_v=control, wiper_v=9,
            balance_left_ohm=trim, **PARAMS)

    def test_five_kcl_rows_and_tail_conservation(self):
        for control in (0, 0.5, 1, 2, 3):
            with self.subTest(control=control):
                out = self.solve(control=control)
                self.assertLess(out["max_kcl_residual_a"], 1e-12)
                q = out["devices"]
                self.assertAlmostEqual(
                    q["Q14"]["emitter_a"] + q["Q13"]["emitter_a"],
                    q["Q21"]["collector_a"], delta=1e-12)
                self.assertEqual(out["first_vca_collector_load_currents_a"],
                                 (q["Q14"]["base_a"], q["Q13"]["base_a"]))
                self.assertAlmostEqual(
                    out["external_q21_base_source_current_a"],
                    q["Q21"]["base_a"] + control / 33000,
                    delta=1e-15)

    def test_external_loudness_changes_tail_and_trim_redistributes(self):
        off = self.solve(control=0)
        on = self.solve(control=2)
        self.assertLess(off["devices"]["Q21"]["collector_a"], 1e-8)
        self.assertGreater(on["devices"]["Q21"]["collector_a"], 4e-4)
        left = self.solve(trim=0)["nodes_v"]
        right = self.solve(trim=100)["nodes_v"]
        self.assertNotAlmostEqual(left["Q14_COLLECTOR"],
                                  right["Q14_COLLECTOR"], delta=1e-3)

    def test_invalid_source_and_trim_rejected(self):
        for trim in (-1, 101, float("inf")):
            with self.subTest(trim=trim), self.assertRaises(ValueError):
                self.solve(trim=trim)


if __name__ == "__main__":
    unittest.main()
