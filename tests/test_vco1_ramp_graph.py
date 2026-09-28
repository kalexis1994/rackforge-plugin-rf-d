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
        self.assertEqual(parts["Q10"]["terminals"], {
            "emitter": "GND", "collector": "RAMP_C1", "base": "Q10_BASE"
        })
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
            "noninverting": "QB_COLLECTOR", "inverting": "NEG4_REF", "output": "IC3_OUT",
            "positive_supply": "POS10_V", "negative_supply": "NEG10_V"
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

    def test_reset_trace_keeps_q5_q6_part_conflict_open(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        evidence = json.loads((ROOT / "evidence" / "vco1_ca3046_parts.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        source_parts = {part["ref"]: part for part in evidence["components"]}
        for ref in ("Q5", "Q6"):
            self.assertEqual(set(parts[ref]["part_candidates"]), {
                source_parts[ref]["schematic"], source_parts[ref]["bom"]
            })
            self.assertEqual(parts[ref]["candidate_status"], "schematic_BOM_conflict")
            self.assertEqual(parts[ref]["terminals"]["emitter"], "GND")
        self.assertEqual(parts["Q5"]["terminals"]["collector"], parts["Q6"]["terminals"]["base"])
        self.assertEqual(set(parts["R41"]["terminals"].values()), {
            parts["Q6"]["terminals"]["collector"], parts["Q10"]["terminals"]["base"]
        })
        self.assertEqual(parts["R41"]["value"], 910)
        self.assertEqual(parts["Q10"]["terminals"]["collector"], "RAMP_C1")

    def test_schmitt_bias_returns_to_negative_rail_not_saw_output(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        expected = {
            "R6": (56, {"SCHMITT_Q6_COLLECTOR", "RESET_BIAS"}),
            "R15": (2200, {"POS10_V", "SCHMITT_DRIVE"}),
            "R16": (33200, {"POS10_V", "SCHMITT_SENSE"}),
            "R17": (10000, {"SCHMITT_SENSE", "RESET_BIAS"}),
            "R26": (1000, {"RESET_BIAS", "NEG10_V"}),
            "R30": (10700, {"SCHMITT_DRIVE", "SCHMITT_SENSE"}),
            "R31": (10000, {"SCHMITT_Q5_COLLECTOR", "NEG10_V"}),
        }
        for ref, (value, nodes) in expected.items():
            self.assertEqual(parts[ref]["value"], value)
            self.assertEqual(set(parts[ref]["terminals"].values()), nodes)
        self.assertEqual(parts["Q5"]["terminals"]["base"], "SCHMITT_SENSE")
        self.assertEqual(parts["Q6"]["terminals"]["collector"], "SCHMITT_Q6_COLLECTOR")
        self.assertNotIn("SAW_OUTPUT", graph["nodes"])

    def test_fet_coupling_keeps_c4_value_disagreement_explicit(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        self.assertEqual(set(parts["C3"]["terminals"].values()), {"FET_C3_LEFT", "SCHMITT_DRIVE"})
        self.assertEqual(parts["C3"]["value"], 1e-10)
        self.assertEqual(set(parts["C4"]["terminals"].values()), {"FET_C4_LEFT", "SCHMITT_DRIVE"})
        self.assertEqual(set(parts["R24"]["terminals"].values()), set(parts["C4"]["terminals"].values()))
        self.assertEqual(parts["C4"]["value"], 1e-11)
        self.assertEqual(parts["C4"]["bom_value"], 1e-10)
        self.assertEqual(parts["C4"]["candidate_status"], "schematic_BOM_conflict")
        self.assertEqual(set(parts["R4"]["terminals"].values()), {"POS10_V", "FET_C4_LEFT"})
        self.assertEqual(set(parts["R45"]["terminals"].values()), {"POS10_V", "FET_C3_LEFT"})

    def test_dual_fet_amplifier_reaches_q3_and_saw_connector(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        self.assertEqual(parts["Q7"]["terminals"], {
            "left_gate": "RAMP_C1", "left_drain": "FET_LEFT_DRAIN",
            "right_gate": "FET_C4_LEFT", "right_drain": "FET_RIGHT_DRAIN",
            "common_source": "FET_COMMON_SOURCE",
        })
        self.assertEqual(parts["Q8"]["terminals"], {
            "base": "FET_RIGHT_DRAIN", "emitter": "FET_C3_LEFT", "collector": "Q3_BASE"
        })
        self.assertEqual(parts["Q9"]["terminals"], {
            "base": "FET_LEFT_DRAIN", "emitter": "FET_C3_LEFT", "collector": "NEG10_V"
        })
        self.assertEqual(parts["Q3"]["terminals"], {
            "base": "Q3_BASE", "collector": "SCHMITT_DRIVE", "emitter": "NEG10_V"
        })
        expected = {
            "R5": (5600, {"POS10_V", "FET_RIGHT_DRAIN"}),
            "R46": (5600, {"POS10_V", "FET_LEFT_DRAIN"}),
            "R47": (100, {"FET_COMMON_SOURCE", "Q4_COLLECTOR"}),
            "R48": (12000, {"Q4_EMITTER", "NEG10_V"}),
            "R49": (1000, {"NEG4_REF", "Q4_BASE"}),
            "R25": (15000, {"FET_C4_LEFT", "NEG10_V"}),
            "R36": (2700, {"Q3_BASE", "NEG10_V"}),
            "R34": (4300, {"SCHMITT_DRIVE", "SAW_OUTPUT_9B"}),
        }
        for ref, (value, nodes) in expected.items():
            self.assertEqual(parts[ref]["value"], value)
            self.assertEqual(set(parts[ref]["terminals"].values()), nodes)
        self.assertEqual(parts["Q4"]["terminals"], {
            "base": "Q4_BASE", "collector": "Q4_COLLECTOR", "emitter": "Q4_EMITTER"
        })

    def test_saw_9b_includes_triangle_and_pulse_stage_loads(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        expected = {
            "R33": (4700, {"GND", "SAW_OUTPUT_9B"}),
            "R34": (4300, {"SCHMITT_DRIVE", "SAW_OUTPUT_9B"}),
            "R23": (8200, {"TRI_OUTPUT_21B", "SAW_OUTPUT_9B"}),
            "R14": (150000, {"Q2_COLLECTOR", "SAW_OUTPUT_9B"}),
            "R29": (10000, {"Q2_EMITTER", "SAW_OUTPUT_9B"}),
            "R44": (390000, {"Q11_BASE", "SAW_OUTPUT_9B"}),
            "R35": (100000, {"Q12_BASE", "SAW_OUTPUT_9B"}),
        }
        for ref, (value, nodes) in expected.items():
            self.assertEqual(parts[ref]["value"], value)
            self.assertEqual(set(parts[ref]["terminals"].values()), nodes)
        self.assertEqual(parts["Q12"]["terminals"]["emitter"], "SAW_OUTPUT_9B")
        self.assertEqual(parts["Q12"]["kind"], "NPN_2N3392_schematic")

    def test_triangle_former_and_buffer_connect_internal_saw_to_21b(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        self.assertEqual(parts["Q2"]["terminals"], {
            "base": "SCHMITT_DRIVE", "collector": "Q2_COLLECTOR", "emitter": "Q2_EMITTER"
        })
        self.assertEqual(parts["Q1"]["terminals"], {
            "base": "Q2_COLLECTOR", "collector": "POS10_V", "emitter": "Q1_EMITTER"
        })
        expected = {
            "R3": (10700, {"POS10_V", "Q2_COLLECTOR"}),
            "R14": (150000, {"Q2_COLLECTOR", "SAW_OUTPUT_9B"}),
            "R28": (750, {"Q1_EMITTER", "TRI_OUTPUT_21B"}),
            "R29": (10000, {"Q2_EMITTER", "SAW_OUTPUT_9B"}),
            "R23": (8200, {"TRI_OUTPUT_21B", "SAW_OUTPUT_9B"}),
        }
        for ref, (value, nodes) in expected.items():
            self.assertEqual(parts[ref]["value"], value)
            self.assertEqual(set(parts[ref]["terminals"].values()), nodes)

    def test_trim_and_reference_divider_keep_voltage_label_distinct(self) -> None:
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        parts = {part["ref"]: part for part in graph["parts"]}
        self.assertEqual(parts["R11"]["terminals"], {
            "high": "IC1_SUM", "wiper": "IC1_SUM", "low": "R37_TOP"
        })
        self.assertEqual(set(parts["R37"]["terminals"].values()), {"R37_TOP", "NEG10_V"})
        self.assertEqual(parts["R37"]["value"], 11800)
        self.assertEqual(parts["IC1"]["terminals"]["noninverting"], "IC1_PLUS")
        self.assertEqual(set(parts["R10"]["terminals"].values()), {"IC1_PLUS", "NEG5_V"})
        self.assertEqual(set(parts["R166"]["terminals"].values()), {"NEG10_V", "NEG4_REF"})
        self.assertEqual(set(parts["R174"]["terminals"].values()), {"NEG4_REF", "GND"})
        self.assertEqual(set(parts["C14"]["terminals"].values()), {"NEG4_REF", "GND"})
        self.assertEqual(graph["schematic_voltage_labels_v"]["NEG4_REF"], -4)


if __name__ == "__main__":
    unittest.main()
