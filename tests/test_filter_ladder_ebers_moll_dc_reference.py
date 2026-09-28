"""KCL and both-junction regression for the conditional ladder DC solver."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, UPPER, _device, conditional_ladder_ebers_moll_dc)
from semiconductor_ideal import thermal_voltage_v


CUTOFF = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                scale_active_ohm=250, contour_pin16_v=0),
              range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
              beta26=100, beta28=100, temperature_k=298.15)


class LadderEbersMollDCTests(unittest.TestCase):
    def scenario(self, r61=200, reverse_beta=5):
        return conditional_ladder_ebers_moll_dc(
            cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: reverse_beta for name in DEVICE_NODES},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)

    def test_device_equations_obey_kcl_in_active_and_saturation(self):
        vt = thermal_voltage_v(298.15)
        for collector in (1.0, 0.0):
            with self.subTest(collector=collector):
                out = _device(0.6, collector, 0, 1e-14, 100, 5, vt)
                self.assertAlmostEqual(out["emitter_a"],
                                       out["collector_a"] + out["base_a"], delta=1e-18)
                self.assertAlmostEqual(out["collector_a"],
                    out["forward_junction_a"] - out["reverse_junction_a"]
                    - out["reverse_junction_a"] / 5, delta=1e-18)
                self.assertEqual(out["v_bc_v"] > 0, collector == 0)

    def test_both_r61_candidates_close_all_sixteen_node_kcls(self):
        for candidate in (200, 200000):
            with self.subTest(r61=candidate):
                out = self.scenario(candidate)
                self.assertEqual(len(out["nodes_v"]), 16)
                self.assertLess(out["max_kcl_residual_a"], 1e-11)
                for residual in out["kcl_residuals_a"].values():
                    self.assertLess(abs(residual), 1e-11)
                for part in out["devices"].values():
                    self.assertAlmostEqual(part["emitter_a"], part["collector_a"]
                                           + part["base_a"], delta=1e-15)
                self.assertTrue(out["q28_forward_active_candidate"])
                self.assertTrue(out["physical_r61_unresolved"])

    def test_active_case_matches_prior_limit_and_saturated_case_is_solved(self):
        active = self.scenario(200)
        saturated = self.scenario(200000)
        self.assertAlmostEqual(active["nodes_v"]["BOTTOM"], 1.9607503461842566,
                               delta=1e-7)
        self.assertEqual(active["forward_biased_base_collector_devices"], ())
        self.assertEqual(set(saturated["forward_biased_base_collector_devices"]),
                         {"Q29", "Q23", "Q19", "Q10", "Q30", "Q24", "Q20", "Q11"})
        self.assertGreater(saturated["iterations"], 0)

    def test_reverse_gain_changes_saturated_solution(self):
        low = self.scenario(200000, reverse_beta=2)
        high = self.scenario(200000, reverse_beta=20)
        self.assertNotAlmostEqual(low["nodes_v"]["TAIL"], high["nodes_v"]["TAIL"],
                                  delta=1e-4)
        self.assertLess(low["max_kcl_residual_a"], 1e-11)
        self.assertLess(high["max_kcl_residual_a"], 1e-11)

    def test_invalid_reverse_gain_is_rejected(self):
        args = dict(cutoff_inputs=CUTOFF, is29_a=1e-14, is30_a=1e-14,
                    beta29=100, beta30=100,
                    upper_is_a={name: 1e-14 for name in UPPER},
                    upper_beta={name: 100 for name in UPPER},
                    r61_ohm=200, r73_bottom_side_to_wiper_ohm=500)
        for reverse in ({name: 5 for name in list(DEVICE_NODES)[:-1]},
                        {name: math.nan if name == "Q29" else 5
                         for name in DEVICE_NODES},
                        {name: 0 if name == "Q2" else 5
                         for name in DEVICE_NODES}):
            with self.subTest(reverse=reverse), self.assertRaises(ValueError):
                conditional_ladder_ebers_moll_dc(**args, reverse_beta=reverse)


if __name__ == "__main__":
    unittest.main()
