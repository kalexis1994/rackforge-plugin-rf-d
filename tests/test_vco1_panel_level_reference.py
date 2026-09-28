"""Check SW9-ON R6/R45 passive loading at endpoints and interior positions."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_panel_level_reference import panel_level_reference  # noqa: E402


class PanelLevelTests(unittest.TestCase):
    def test_endpoints_match_exact_circuits(self) -> None:
        low = panel_level_reference(0.0)["admittance_siemens"]
        high = panel_level_reference(1.0)["admittance_siemens"]
        self.assertAlmostEqual(low[0][0], 1 / 25000)
        self.assertAlmostEqual(low[0][1], 0)
        self.assertAlmostEqual(low[1][1], 1 / 33000)
        self.assertAlmostEqual(high[0][0], 1 / 25000 + 1 / 33000)
        self.assertAlmostEqual(high[0][1], -1 / 33000)
        self.assertAlmostEqual(high[1][1], 1 / 33000)

    def test_interior_reciprocity_and_kcl(self) -> None:
        for alpha in (0.1, 0.5, 0.9):
            matrix = panel_level_reference(alpha)["admittance_siemens"]
            self.assertAlmostEqual(matrix[0][1], matrix[1][0])
            source_v, mixer_v = 1.2, -0.4
            r_top, r_bottom = 25000 * (1 - alpha), 25000 * alpha
            wiper = (source_v / r_top + mixer_v / 33000) / (1 / r_top + 1 / r_bottom + 1 / 33000)
            source_i = matrix[0][0] * source_v + matrix[0][1] * mixer_v
            mixer_i = matrix[1][0] * source_v + matrix[1][1] * mixer_v
            self.assertAlmostEqual(source_i, (source_v - wiper) / r_top)
            self.assertAlmostEqual(mixer_i, (mixer_v - wiper) / 33000)
            self.assertAlmostEqual(source_i + mixer_i, wiper / r_bottom)

    def test_invalid_position_rejected(self) -> None:
        for alpha in (-0.01, 1.01):
            with self.assertRaises(ValueError):
                panel_level_reference(alpha)


if __name__ == "__main__":
    unittest.main()
