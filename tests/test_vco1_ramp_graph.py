"""Protect the traced ramp connections against later netlist transcription errors."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RampGraphTests(unittest.TestCase):
    def test_graph_uses_only_declared_nodes_and_agrees_with_package_pins(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        pinmap = json.loads((ROOT / "evidence" / "vco1_ic2_pinmap.json").read_text(encoding="utf-8"))
        nodes = set(graph["nodes"])
        refs = [part["ref"] for part in graph["parts"]]
        self.assertEqual(len(refs), len(set(refs)))
        for part in graph["parts"]:
            self.assertTrue(set(part["terminals"].values()) <= nodes)
        for device in pinmap["transistors"]:
            part = next(part for part in graph["parts"] if part["ref"] == "IC2." + device["board_name"])
            self.assertEqual(part["package_pins"], {
                terminal: device[terminal] for terminal in part["package_pins"]
            })

    def test_ramp_has_documented_current_sink_and_reset_switch(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        self.assertEqual(set(parts["C1"]["terminals"].values()), {"GND", "RAMP_C1"})
        self.assertEqual(parts["IC2.Qa"]["terminals"]["collector"], "RAMP_C1")
        self.assertEqual(parts["Q10"]["terminals"], {"emitter": "GND", "collector": "RAMP_C1"})
        self.assertEqual(parts["IC2.Qc"]["terminals"]["collector"], parts["IC2.Qa"]["terminals"]["emitter"])
        self.assertEqual(set(parts["R42"]["terminals"].values()), {"IC1_SUM", "QC_EMITTER"})
        self.assertEqual(set(parts["R79"]["terminals"].values()), {"QC_EMITTER", "NEG10_V"})
        self.assertEqual(set(parts["R19"]["terminals"].values()), {"R8_BOTTOM", "NEG5_V"})
        self.assertEqual(parts["R8"]["terminals"]["wiper"], parts["IC2.Qb"]["terminals"]["base"])
        self.assertEqual(set(parts["C2"]["terminals"].values()), {"QA_BASE", "QB_BASE"})
        self.assertEqual(set(parts["R7"]["terminals"].values()), {"QA_BASE", "NEG5_V"})

    def test_ic3_reference_loop_and_rc_network_are_traced_as_drawn(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        self.assertEqual(parts["IC3"]["terminals"], {
            "noninverting": "QB_COLLECTOR", "inverting": "NEG4_REF", "output": "IC3_OUT"
        })
        self.assertEqual(parts["IC2.Qc"]["terminals"]["base"], "QC_BASE")
        self.assertEqual(set(parts["R69"]["terminals"].values()), {"IC3_OUT", "QC_BASE"})
        self.assertEqual(parts["R69"]["kind"], "resistor")
        self.assertEqual(parts["R78"]["kind"], "resistance_capacitance_network")
        self.assertEqual(parts["R78"]["terminals"], {"a": "QC_BASE", "b": "NEG10_V"})
        self.assertEqual(parts["R78"]["branches"], [
            {"kind": "resistor", "resistance_ohm": 2000},
            {"kind": "series_rc", "resistance_ohm": 220, "capacitance_farad": 1e-8},
        ])


if __name__ == "__main__":
    unittest.main()
