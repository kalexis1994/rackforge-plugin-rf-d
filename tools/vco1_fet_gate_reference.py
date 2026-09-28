"""Conditional DC voltage at the second gate of the VCO 1 dual E402 FET.

The Q3 collector voltage and both rails are imposed. C4 is open at DC, FET gate
current is neglected, and the transistor loop is not solved. This gives no
gain, trip time, or loaded saw estimate. Source: SVC-9 Fig. 9-3 (PDF p. 5),
resistor values checked against Table 7-5 (PDF pp. 24-25).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"
EXPECTED = {
    "R4": (33200, {"POS10_V", "FET_C4_LEFT"}),
    "R24": (10700, {"SCHMITT_DRIVE", "FET_C4_LEFT"}),
    "R25": (15000, {"NEG10_V", "FET_C4_LEFT"}),
}


def conditional_second_gate_v(
    q3_collector_v: float, positive_rail_v: float = 10.0, negative_rail_v: float = -10.0,
) -> float:
    """Return the unloaded resistive gate voltage for imposed Q3 collector voltage."""
    if any(not math.isfinite(v) for v in (q3_collector_v, positive_rail_v, negative_rail_v)):
        raise ValueError("all boundary voltages must be finite")
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    for ref, (value, nodes) in EXPECTED.items():
        part = parts[ref]
        if part["kind"] != "resistor" or part["value"] != value or set(part["terminals"].values()) != nodes:
            raise ValueError(f"{ref} does not match the traced Fig. 9-3 gate divider")
    if parts["Q7"]["terminals"]["right_gate"] != "FET_C4_LEFT":
        raise ValueError("the second Q7 gate is not at the traced node")
    g4, g24, g25 = (1 / parts[ref]["value"] for ref in ("R4", "R24", "R25"))
    return (g4 * positive_rail_v + g24 * q3_collector_v + g25 * negative_rail_v) / (g4 + g24 + g25)


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--q3-collector-v", type=float, required=True)
    parser.add_argument("--positive-rail-v", type=float, default=10.0)
    parser.add_argument("--negative-rail-v", type=float, default=-10.0)
    args = parser.parse_args()
    try:
        gate = conditional_second_gate_v(args.q3_collector_v, args.positive_rail_v, args.negative_rail_v)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({
        "model": "conditional_unloaded_second_FET_gate_DC_only",
        "imposed_q3_collector_v": args.q3_collector_v,
        "second_fet_gate_v": gate,
        "predicts_transistor_gain_or_saw": False,
        "excluded": ["FET gate current", "C4 dynamics and value conflict", "Q3 loading", "rail movement", "device mismatch"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
