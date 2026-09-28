"""Conditional passive map from Q1 emitter and saw 9B to triangle 21B.

Q1 emitter and 9B are imposed; external 21B load is open. This excludes
Q1/Q2 device currents and the coupled 9B circuit, so it is not a waveform
amplitude prediction. Source: SVC-9 Fig. 9-3 (PDF p. 5), Table 7-5
(PDF pp. 24-25).
"""

from __future__ import annotations

import json
from pathlib import Path


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"


def passive_triangle_21b() -> dict[str, object]:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    expected = {
        "R28": (750, {"Q1_EMITTER", "TRI_OUTPUT_21B"}),
        "R23": (8200, {"SAW_OUTPUT_9B", "TRI_OUTPUT_21B"}),
    }
    for ref, (value, terminals) in expected.items():
        part = parts[ref]
        if part["kind"] != "resistor" or part["value"] != value or set(part["terminals"].values()) != terminals:
            raise ValueError(f"{ref} does not match Fig. 9-3 triangle output")
    if parts["Q1"]["terminals"]["emitter"] != "Q1_EMITTER":
        raise ValueError("Q1 is not connected to the traced 21B output resistor")
    g28, g23 = 1 / 750, 1 / 8200
    total = g28 + g23
    return {
        "passive_thevenin_resistance_ohm": 1 / total,
        "boundary_voltage_coefficients": {
            "Q1_EMITTER": g28 / total,
            "SAW_OUTPUT_9B": g23 / total,
        },
        "excluded": ["Q1/Q2 device currents", "external 21B load", "9B feedback"],
    }


if __name__ == "__main__":
    print(json.dumps(passive_triangle_21b(), indent=2))
