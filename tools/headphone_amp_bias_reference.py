"""Q16 base bias boundary before solving the board-3 active headphone stage."""

from __future__ import annotations

import json
import math
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "headphone_amp_active_board3.json"


def q16_base_bias(*, base_current_leaving_node_a: float = 0.0) -> dict[str, float]:
    """Exact resistive bias with C19 open at DC and imposed Q16 base current."""
    if not math.isfinite(base_current_leaving_node_a):
        raise ValueError("finite imposed base current required")
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    resistors = {row["ref"]: row["ohm"] for row in data["resistors"]}
    capacitors = {row["ref"]: row["farad"] for row in data["capacitors"]}
    rails = data["rails"]
    if (data["source"] != "SVC-9 Fig. 9-8 circuit 11 board 3 headphone amplifier, PDF p. 10 (SVC-204D PDF p. 66)"
            or resistors.get("R50") != 6200
            or resistors.get("R53") != 24000
            or capacitors.get("C19") != 2.5e-6
            or rails != {"BOARD3_PIN18": -10, "BOARD3_PIN21": -20,
                         "BOARD3_PINS9_10": 0}):
        raise ValueError("Q16 base bias differs from board-3 schematic")
    r50, r53 = resistors["R50"], resistors["R53"]
    negative_rail = rails["BOARD3_PIN18"]
    conductance = 1/r50+1/r53
    open_base_v = (negative_rail/r50)/conductance
    base_v = (negative_rail/r50-base_current_leaving_node_a)/conductance
    current_to_negative_rail_a = (base_v-negative_rail)/r50
    current_to_ground_a = base_v/r53
    return {"base_v": base_v,
            "open_base_v": open_base_v,
            "thevenin_resistance_ohm": 1/conductance,
            "current_to_negative_rail_a": current_to_negative_rail_a,
            "current_to_ground_a": current_to_ground_a,
            "base_current_leaving_node_a": base_current_leaving_node_a,
            "kcl_residual_a": abs(current_to_negative_rail_a
                                  + current_to_ground_a
                                  + base_current_leaving_node_a),
            "c19_dc_open": True}
