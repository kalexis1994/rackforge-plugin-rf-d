"""Protect the five ON-source bus topology and conditional KCL."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from mixer_panel_bus_reference import mixer_bus_coefficients, solve_mixer_bus  # noqa: E402


class MixerPanelBusTests(unittest.TestCase):
    def test_full_level_open_board_weights_match_series_resistors(self) -> None:
        active = {"OSC1", "OSC2", "OSC3", "NOISE", "EXT"}
        result = mixer_bus_coefficients(active, {name: 1.0 for name in active - {"EXT"}})
        weights = result["boundary_voltage_coefficients"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertAlmostEqual(weights["NOISE"], 3 * weights["OSC1"])
        self.assertAlmostEqual(weights["OSC1"], weights["OSC2"])
        self.assertAlmostEqual(weights["OSC1"], weights["OSC3"])
        self.assertAlmostEqual(weights["OSC1"], weights["EXT"])

    def test_bus_kcl_with_loaded_pots_and_imposed_board_current(self) -> None:
        boundaries = {"OSC1": 1.2, "OSC2": -0.4, "NOISE": 0.3, "EXT": -0.2}
        alpha = {"OSC1": 0.7, "OSC2": 0.2, "NOISE": 0.5}
        result = solve_mixer_bus(boundaries, alpha, board_current_a=1e-6)
        self.assertAlmostEqual(result["kcl_residual_a"], 0.0, places=12)
        reference = result["reference"]
        self.assertLess(sum(reference["boundary_voltage_coefficients"].values()), 1.0)

    def test_zero_pot_still_loads_bus_when_source_is_on(self) -> None:
        result = mixer_bus_coefficients({"OSC1"}, {"OSC1": 0.0})
        self.assertAlmostEqual(result["boundary_voltage_coefficients"]["OSC1"], 0.0)
        self.assertAlmostEqual(result["bus_passive_thevenin_resistance_ohm"], 33000)

    def test_active_set_requires_matching_pot_positions(self) -> None:
        with self.assertRaises(ValueError):
            mixer_bus_coefficients({"OSC1", "EXT"}, {})
        with self.assertRaises(ValueError):
            mixer_bus_coefficients({"MISSING"}, {})


if __name__ == "__main__":
    unittest.main()
