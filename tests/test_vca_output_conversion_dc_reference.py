"""Board-4 PNP output-conversion KCL and conditional domain."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from vca_output_conversion_dc_reference import (DEVICES, _parts,
                                                conditional_output_conversion_dc)


PARAMS = dict(is_a={n: 1e-14 for n in DEVICES},
              beta_forward={n: 100 for n in DEVICES},
              beta_reverse={n: 5 for n in DEVICES}, temperature_k=298.15)


class OutputConversionDcTest(unittest.TestCase):
    def solve(self, q12=7.75, q17=7.75, q1=8.3):
        return conditional_output_conversion_dc(
            q1_base_v=q1, q12_base_v=q12, q17_base_v=q17, **PARAMS)

    def test_documented_parts_and_nodal_conservation(self):
        self.assertEqual(_parts()["R9"], 62)
        out = self.solve()
        self.assertEqual(len(out["nodes_v"]), 6)
        self.assertLess(out["max_kcl_residual_a"], 1e-12)
        v, q = out["nodes_v"], out["devices"]
        self.assertAlmostEqual((10-v["Q1_EMITTER"])/62,
                               q["Q1"]["emitter_a"], delta=1e-12)
        self.assertAlmostEqual(q["Q1"]["collector_a"],
                               q["Q12"]["emitter_a"]
                               + q["Q17"]["emitter_a"], delta=1e-12)
        self.assertAlmostEqual(v["Q17_COLLECTOR"]/680,
                               q["Q17"]["collector_a"], delta=1e-12)
        self.assertAlmostEqual(q["Q17"]["emitter_a"],
                               q["Q17"]["collector_a"]
                               + q["Q17"]["base_a"], delta=1e-12)
        self.assertGreater(v["Q17_COLLECTOR"], 0)
        self.assertLess(v["Q17_COLLECTOR"], 10)

    def test_differential_drive_produces_single_ended_response(self):
        balanced = self.solve()["q17_collector_output_v"]
        lower_q17_base = self.solve(q17=7.73)["q17_collector_output_v"]
        higher_q17_base = self.solve(q17=7.77)["q17_collector_output_v"]
        self.assertGreater(lower_q17_base, balanced)
        self.assertLess(higher_q17_base, balanced)

    def test_incomplete_device_parameters_rejected(self):
        with self.assertRaises(ValueError):
            conditional_output_conversion_dc(
                q1_base_v=8.3, q12_base_v=7.75, q17_base_v=7.75,
                is_a={"Q1": 1e-14},
                beta_forward=PARAMS["beta_forward"],
                beta_reverse=PARAMS["beta_reverse"],
                temperature_k=298.15)


if __name__ == "__main__":
    unittest.main()
