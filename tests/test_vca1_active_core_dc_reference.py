"""Circuit KCL, limiting states and balance for the conditional first VCA."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from vca1_active_core_dc_reference import DEVICES, _evaluate, conditional_vca1_dc


PARAMS = dict(is_a={name: 1e-14 for name in DEVICES},
              beta_forward={name: 100 for name in DEVICES},
              beta_reverse={name: 5 for name in DEVICES},
              temperature_k=298.15)


class Vca1ActiveCoreDcTest(unittest.TestCase):
    def solve(self, loudness=2, wiper=5, trim=12.5):
        return conditional_vca1_dc(wiper_v=wiper, loudness_v=loudness,
                                   balance_left_ohm=trim, **PARAMS)

    def test_all_eight_kcl_rows_and_tail_current(self):
        for loudness in (0, 0.25, 0.5, 1, 2, 3):
            with self.subTest(loudness=loudness):
                result = self.solve(loudness=loudness)
                self.assertLess(result["max_kcl_residual_a"], 1e-12)
                x = list(result["nodes_v"].values())
                residual, _ = _evaluate(x, **result["network_parameters"])
                self.assertLess(max(abs(v) for v in residual), 1e-12)
                q = result["devices"]
                self.assertAlmostEqual(q["Q16"]["emitter_a"] + q["Q15"]["emitter_a"],
                                       q["Q18"]["collector_a"], delta=1e-12)

    def test_loudness_controls_tail_and_zero_is_nearly_off(self):
        currents = [self.solve(loudness=v)["devices"]["Q18"]["collector_a"]
                    for v in (0, 0.25, 0.5, 1, 2, 3)]
        self.assertEqual(currents, sorted(currents))
        self.assertLess(currents[0], 1e-8)
        self.assertGreater(currents[-1], 3e-4)

    def test_balance_segments_redistribute_collector_voltages(self):
        left = self.solve(trim=0)
        mid = self.solve(trim=12.5)
        right = self.solve(trim=25)
        for result in (left, mid, right):
            self.assertLess(result["max_kcl_residual_a"], 1e-12)
        def delta(result):
            return (result["nodes_v"]["Q16_COLLECTOR"]
                    - result["nodes_v"]["Q15_COLLECTOR"])
        self.assertGreater(delta(left), delta(mid))
        self.assertGreater(delta(mid), delta(right))

    def test_low_wiper_can_drive_q18_base_collector_forward(self):
        result = self.solve(loudness=2, wiper=3)
        self.assertIn("Q18", result["forward_biased_base_collector_devices"])
        self.assertLess(result["max_kcl_residual_a"], 1e-12)

    def test_rejects_invalid_boundaries(self):
        for trim in (-1, 26, float("nan")):
            with self.subTest(trim=trim), self.assertRaises(ValueError):
                self.solve(trim=trim)
        with self.assertRaises(ValueError):
            conditional_vca1_dc(wiper_v=5, loudness_v=2,
                                balance_left_ohm=12.5,
                                is_a={"Q16": 1e-14},
                                beta_forward=PARAMS["beta_forward"],
                                beta_reverse=PARAMS["beta_reverse"],
                                temperature_k=298.15)


if __name__ == "__main__":
    unittest.main()
