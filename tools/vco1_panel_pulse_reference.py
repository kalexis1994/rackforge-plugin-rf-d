"""Conditional source at 22B and load on 20B from Fig. 9-17 (SVC-9 p. 19).

The switch's mechanical position map, transistor currents, and R6 wiper load
are outside this passive calculation. Voltages use an imposed nominal -10 V.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "evidence" / "vco1_panel_pulse_width.json"
BOARD_PATH = ROOT / "evidence" / "vco1_ramp_graph.json"


def panel_pulse_reference(negative_rail_v: float = -10.0) -> dict[str, object]:
    panel = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    board = json.loads(BOARD_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in panel["parts"]}
    board_parts = {part["ref"]: part for part in board["parts"]}
    expected = {
        "R34_PANEL": (1500, {"GND", "SW6_11"}),
        "R33_PANEL": (1000, {"SW6_11", "SW6_12"}),
        "R32_PANEL": (7500, {"SW6_12", "NEG10_V"}),
        "R6_PANEL": (25000, {"R6_TOP", "GND"}),
        "R45_PANEL": (33000, {"R6_WIPER", "OSC1_ON_SWITCH"}),
    }
    for ref, (value, terminals) in expected.items():
        part = parts[ref]
        if part["value_ohm"] != value or set(part["terminals"]) != terminals:
            raise ValueError(f"{ref} does not match the traced Fig. 9-17 network")
    if panel["links"]["board_pulse_width"] != "22B" or panel["links"]["sw6_lower_common"] != 14:
        raise ValueError("SW6 lower common must feed board terminal 22B")
    if panel["sw6_lower_contacts"] != {
        "7": "NEG10_V", "8": "open", "9": "open", "10": "GND",
        "11": "SW6_11", "12": "SW6_12",
    }:
        raise ValueError("SW6 lower contact map differs from Fig. 9-17")
    if panel["links"]["sw6_upper_rectangular_contacts"] != [4, 5, 6]:
        raise ValueError("SW6 must route 20B through rectangular contacts")
    if board_parts["R1"]["terminals"]["a"] != "PULSE_WIDTH_22B":
        raise ValueError("board R1 must receive terminal 22B")
    if set(board_parts["R22"]["terminals"].values()) != {"GND", "RECT_OUTPUT_20B"}:
        raise ValueError("board R22 must load terminal 20B")

    r34, r33, r32 = (parts[ref]["value_ohm"] for ref in ("R34_PANEL", "R33_PANEL", "R32_PANEL"))
    total = r34 + r33 + r32
    contacts = {
        "7": {"voltage_v": negative_rail_v, "thevenin_ohm": 0.0},
        "8": {"voltage_v": None, "thevenin_ohm": None},
        "9": {"voltage_v": None, "thevenin_ohm": None},
        "10": {"voltage_v": 0.0, "thevenin_ohm": 0.0},
        "11": {"voltage_v": negative_rail_v * r34 / total,
               "thevenin_ohm": 1 / (1 / r34 + 1 / (r33 + r32))},
        "12": {"voltage_v": negative_rail_v * (r34 + r33) / total,
               "thevenin_ohm": 1 / (1 / (r34 + r33) + 1 / r32)},
    }
    r22, r13, r6 = board_parts["R22"]["value"], board_parts["R13"]["value"], parts["R6_PANEL"]["value_ohm"]
    loaded_to_ground = 1 / (1 / r22 + 1 / r6)
    return {
        "negative_rail_assumed_v": negative_rail_v,
        "sw6_lower_contact_sources_at_22b": contacts,
        "rect_20b_pulse_selected_r6_track_to_ground_ohm": loaded_to_ground,
        "rect_20b_coefficient_of_imposed_q12_collector": loaded_to_ground / (r13 + loaded_to_ground),
        "excluded": panel["limits"],
    }


if __name__ == "__main__":
    print(json.dumps(panel_pulse_reference(), indent=2))
