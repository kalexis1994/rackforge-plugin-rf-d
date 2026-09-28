"""Passive 9B/21B two-port through SW6 and R6, SVC-9 Fig. 9-17 p. 19.

Board transistor currents, R6 wiper/mixer loading and mechanical switch
legends are excluded. The port admittance matrices are for imposed 9B/21B
voltages, not waveform or audio predictions.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "evidence" / "vco1_panel_pulse_width.json"
BOARD_PATH = ROOT / "evidence" / "vco1_ramp_graph.json"
PORTS = ("SAW_OUTPUT_9B", "TRI_OUTPUT_21B")


def _port_currents(saw_v: float, tri_v: float, r30: float, r31: float,
                   r6: float, selected_contact: int) -> tuple[float, float]:
    g30, g31 = 1 / r30, 1 / r31
    tap_load = 1 / r6 if selected_contact == 2 else 0.0
    tap_v = (g30 * saw_v + g31 * tri_v) / (g30 + g31 + tap_load)
    saw_i = g30 * (saw_v - tap_v)
    tri_i = g31 * (tri_v - tap_v)
    if selected_contact == 3:
        saw_i += saw_v / r6
    elif selected_contact == 1:
        tri_i += tri_v / r6
    return saw_i, tri_i


def panel_waveform_reference() -> dict[str, object]:
    panel = json.loads(PANEL_PATH.read_text(encoding="utf-8"))
    board = json.loads(BOARD_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in panel["parts"]}
    board_parts = {part["ref"]: part for part in board["parts"]}
    expected = {
        "R30_PANEL": (47000, {"SAW_OUTPUT_9B", "SAW_TRI_TAP"}),
        "R31_PANEL": (10000, {"SAW_TRI_TAP", "TRI_OUTPUT_21B"}),
        "R6_PANEL": (25000, {"R6_TOP", "GND"}),
    }
    for ref, (resistance, terminals) in expected.items():
        part = parts[ref]
        if part["value_ohm"] != resistance or set(part["terminals"]) != terminals:
            raise ValueError(f"{ref} does not match Fig. 9-17")
    if panel["links"]["sw6_upper_common"] != "R6_TOP":
        raise ValueError("SW6 upper common must feed R6 top")
    if panel["links"]["sw6_upper_contacts"] != {
        "1": "TRI_OUTPUT_21B", "2": "SAW_TRI_TAP", "3": "SAW_OUTPUT_9B",
        "4": "RECT_OUTPUT_20B", "5": "RECT_OUTPUT_20B", "6": "RECT_OUTPUT_20B",
    }:
        raise ValueError("SW6 upper contact map differs from Fig. 9-17")
    if (panel["links"]["board_saw_output"], panel["links"]["board_triangle_output"]) != ("9B", "21B"):
        raise ValueError("board connections differ from Fig. 9-17")
    r23 = board_parts["R23"]
    if r23["value"] != 8200 or set(r23["terminals"].values()) != set(PORTS):
        raise ValueError("board R23 must bridge 9B and 21B")
    r30, r31, r6 = (parts[ref]["value_ohm"] for ref in ("R30_PANEL", "R31_PANEL", "R6_PANEL"))
    cases = {}
    for contact in range(1, 7):
        saw_1, tri_1 = _port_currents(1.0, 0.0, r30, r31, r6, contact)
        saw_2, tri_2 = _port_currents(0.0, 1.0, r30, r31, r6, contact)
        panel_y = [[saw_1, saw_2], [tri_1, tri_2]]
        bridge_g = 1 / r23["value"]
        board_r23_y = [[bridge_g, -bridge_g], [-bridge_g, bridge_g]]
        cases[str(contact)] = {
            "panel_admittance_siemens": panel_y,
            "panel_plus_board_r23_admittance_siemens": [
                [panel_y[i][j] + board_r23_y[i][j] for j in range(2)] for i in range(2)
            ],
        }
    return {
        "ports": PORTS,
        "panel_permanent_series_bridge_ohm": r30 + r31,
        "panel_plus_board_r23_parallel_bridge_ohm": 1 / (1 / (r30 + r31) + 1 / r23["value"]),
        "selected_contact_cases": cases,
        "excluded": panel["limits"],
    }


if __name__ == "__main__":
    print(json.dumps(panel_waveform_reference(), indent=2))
