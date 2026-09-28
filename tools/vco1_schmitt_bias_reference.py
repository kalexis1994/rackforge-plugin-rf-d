"""Conditional DC resistive solution of the VCO 1 Q5 sense/reset-bias nodes.

Q6 collector and the FET-derived drive are imposed boundary voltages. Q5 base
current is neglected; transistor switching, C3/C4, and reset timing are absent.
Source: SVC-9 Fig. 9-3 (PDF p. 5), values checked against Table 7-5.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"
EXPECTED = {
    "R6": (56, {"SCHMITT_Q6_COLLECTOR", "RESET_BIAS"}),
    "R16": (33200, {"POS10_V", "SCHMITT_SENSE"}),
    "R17": (10000, {"SCHMITT_SENSE", "RESET_BIAS"}),
    "R26": (1000, {"RESET_BIAS", "NEG10_V"}),
    "R30": (10700, {"SCHMITT_DRIVE", "SCHMITT_SENSE"}),
}


def resistances() -> dict[str, float]:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    result = {}
    for ref, (value, nodes) in EXPECTED.items():
        part = parts[ref]
        if part["kind"] != "resistor" or part["value"] != value or set(part["terminals"].values()) != nodes:
            raise ValueError(f"{ref} does not match the traced Fig. 9-3 branch")
        result[ref] = float(value)
    return result


def conditional_bias_v(
    drive_v: float, q6_collector_v: float, positive_rail_v: float = 10.0,
    negative_rail_v: float = -10.0,
) -> tuple[float, float]:
    """Solve Q5 base and R6/R17/R26 junction, with external nodes imposed."""
    boundaries = (drive_v, q6_collector_v, positive_rail_v, negative_rail_v)
    if any(not math.isfinite(v) for v in boundaries):
        raise ValueError("all boundary voltages must be finite")
    r = resistances()
    g_s = 1 / r["R16"] + 1 / r["R17"] + 1 / r["R30"]
    g_b = 1 / r["R17"] + 1 / r["R6"] + 1 / r["R26"]
    coupling = 1 / r["R17"]
    source_s = positive_rail_v / r["R16"] + drive_v / r["R30"]
    source_b = q6_collector_v / r["R6"] + negative_rail_v / r["R26"]
    determinant = g_s * g_b - coupling * coupling
    sense = (source_s * g_b + coupling * source_b) / determinant
    bias = (g_s * source_b + coupling * source_s) / determinant
    return sense, bias


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive-v", type=float, required=True, help="FET-derived node at R15/R30/C3/C4")
    parser.add_argument("--q6-collector-v", type=float, required=True)
    parser.add_argument("--positive-rail-v", type=float, default=10.0)
    parser.add_argument("--negative-rail-v", type=float, default=-10.0)
    args = parser.parse_args()
    try:
        sense, bias = conditional_bias_v(
            args.drive_v, args.q6_collector_v, args.positive_rail_v, args.negative_rail_v
        )
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({
        "model": "conditional_resistive_Q5_sense_DC_only",
        "imposed_boundary_v": {
            "SCHMITT_DRIVE": args.drive_v,
            "SCHMITT_Q6_COLLECTOR": args.q6_collector_v,
            "POS10_V": args.positive_rail_v,
            "NEG10_V": args.negative_rail_v,
        },
        "q5_base_sense_v": sense,
        "reset_bias_v": bias,
        "predicts_threshold_hysteresis_or_reset_time": False,
        "excluded": ["Q5/Q6 currents and device choice", "Q10 loading", "FET gain", "C3/C4 dynamics", "rail movement"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
