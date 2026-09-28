"""Protect the conditional pulse-bias and 20B resistor equations."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_pulse_passive_reference import passive_pulse_network  # noqa: E402


class PulsePassiveTests(unittest.TestCase):
    def test_q11_weights_satisfy_base_kcl(self) -> None:
        result = passive_pulse_network()
        weights = result["q11_base_boundary_voltage_coefficients"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertAlmostEqual(weights["PULSE_WIDTH_22B"], weights["SCHMITT_DRIVE"])
        boundaries = {
            "PULSE_WIDTH_22B": -1.0, "SCHMITT_DRIVE": -4.0,
            "SAW_OUTPUT_9B": -2.0, "Q12_COLLECTOR": -7.0,
        }
        base = sum(weights[node] * voltage for node, voltage in boundaries.items())
        kcl = sum((base - boundaries[node]) / resistance for node, resistance in (
            ("PULSE_WIDTH_22B", 43000), ("SCHMITT_DRIVE", 43000),
            ("SAW_OUTPUT_9B", 390000), ("Q12_COLLECTOR", 910000),
        ))
        self.assertAlmostEqual(kcl, 0.0, places=12)

    def test_20b_divider_is_conditional_on_q12_collector(self) -> None:
        result = passive_pulse_network()
        weights = result["rect_20b_boundary_voltage_coefficients"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertAlmostEqual(weights["Q12_COLLECTOR"], 4700 / (4700 + 6200))
        self.assertAlmostEqual(result["rect_20b_passive_thevenin_resistance_ohm"], 1 / (1 / 4700 + 1 / 6200))


if __name__ == "__main__":
    unittest.main()
