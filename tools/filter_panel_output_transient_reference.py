"""Nonlinear output transient with exact resistive R20/HI/LO reduction.

SW18 is imposed ON. The two panel nodes have no capacitor, so eliminating
them into one equivalent main load preserves C2_RIGHT and all prior states.
"""

from __future__ import annotations

import math

from filter_panel_output_small_signal_reference import _panel_parts
from filter_vca_output_transient_reference import nonlinear_output_step


def panel_load_reduction(*, r20_wiper_to_ground_ohm: float,
                         hi_load_ohm: float,
                         lo_load_ohm: float) -> dict[str, float]:
    """R20/R57/R58 and jack loads as seen from board-4 pin 21."""
    if not all(math.isfinite(v) and v > 0 for v in
               (hi_load_ohm, lo_load_ohm)):
        raise ValueError("positive finite HI/LO jack loads required")
    r = _panel_parts()
    if (not math.isfinite(r20_wiper_to_ground_ohm)
            or not 0 <= r20_wiper_to_ground_ohm <= r["R20_PANEL"]):
        raise ValueError("electrical R20 segment in [0, 5000] ohm required")
    low_shunt = 1/(1/r["R58_PANEL"] + 1/lo_load_ohm)
    low_leg = r["R57_PANEL"] + low_shunt
    hi_shunt = 1/(1/hi_load_ohm + 1/low_leg)
    wiper_shunt = (0.0 if r20_wiper_to_ground_ohm == 0 else
                   1/(1/r20_wiper_to_ground_ohm + 1/hi_shunt))
    upper_segment = r["R20_PANEL"] - r20_wiper_to_ground_ohm
    equivalent_main = upper_segment + wiper_shunt
    return {"low_shunt_ohm": low_shunt,
            "low_leg_ohm": low_leg,
            "hi_shunt_ohm": hi_shunt,
            "wiper_shunt_ohm": wiper_shunt,
            "r20_upper_ohm": upper_segment,
            "equivalent_main_load_ohm": equivalent_main,
            "hi_to_pin21_ratio": wiper_shunt/equivalent_main,
            "lo_to_hi_ratio": low_shunt/low_leg}


def nonlinear_panel_output_step(*, r20_wiper_to_ground_ohm: float,
                                hi_load_ohm: float,
                                lo_load_ohm: float,
                                **output_step_parameters) -> dict:
    """One existing 48-node nonlinear step, then recover both panel jacks."""
    reduced = panel_load_reduction(
        r20_wiper_to_ground_ohm=r20_wiper_to_ground_ohm,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm)
    if "main_load_ohm" in output_step_parameters:
        raise ValueError("main load is derived from panel HI/LO loads")
    out = nonlinear_output_step(
        main_load_ohm=reduced["equivalent_main_load_ohm"],
        **output_step_parameters)
    pin21 = out["main_pin21_v"]
    hi = pin21*reduced["hi_to_pin21_ratio"]
    lo = hi*reduced["lo_to_hi_ratio"]
    r = _panel_parts()
    low_leg_current = (hi-lo)/r["R57_PANEL"]
    return {
        **out,
        "board4_pin21_v": pin21,
        "j4_hi_v": hi,
        "j5_lo_v": lo,
        "j4_hi_external_current_a": hi/hi_load_ohm,
        "j5_lo_external_current_a": lo/lo_load_ohm,
        "r57_current_a": low_leg_current,
        "r58_current_a": lo/r["R58_PANEL"],
        "r20_upper_current_a": (out["main_pin21_current_a"] if reduced["r20_upper_ohm"] == 0
                                else (pin21-hi)/reduced["r20_upper_ohm"]),
        "r20_lower_current_a": (out["main_pin21_current_a"] if r20_wiper_to_ground_ohm == 0
                                else hi/r20_wiper_to_ground_ohm),
        "panel_reduction": reduced,
        "sw18_on_imposed": True,
    }
