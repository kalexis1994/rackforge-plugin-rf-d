"""Open-loop passive regeneration return in SVC-9 Figs. 9-11 and 9-17.

RECOVERY_TAP is an imposed ideal voltage, BOTTOM is AC-grounded, and Q30
base current is zero for the frequency-domain transfer. These boundaries
deliberately exclude the active ladder loop and cannot predict resonance.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_regeneration_path.json"


def _values() -> tuple[float, float, float, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    p = data["parts"]
    values = (p["C10_BOARD4"]["farad"], p["R14_PANEL"]["total_ohm"],
              p["R73_BOARD4"]["total_ohm"], p["R76_BOARD4"]["ohm"])
    if (data["filter_schematic"]["figure"], data["panel_wiring"]["figure"],
            values) != ("9-11", "9-17", (10e-6, 50000, 1000, 330)):
        raise ValueError("regeneration source/value changed; recheck schematic and wiring")
    return values


def passive_return(*, frequency_hz: float, r14_pin7_to_pin6_ohm: float,
                   r73_bottom_side_to_wiper_ohm: float) -> dict:
    """Q30 base / ideal recovery-tap phasor for BOTTOM at AC ground.

    R14 is electrical resistance, not a knob position. R73 left segment is
    from R76/BOTTOM to Q30 base. All resistances are in ohms.
    """
    c10, r14_total, r73_total, r76 = _values()
    if (not math.isfinite(frequency_hz) or frequency_hz < 0
            or not math.isfinite(r14_pin7_to_pin6_ohm)
            or not 0 <= r14_pin7_to_pin6_ohm <= r14_total
            or not math.isfinite(r73_bottom_side_to_wiper_ohm)
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total):
        raise ValueError("frequency and both electrical resistance segments must be in range")
    r_bottom = r76 + r73_bottom_side_to_wiper_ohm
    r_top = r14_pin7_to_pin6_ohm + r73_total - r73_bottom_side_to_wiper_ohm
    total = r_top + r_bottom
    high_frequency_gain = r_bottom / total
    corner_hz = 1 / (2 * math.pi * c10 * total)
    if frequency_hz == 0:
        transfer = 0j
    else:
        s_c = 1j * 2 * math.pi * frequency_hz * c10
        transfer = s_c * r_bottom / (1 + s_c * total)
    return {
        "q30_base_per_recovery_tap": transfer,
        "magnitude": abs(transfer),
        "high_frequency_gain": high_frequency_gain,
        "conditional_corner_hz": corner_hz,
        "r_bottom_ohm": r_bottom,
        "r_top_ohm": r_top,
        "r14_pin7_to_pin6_ohm": r14_pin7_to_pin6_ohm,
        "r73_bottom_side_to_wiper_ohm": r73_bottom_side_to_wiper_ohm,
    }


if __name__ == "__main__":
    for r14 in (0, 25000, 50000):
        result = passive_return(frequency_hz=1000, r14_pin7_to_pin6_ohm=r14,
                                r73_bottom_side_to_wiper_ohm=500)
        print(f"R14 path {r14} ohm: magnitude={result['magnitude']:.6g}, "
              f"conditional corner={result['conditional_corner_hz']:.3f} Hz")
