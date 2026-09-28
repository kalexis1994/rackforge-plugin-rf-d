"""Check the passive panel network and board-terminal connection."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_panel_pulse_reference import panel_pulse_reference  # noqa: E402


class PanelPulseTests(unittest.TestCase):
    def test_contact_divider_open_circuit_and_thevenin(self) -> None:
        result = panel_pulse_reference()
        contacts = result["sw6_lower_contact_sources_at_22b"]
        self.assertEqual(contacts["7"]["voltage_v"], -10)
        self.assertEqual(contacts["10"]["voltage_v"], 0)
        self.assertIsNone(contacts["8"]["voltage_v"])
        self.assertIsNone(contacts["9"]["voltage_v"])
        self.assertAlmostEqual(contacts["11"]["voltage_v"], -1.5)
        self.assertAlmostEqual(contacts["12"]["voltage_v"], -2.5)
        self.assertAlmostEqual(contacts["11"]["thevenin_ohm"], 1275)
        self.assertAlmostEqual(contacts["12"]["thevenin_ohm"], 1875)

    def test_rectangular_load_when_selected(self) -> None:
        result = panel_pulse_reference()
        ground = 1 / (1 / 4700 + 1 / 25000)
        self.assertAlmostEqual(result["rect_20b_pulse_selected_r6_track_to_ground_ohm"], ground)
        self.assertAlmostEqual(result["rect_20b_coefficient_of_imposed_q12_collector"], ground / (6200 + ground))


if __name__ == "__main__":
    unittest.main()
