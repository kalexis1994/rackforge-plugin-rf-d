"""Check the shared reference inventory and conditional divider calculation."""

import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from neg4_reference import conditional_reference_v, divider_model


class SharedReferenceTests(unittest.TestCase):
    def test_schematic_inventory_covers_three_opamps_and_base_drives(self) -> None:
        evidence = json.loads((ROOT / "evidence" / "neg4_reference_loads.json").read_text(encoding="utf-8"))
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        graph_parts = {part["ref"]: part for part in graph["parts"]}
        self.assertEqual(evidence["node"], "NEG4_REF")
        self.assertEqual(graph_parts["IC3"]["terminals"]["inverting"], evidence["node"])
        self.assertEqual({part["ref"] for part in evidence["external_connections"]},
                         {"IC3", "IC5", "IC10", "R49", "R86", "R161"})
        self.assertEqual({part["oscillator"] for part in evidence["external_connections"]}, {1, 2, 3})
        self.assertEqual({part["ref"] for part in evidence["divider"]}, {"R166", "R174"})
        self.assertEqual(evidence["bypass"]["ref"], "C14")

    def test_kcl_and_signed_load_sensitivity(self) -> None:
        v_th, r_th = divider_model()
        self.assertAlmostEqual(v_th, -10 * 3900 / (6200 + 3900))
        self.assertAlmostEqual(r_th, 6200 * 3900 / (6200 + 3900))
        self.assertEqual(conditional_reference_v(0), v_th)
        for current_a in (1e-6, -1e-6, 20e-6):
            voltage = conditional_reference_v(current_a)
            self.assertAlmostEqual(voltage, v_th - r_th * current_a)
            self.assertAlmostEqual((voltage + 10) / 6200 + voltage / 3900 + current_a, 0)

    def test_nonfinite_scenario_is_rejected(self) -> None:
        for current_a in (math.inf, -math.inf, math.nan):
            with self.assertRaises(ValueError):
                conditional_reference_v(current_a)


if __name__ == "__main__":
    unittest.main()
