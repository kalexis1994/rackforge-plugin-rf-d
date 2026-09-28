"""Conditional five-source ON mixer bus from SVC-9 Fig. 9-17 PDF p. 19.

Each source voltage is imposed. The current drawn by board-4 pin 4 is also an
imposed boundary; this reference does not model its C27/filter input or the
OFF switch network. Pot positions are electrical resistance fractions.
"""

from __future__ import annotations

import json
from pathlib import Path

from vco1_panel_level_reference import pot_series_admittance


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "evidence" / "mixer_panel_bus.json"
OSC1_PATH = ROOT / "evidence" / "vco1_panel_pulse_width.json"


def _sources() -> dict[str, dict[str, object]]:
    data = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    osc1 = json.loads(OSC1_PATH.read_text(encoding="utf-8"))
    if data["bus"] != "MIX_BUS_BOARD4_PIN4" or data["board_input_source"] != {
        "id": "SVC-9", "pdf_page": 13, "figure": "9-11", "board": 4,
        "pin": 4, "first_series_component": "C27",
    }:
        raise ValueError("mixer bus source or board-4 destination differs")
    expected = {
        "OSC1": ("SW9", "R6_PANEL", 25000, "R45_PANEL", 33000),
        "OSC2": ("SW11", "R7_PANEL", 25000, "R47_PANEL", 33000),
        "OSC3": ("SW13", "R8_PANEL", 25000, "R49_PANEL", 33000),
        "NOISE": ("SW12", "R10_PANEL", 25000, "R48_PANEL", 11000),
        "EXT": ("SW10", None, None, "R46_PANEL", 33000),
    }
    sources = {source["id"]: source for source in data["sources"]}
    if set(sources) != set(expected):
        raise ValueError("Fig. 9-17 requires three oscillators, noise and external input")
    for name, (switch, pot, pot_ohm, series, series_ohm) in expected.items():
        source = sources[name]
        if (source["switch"], source["pot"], source["pot_ohm"],
                source["series"], source["series_ohm"]) != (switch, pot, pot_ohm, series, series_ohm):
            raise ValueError(f"{name} panel path differs from Fig. 9-17")
    osc1_parts = {part["ref"]: part for part in osc1["parts"]}
    if osc1_parts["R6_PANEL"]["value_ohm"] != sources["OSC1"]["pot_ohm"]:
        raise ValueError("OSC1 R6 conflicts with the panel trace")
    if osc1_parts["R45_PANEL"]["value_ohm"] != sources["OSC1"]["series_ohm"]:
        raise ValueError("OSC1 R45 conflicts with the panel trace")
    return sources


def mixer_bus_coefficients(active: set[str], alpha: dict[str, float]) -> dict[str, object]:
    """Return bus voltage weights for ON sources and imposed board current.

    Positive board current leaves the bus through board 4. Alpha is required
    for each active pot source; EXT has no level pot in this panel network.
    """
    sources = _sources()
    if not active or not active <= sources.keys():
        raise ValueError("active must contain known ON sources")
    expected_alpha = active - {"EXT"}
    if set(alpha) != expected_alpha:
        raise ValueError("provide one electrical pot fraction per active pot source")
    branches = {}
    for name in sorted(active):
        source = sources[name]
        if source["pot"] is None:
            g = 1 / source["series_ohm"]
            branches[name] = {"source_to_bus_siemens": -g, "bus_self_siemens": g}
        else:
            matrix = pot_series_admittance(alpha[name], source["pot_ohm"], source["series_ohm"])
            branches[name] = {"source_to_bus_siemens": matrix[1][0],
                              "bus_self_siemens": matrix[1][1]}
    total_g = sum(branch["bus_self_siemens"] for branch in branches.values())
    return {
        "active_on_sources": sorted(active),
        "boundary_voltage_coefficients": {
            name: -branch["source_to_bus_siemens"] / total_g for name, branch in branches.items()
        },
        "board_current_to_bus_voltage_ohm": -1 / total_g,
        "bus_passive_thevenin_resistance_ohm": 1 / total_g,
        "branches": branches,
        "excluded": ["OFF switch network", "board-4 C27/filter input law", "source device impedances"],
    }


def solve_mixer_bus(boundary_voltage_v: dict[str, float], alpha: dict[str, float],
                    board_current_a: float = 0.0) -> dict[str, object]:
    reference = mixer_bus_coefficients(set(boundary_voltage_v), alpha)
    bus_v = sum(reference["boundary_voltage_coefficients"][name] * voltage
                for name, voltage in boundary_voltage_v.items())
    bus_v += reference["board_current_to_bus_voltage_ohm"] * board_current_a
    branch_currents = {
        name: branch["source_to_bus_siemens"] * boundary_voltage_v[name]
              + branch["bus_self_siemens"] * bus_v
        for name, branch in reference["branches"].items()
    }
    return {"bus_voltage_v": bus_v, "currents_leaving_bus_to_panel_a": branch_currents,
            "board_current_leaving_bus_a": board_current_a,
            "kcl_residual_a": sum(branch_currents.values()) + board_current_a,
            "reference": reference}


if __name__ == "__main__":
    active = {"OSC1", "OSC2", "OSC3", "NOISE", "EXT"}
    print(json.dumps(mixer_bus_coefficients(active, {name: 1.0 for name in active - {"EXT"}}), indent=2))
