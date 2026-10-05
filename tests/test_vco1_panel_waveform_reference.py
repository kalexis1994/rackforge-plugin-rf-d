"""Protect SW6/R6 waveform loading and the permanent 9B-21B bridge."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_panel_waveform_reference import panel_waveform_reference  # noqa: E402


class PanelWaveformTests(unittest.TestCase):
    def test_bridge_exists_in_every_switch_contact(self) -> None:
        result = panel_waveform_reference()
        self.assertEqual(result["panel_permanent_series_bridge_ohm"], 57000)
        self.assertEqual(result["board_r23_shunt_ohm"], 8200)
        self.assertEqual(result["board_r23_reference_v"], -10)
        self.assertEqual(result["board_r23_affine_current_a"], [0, 10 / 8200])
        for case in result["selected_contact_cases"].values():
            panel = case["panel_admittance_siemens"]
            combined = case["panel_plus_board_r23_admittance_siemens"]
            self.assertEqual(combined[0], panel[0])
            self.assertEqual(combined[1][0], panel[1][0])
            self.assertAlmostEqual(combined[1][1] - panel[1][1], 1 / 8200)
        for case in result["selected_contact_cases"].values():
            matrix = case["panel_admittance_siemens"]
            self.assertAlmostEqual(matrix[0][1], matrix[1][0])
            self.assertLess(matrix[0][1], 0)

    def test_r6_load_moves_with_selector(self) -> None:
        cases = panel_waveform_reference()["selected_contact_cases"]
        g6 = 1 / 25000
        pulse = cases["4"]["panel_admittance_siemens"]
        for contact in ("5", "6"):
            self.assertEqual(cases[contact]["panel_admittance_siemens"], pulse)
        saw = cases["3"]["panel_admittance_siemens"]
        tri = cases["1"]["panel_admittance_siemens"]
        self.assertAlmostEqual(saw[0][0] - pulse[0][0], g6)
        self.assertAlmostEqual(saw[1][1] - pulse[1][1], 0)
        self.assertAlmostEqual(tri[1][1] - pulse[1][1], g6)
        self.assertAlmostEqual(tri[0][0] - pulse[0][0], 0)

    def test_tap_selection_obeys_kcl(self) -> None:
        matrix = panel_waveform_reference()["selected_contact_cases"]["2"]["panel_admittance_siemens"]
        saw_v, tri_v = 1.2, -0.7
        g30, g31, g6 = 1 / 47000, 1 / 10000, 1 / 25000
        tap_v = (g30 * saw_v + g31 * tri_v) / (g30 + g31 + g6)
        currents = (matrix[0][0] * saw_v + matrix[0][1] * tri_v,
                    matrix[1][0] * saw_v + matrix[1][1] * tri_v)
        self.assertAlmostEqual(currents[0], (saw_v - tap_v) / 47000)
        self.assertAlmostEqual(currents[1], (tri_v - tap_v) / 10000)
        self.assertAlmostEqual(currents[0] + currents[1], tap_v / 25000)


if __name__ == "__main__":
    unittest.main()
