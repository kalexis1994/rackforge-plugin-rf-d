"""Conditional passive Q26 base node, SVC-9 Figs. 9-11 and 9-17.

The panel switch branches and transistor base current remain explicit
boundaries. This is a circuit reference, not a Model D cutoff calibration.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_cutoff_base_network.json"


def _values() -> tuple[float, float, float, float, float, float, float, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    p = data["parts"]
    values = (p["R11"]["ohm"], p["R55"]["ohm"], p["R74"]["ohm"],
              p["R49"]["ohm"], p["R70"]["ohm"], p["C18"]["farad"],
              data["rails_v"]["NEG10"], data["rails_v"]["POS10"])
    if (data["board4"]["figure"], data["panel"]["figure"], values,
            data["direct_connection"], p["R49"]["wiper"],
            p["R55"]["between"], p["R74"]["between"]) != (
                "9-11", "9-17", (5000, 200000, 47000, 500, 1800, 1e-10, -10, 10),
                ["PANEL_FILTER_CONT_IN", "BOARD4_PIN5_CONTROL_NODE", "CONTROL_BASE"],
                "CONTROL_BASE", ["CUTOFF_WIPER", "CONTROL_BASE"],
                ["BOARD4_PIN16_AMT_OF_CONTOUR", "CONTROL_BASE"]):
        raise ValueError("Q26 base evidence differs from documented topology")
    return values


def conditional_q26_base(*, cutoff_fraction_from_neg10: float,
                         scale_active_ohm: float, contour_pin16_v: float,
                         other_branches: tuple[tuple[float, float], ...] = (),
                         q26_base_current_a: float = 0,
                         previous_base_v: float | None = None,
                         step_s: float | None = None) -> dict:
    """Resolve CONTROL_BASE at DC or over one held-input C18 interval.

    Each other branch is (Thevenin voltage V, positive series resistance Ω).
    Q26 base current is signed positive when leaving CONTROL_BASE. For the
    existing infinite-beta Q26/Q28 model, set it to zero. ``step_s`` and
    ``previous_base_v`` must either both be supplied or both be omitted.
    """
    r11, r55, r74, r49, r70, c18, minus, plus = _values()
    if (not all(math.isfinite(x) for x in (cutoff_fraction_from_neg10,
                                          scale_active_ohm, contour_pin16_v,
                                          q26_base_current_a))
            or not 0 <= cutoff_fraction_from_neg10 <= 1
            or not 0 <= scale_active_ohm <= r49):
        raise ValueError("finite electrical cutoff/scale fractions and boundaries required")
    if (previous_base_v is None) != (step_s is None):
        raise ValueError("previous_base_v and step_s must be supplied together")
    if step_s is not None and (not math.isfinite(step_s) or step_s < 0
                               or not math.isfinite(previous_base_v)):
        raise ValueError("finite previous voltage and nonnegative step required")
    for voltage_v, resistance_ohm in other_branches:
        if not math.isfinite(voltage_v) or not math.isfinite(resistance_ohm) or resistance_ohm <= 0:
            raise ValueError("other branches need finite voltage and positive resistance")

    fraction = cutoff_fraction_from_neg10
    wiper_v = minus + (plus - minus) * fraction
    wiper_thevenin_ohm = r11 * fraction * (1 - fraction)
    knob_source_ohm = r55 + wiper_thevenin_ohm
    scale_ground_ohm = r70 + scale_active_ohm
    conductance_s = 1 / knob_source_ohm + 1 / r74 + 1 / scale_ground_ohm
    drive_a = wiper_v / knob_source_ohm + contour_pin16_v / r74 - q26_base_current_a
    for voltage_v, resistance_ohm in other_branches:
        conductance_s += 1 / resistance_ohm
        drive_a += voltage_v / resistance_ohm
    dc_v = drive_a / conductance_s
    time_constant_s = c18 / conductance_s
    base_v = (dc_v if step_s is None else
              dc_v + (previous_base_v - dc_v) * math.exp(-step_s / time_constant_s))
    branch_current_a = ((base_v - wiper_v) / knob_source_ohm
                        + (base_v - contour_pin16_v) / r74
                        + base_v / scale_ground_ohm + q26_base_current_a
                        + sum((base_v - voltage_v) / resistance_ohm
                              for voltage_v, resistance_ohm in other_branches))
    capacitor_current_a = 0 if step_s is None else -branch_current_a
    return {
        "q26_base_v": base_v,
        "dc_equilibrium_v": dc_v,
        "cutoff_wiper_thevenin_v": wiper_v,
        "cutoff_wiper_thevenin_ohm": wiper_thevenin_ohm,
        "cutoff_path_total_ohm": knob_source_ohm,
        "scale_to_ground_ohm": scale_ground_ohm,
        "node_conductance_s": conductance_s,
        "c18_time_constant_s": time_constant_s,
        "resistive_kcl_residual_a": branch_current_a,
        "c18_current_a": capacitor_current_a,
        "contour_pin16_v_imposed": contour_pin16_v,
        "q26_base_current_a_imposed": q26_base_current_a,
        "other_branches_imposed": len(other_branches),
        "panel_switch_states_known": False,
    }


if __name__ == "__main__":
    print(json.dumps(conditional_q26_base(cutoff_fraction_from_neg10=0.5,
                                          scale_active_ohm=250,
                                          contour_pin16_v=0), indent=2))
