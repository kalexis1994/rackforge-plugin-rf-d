"""SW9-ON two-port of oscillator-1 R6 level pot and R45 panel resistor.

Source: SVC-9 Fig. 9-17 PDF p. 19; board-4 mixer input in Fig. 9-11 p. 13.
The selected waveform voltage and mixer-bus voltage are imposed. This passive
map does not solve the oscillator, C27 input network, or other mixer sources.
"""

from __future__ import annotations

import json
from pathlib import Path


PANEL_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_panel_pulse_width.json"


def _port_currents(source_v: float, mixer_v: float, alpha: float,
                   pot_ohm: float, series_ohm: float) -> tuple[float, float]:
    """Return currents entering the panel at source and mixer ports in amperes.

    alpha=0 puts the wiper at ground; alpha=1 puts it at the selected source.
    Endpoint cases are exact ideal contacts, avoiding division by zero.
    """
    if alpha == 0.0:
        return source_v / pot_ohm, mixer_v / series_ohm
    if alpha == 1.0:
        return source_v / pot_ohm + (source_v - mixer_v) / series_ohm, (mixer_v - source_v) / series_ohm
    r_top = (1 - alpha) * pot_ohm
    r_bottom = alpha * pot_ohm
    g_top, g_bottom, g_series = 1 / r_top, 1 / r_bottom, 1 / series_ohm
    wiper_v = (g_top * source_v + g_series * mixer_v) / (g_top + g_bottom + g_series)
    return (source_v - wiper_v) / r_top, (mixer_v - wiper_v) / series_ohm


def panel_level_reference(alpha: float) -> dict[str, object]:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    panel = json.loads(PANEL_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in panel["parts"]}
    r6 = parts["R6_PANEL"]
    r45 = parts["R45_PANEL"]
    if (r6["value_ohm"], set(r6["terminals"]), r6["kind"]) != (25000, {"R6_TOP", "GND"}, "potentiometer_total_track"):
        raise ValueError("R6 panel track differs from Fig. 9-17")
    if (r45["value_ohm"], set(r45["terminals"])) != (33000, {"R6_WIPER", "OSC1_ON_SWITCH"}):
        raise ValueError("R45 panel series path differs from Fig. 9-17")
    if panel["links"]["r6_wiper_next"] != "R45_PANEL" or panel["links"]["sw9_on_route"] != {
        "from": "OSC1_ON_SWITCH", "to": "MIX_BUS_BOARD4_PIN4"
    }:
        raise ValueError("SW9 ON must join R45 to the board-4 mixer bus")
    if panel["links"]["mixer_input_source"] != {
        "id": "SVC-9", "pdf_page": 13, "figure": "9-11", "board_pin": 4, "first_series_component": "C27"
    }:
        raise ValueError("mixer-bus destination differs from Fig. 9-11")
    pot, series = r6["value_ohm"], r45["value_ohm"]
    source_1, mixer_1 = _port_currents(1.0, 0.0, alpha, pot, series)
    source_2, mixer_2 = _port_currents(0.0, 1.0, alpha, pot, series)
    return {
        "wiper_fraction_from_ground": alpha,
        "r_top_ohm": (1 - alpha) * pot,
        "r_bottom_ohm": alpha * pot,
        "ports": ["SW6_SELECTED_OUTPUT", "MIX_BUS_BOARD4_PIN4"],
        "admittance_siemens": [[source_1, source_2], [mixer_1, mixer_2]],
        "selected_output_resistance_with_mixer_held_at_zero_ohm": 1 / source_1,
        "excluded": ["SW9 OFF", "board-4 C27 and active input impedance", "other mixer sources", "oscillator device currents"],
    }


if __name__ == "__main__":
    print(json.dumps([panel_level_reference(alpha) for alpha in (0.0, 0.25, 0.5, 0.75, 1.0)], indent=2))
