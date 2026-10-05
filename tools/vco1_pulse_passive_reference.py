"""Conditional passive weights of VCO-1 Q11 base and rectangular output 20B.

Q11 base current, Q12 collector current, transistor switching, external loads,
and feedback closure are excluded. These weights are not a pulse width or
output amplitude prediction. Source: SVC-9 Fig. 9-3 (PDF p. 5), Table 7-5
(PDF pp. 24-25).
"""

from __future__ import annotations

import json
from pathlib import Path


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"
Q11_INPUTS = {
    "R1": (43000, "PULSE_WIDTH_22B"),
    "R40": (43000, "SCHMITT_DRIVE"),
    "R44": (390000, "NEG10_V"),
    "R2": (910000, "Q12_COLLECTOR"),
}


def passive_pulse_network() -> dict[str, object]:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    if parts["Q11"]["terminals"] != {
        "base": "Q11_BASE", "collector": "Q11_COLLECTOR", "emitter": "GND"
    }:
        raise ValueError("Q11 is not the traced PNP pulse stage")
    conductance = {}
    for ref, (value, other_node) in Q11_INPUTS.items():
        part = parts[ref]
        if part["kind"] != "resistor" or part["value"] != value:
            raise ValueError(f"{ref} does not match Fig. 9-3")
        if set(part["terminals"].values()) != {"Q11_BASE", other_node}:
            raise ValueError(f"{ref} does not join the traced Q11 base")
        conductance[other_node] = 1 / value
    for ref, value, other_node in (
        ("R22", 4700, "GND"), ("R13", 6200, "Q12_COLLECTOR")
    ):
        part = parts[ref]
        if part["kind"] != "resistor" or part["value"] != value:
            raise ValueError(f"{ref} does not match Fig. 9-3")
        if set(part["terminals"].values()) != {"RECT_OUTPUT_20B", other_node}:
            raise ValueError(f"{ref} does not join the traced 20B output")
    total = sum(conductance.values())
    g22, g13 = 1 / 4700, 1 / 6200
    return {
        "q11_base_boundary_voltage_coefficients": {node: g / total for node, g in conductance.items()},
        "q11_base_passive_thevenin_resistance_ohm": 1 / total,
        "rect_20b_boundary_voltage_coefficients": {"GND": g22 / (g22 + g13), "Q12_COLLECTOR": g13 / (g22 + g13)},
        "rect_20b_passive_thevenin_resistance_ohm": 1 / (g22 + g13),
        "excluded": ["Q11 base current", "Q12 collector current", "transistor switching", "external 20B load", "feedback closure"],
    }


if __name__ == "__main__":
    print(json.dumps(passive_pulse_network(), indent=2))
