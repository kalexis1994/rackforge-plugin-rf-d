"""Passive conductance inventory at oscillator-1 SAWTOOTH 9B.

All adjacent voltages are independent boundary nodes for this calculation.
Q12 emitter current, external connector load, transistor currents and feedback
are excluded. No physical output amplitude is inferred. Source: SVC-9 Fig. 9-3
(PDF p. 5), resistor values checked in Table 7-5 (PDF pp. 24-25).
"""

from __future__ import annotations

import json
from pathlib import Path


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"
EXPECTED = {
    "R34": (4300, "SCHMITT_DRIVE"),
    "R33": (4700, "GND"),
    "R23": (8200, "TRI_OUTPUT_21B"),
    "R14": (150000, "Q2_COLLECTOR"),
    "R29": (10000, "Q2_EMITTER"),
    "R44": (390000, "Q11_BASE"),
    "R35": (100000, "Q12_BASE"),
}


def passive_saw_9b() -> dict[str, object]:
    """Return the conditional 9B conductance fractions and passive Rth."""
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    if parts["Q12"]["terminals"]["emitter"] != "SAW_OUTPUT_9B":
        raise ValueError("Q12 direct emitter load must remain explicit")
    conductance = {}
    for ref, (value, other_node) in EXPECTED.items():
        part = parts[ref]
        if part["kind"] != "resistor" or part["value"] != value:
            raise ValueError(f"{ref} does not match Fig. 9-3")
        if set(part["terminals"].values()) != {"SAW_OUTPUT_9B", other_node}:
            raise ValueError(f"{ref} is not connected to the traced 9B node")
        conductance[other_node] = 1 / value
    total = sum(conductance.values())
    return {
        "passive_thevenin_resistance_ohm": 1 / total,
        "boundary_voltage_coefficients": {node: g / total for node, g in conductance.items()},
        "excluded": ["Q12 emitter current", "external 9B load", "feedback among boundary nodes"],
    }


if __name__ == "__main__":
    print(json.dumps(passive_saw_9b(), indent=2))
