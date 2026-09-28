"""SVC-9 Fig. 9-17 panel branches feeding board-4 pin 5/Q26 base.

J2 and SW15 always contribute a conductance. SW16/SW17 contribute only
when ON. Upstream source voltages and resistances remain imposed.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_cutoff_base_reference import conditional_q26_base


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_cutoff_base_network.json"


def _resistors() -> tuple[float, float, float, float]:
    p = json.loads(EVIDENCE.read_text(encoding="utf-8"))["parts"]
    actual = tuple(p[ref]["ohm"] for ref in ("R51", "R52", "R53", "R54"))
    states = (p["R51"]["jack_normal"], p["R52"]["switch_off"],
              p["R52"]["switch_on"], p["R53"]["switch_off"],
              p["R53"]["switch_on"], p["R54"]["switch_off"],
              p["R54"]["switch_on"])
    if actual != (100000, 33000, 300000, 150000) or states != (
            "GROUND", "GROUND", "FILTER_MOD_SOURCE", "OPEN", "KEYBOARD_CV",
            "OPEN", "KEYBOARD_CV"):
        raise ValueError("panel branch evidence differs from documented topology")
    return actual


def conditional_panel_q26_base(*, cutoff_fraction_from_neg10: float,
                               scale_active_ohm: float, contour_pin16_v: float,
                               external_control_v: float | None = None,
                               external_source_ohm: float = 0,
                               filter_mod_on: bool = False,
                               modulation_source_v: float | None = None,
                               modulation_source_ohm: float = 0,
                               keyboard_1_3_on: bool = False,
                               keyboard_2_3_on: bool = False,
                               keyboard_cv_v: float | None = None,
                               keyboard_source_ohm: float = 0,
                               q26_base_current_a: float = 0,
                               previous_base_v: float | None = None,
                               step_s: float | None = None) -> dict:
    """Compose all traced panel branches with the passive board-4 base node.

    ``None`` external voltage means J2 unplugged, normalled to ground.
    ``None`` mod/keyboard voltage is permitted only while its route is OFF.
    Zero upstream resistance represents an *imposed ideal* source boundary.
    """
    r51, r52, r53, r54 = _resistors()
    if not all(isinstance(x, bool) for x in
               (filter_mod_on, keyboard_1_3_on, keyboard_2_3_on)):
        raise ValueError("panel switch states must be bool")
    if (filter_mod_on and modulation_source_v is None) or (
            (keyboard_1_3_on or keyboard_2_3_on) and keyboard_cv_v is None):
        raise ValueError("active panel branches need imposed source voltages")
    for resistance in (external_source_ohm, modulation_source_ohm, keyboard_source_ohm):
        if not math.isfinite(resistance) or resistance < 0:
            raise ValueError("source resistances must be finite and nonnegative")
    for voltage in (external_control_v, modulation_source_v, keyboard_cv_v):
        if voltage is not None and not math.isfinite(voltage):
            raise ValueError("source voltages must be finite")

    keyboard_conductance_s = (int(keyboard_1_3_on) / r53
                              + int(keyboard_2_3_on) / r54)
    keyboard_parallel_ohm = (1 / keyboard_conductance_s
                             if keyboard_conductance_s else None)
    branches = [((0 if external_control_v is None else external_control_v),
                 r51 + (0 if external_control_v is None else external_source_ohm)),
                ((modulation_source_v if filter_mod_on else 0),
                 r52 + (modulation_source_ohm if filter_mod_on else 0))]
    if keyboard_parallel_ohm is not None:
        branches.append((keyboard_cv_v, keyboard_parallel_ohm + keyboard_source_ohm))
    base = conditional_q26_base(
        cutoff_fraction_from_neg10=cutoff_fraction_from_neg10,
        scale_active_ohm=scale_active_ohm, contour_pin16_v=contour_pin16_v,
        other_branches=tuple(branches), q26_base_current_a=q26_base_current_a,
        previous_base_v=previous_base_v, step_s=step_s)
    return base | {
        "j2_mode": "external" if external_control_v is not None else "normalled_ground",
        "sw15_mode": "modulation" if filter_mod_on else "ground",
        "sw16_keyboard_1_3_on": keyboard_1_3_on,
        "sw17_keyboard_2_3_on": keyboard_2_3_on,
        "keyboard_parallel_ohm": keyboard_parallel_ohm,
        "keyboard_total_source_ohm": (
            None if keyboard_parallel_ohm is None
            else keyboard_parallel_ohm + keyboard_source_ohm),
        "panel_switch_states_known": True,
        "upstream_source_voltages_imposed": True,
    }


if __name__ == "__main__":
    print(json.dumps(conditional_panel_q26_base(
        cutoff_fraction_from_neg10=0.5, scale_active_ohm=250,
        contour_pin16_v=0), indent=2))
