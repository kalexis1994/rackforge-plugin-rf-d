"""Switch-state and shared-source checks for Fig. 9-17 filter CV panel."""

import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from filter_cutoff_base_reference import conditional_q26_base
from filter_cutoff_panel_reference import conditional_panel_q26_base


class FilterCutoffPanelReferenceTests(unittest.TestCase):
    def scenario(self, **changes):
        inputs = dict(cutoff_fraction_from_neg10=0.5, scale_active_ohm=250,
                      contour_pin16_v=0)
        return conditional_panel_q26_base(**(inputs | changes))

    def test_source_document_marks_ground_normals_and_open_keyboard(self):
        p = json.loads((ROOT / "evidence/filter_cutoff_base_network.json").read_text())["parts"]
        self.assertEqual((p["R51"]["ohm"], p["R51"]["jack_normal"]),
                         (100000, "GROUND"))
        self.assertEqual((p["R52"]["switch_off"], p["R52"]["switch_on"]),
                         ("GROUND", "FILTER_MOD_SOURCE"))
        self.assertEqual((p["R53"]["switch_off"], p["R54"]["switch_off"]),
                         ("OPEN", "OPEN"))

    def test_off_panel_loads_are_ground_shunts_not_open(self):
        out = self.scenario(cutoff_fraction_from_neg10=1)
        expected = conditional_q26_base(cutoff_fraction_from_neg10=1,
                                        scale_active_ohm=250, contour_pin16_v=0,
                                        other_branches=((0, 100000), (0, 33000)))
        bare = conditional_q26_base(cutoff_fraction_from_neg10=1,
                                    scale_active_ohm=250, contour_pin16_v=0)
        self.assertEqual(out["j2_mode"], "normalled_ground")
        self.assertEqual(out["sw15_mode"], "ground")
        self.assertAlmostEqual(out["q26_base_v"], expected["q26_base_v"])
        self.assertLess(out["q26_base_v"], bare["q26_base_v"])
        self.assertAlmostEqual(out["resistive_kcl_residual_a"], 0, delta=1e-18)

    def test_plug_and_modulation_have_series_source_impedance(self):
        out = self.scenario(external_control_v=2, external_source_ohm=5000,
                            filter_mod_on=True, modulation_source_v=-1,
                            modulation_source_ohm=7000)
        expected = conditional_q26_base(cutoff_fraction_from_neg10=0.5,
                                        scale_active_ohm=250, contour_pin16_v=0,
                                        other_branches=((2, 105000), (-1, 40000)))
        self.assertEqual(out["j2_mode"], "external")
        self.assertEqual(out["sw15_mode"], "modulation")
        self.assertAlmostEqual(out["q26_base_v"], expected["q26_base_v"])

    def test_two_keyboard_routes_share_one_upstream_source(self):
        out = self.scenario(keyboard_1_3_on=True, keyboard_2_3_on=True,
                            keyboard_cv_v=2, keyboard_source_ohm=10000)
        self.assertAlmostEqual(out["keyboard_parallel_ohm"], 100000)
        self.assertAlmostEqual(out["keyboard_total_source_ohm"], 110000)
        expected = conditional_q26_base(cutoff_fraction_from_neg10=0.5,
                                        scale_active_ohm=250, contour_pin16_v=0,
                                        other_branches=((0, 100000), (0, 33000),
                                                        (2, 110000)))
        self.assertAlmostEqual(out["q26_base_v"], expected["q26_base_v"])
        one = self.scenario(keyboard_1_3_on=True, keyboard_cv_v=2)
        two = self.scenario(keyboard_2_3_on=True, keyboard_cv_v=2)
        self.assertLess(one["q26_base_v"], two["q26_base_v"])
        self.assertLess(two["q26_base_v"], out["q26_base_v"])

    def test_c18_changes_with_switch_conductance(self):
        off = self.scenario()
        on = self.scenario(keyboard_1_3_on=True, keyboard_cv_v=1)
        self.assertLess(on["c18_time_constant_s"], off["c18_time_constant_s"])
        step = self.scenario(keyboard_1_3_on=True, keyboard_cv_v=1,
                             previous_base_v=0, step_s=on["c18_time_constant_s"])
        self.assertAlmostEqual(step["q26_base_v"],
                               on["q26_base_v"] * (1 - math.exp(-1)))

    def test_invalid_states_and_sources_rejected(self):
        for changes in ({"filter_mod_on": True},
                        {"keyboard_1_3_on": True},
                        {"keyboard_2_3_on": True},
                        {"filter_mod_on": 1, "modulation_source_v": 1},
                        {"external_source_ohm": -1},
                        {"keyboard_source_ohm": math.inf},
                        {"external_control_v": math.nan}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.scenario(**changes)


if __name__ == "__main__":
    unittest.main()
