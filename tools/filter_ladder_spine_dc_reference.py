"""Conditional resistor-spine DC of board-4 ladder, SVC-9 Fig. 9-11.

Four signed tap withdrawals stand for attached active devices. This
reference does not infer those currents or complete ladder collector bias.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_bottom_bias_dc_reference import conditional_bottom_bias_dc


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_ladder_dc_spine.json"


def _spine() -> tuple[float, tuple[float, ...]]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parts = data["series_resistors_top_to_bottom"]
    refs = tuple(part["ref"] for part in parts)
    values = tuple(part["ohm"] for part in parts)
    if (data["schematic"]["figure"], data["parts_list"]["table"],
            data["positive_rail_v"], refs, values) != (
                "9-11", "7-8", 10, ("R4", "R16", "R32", "R41", "R52"),
                (220, 150, 150, 150, 150)):
        raise ValueError("ladder resistor spine differs from documentary source")
    for index, part in enumerate(parts):
        if part["between"] != data["nodes_top_to_bottom"][index:index + 2]:
            raise ValueError("ladder spine node order differs from documentary source")
    return data["positive_rail_v"], values


def conditional_spine_dc(*, bottom_v: float,
                         tap_withdrawals_a: tuple[float, float, float, float]) -> dict:
    """Resolve five resistor currents and four tap voltages for imposed loads.

    Tap withdrawals are signed positive leaving the spine, from top to
    bottom. ``bottom_injection_a`` is current through board-4 R52 entering
    BOTTOM; it can be negative for inconsistent/imposed boundary cases.
    """
    plus, resistances = _spine()
    if not math.isfinite(bottom_v) or len(tap_withdrawals_a) != 4 or not all(
            math.isfinite(current) for current in tap_withdrawals_a):
        raise ValueError("finite BOTTOM voltage and four finite tap currents required")
    total_ohm = sum(resistances)
    weights_ohm = tuple(sum(resistances[:index + 1]) for index in range(4))
    weighted_drop_v = sum(weight * current for weight, current in
                          zip(weights_ohm, tap_withdrawals_a))
    bottom_injection_a = (plus - bottom_v - weighted_drop_v) / total_ohm
    currents_bottom_up = [bottom_injection_a]
    for withdrawal in reversed(tap_withdrawals_a):
        currents_bottom_up.append(currents_bottom_up[-1] + withdrawal)
    currents_top_down = tuple(reversed(currents_bottom_up))
    tap_voltages = []
    voltage = plus
    for resistance, current in zip(resistances, currents_top_down):
        voltage -= resistance * current
        tap_voltages.append(voltage)
    tap_kcl = tuple(currents_top_down[i] - tap_withdrawals_a[i]
                    - currents_top_down[i + 1] for i in range(4))
    return {
        "bottom_injection_a": bottom_injection_a,
        "resistor_currents_top_to_bottom_a": currents_top_down,
        "tap_voltages_top_to_bottom_v": tuple(tap_voltages[:4]),
        "bottom_v_reconstructed": tap_voltages[4],
        "tap_kcl_residuals_a": tap_kcl,
        "bottom_voltage_residual_v": tap_voltages[4] - bottom_v,
        "total_spine_ohm": total_ohm,
        "tap_drop_weights_ohm": weights_ohm,
        "tap_withdrawals_a_imposed": tap_withdrawals_a,
        "active_tap_currents_known": False,
    }


def conditional_spine_bottom_dc(*, cutoff_inputs: dict,
                                is29_a: float, is30_a: float,
                                beta29: float, beta30: float,
                                r61_ohm: int,
                                r73_bottom_side_to_wiper_ohm: float,
                                tap_withdrawals_a: tuple[float, float, float, float]) -> dict:
    """Close resistor spine against the lower-pair DC model for chosen R61.

    The lower-pair base-current split is invariant to a common DC shift of
    both bases, so one algebraic probe obtains the base-current sum. Its
    intermediate voltages are not interpreted as a physical operating point.
    """
    plus, resistances = _spine()
    if len(tap_withdrawals_a) != 4 or not all(math.isfinite(x) for x in tap_withdrawals_a):
        raise ValueError("four finite imposed tap currents required")
    common = dict(cutoff_inputs=cutoff_inputs, is29_a=is29_a, is30_a=is30_a,
                  beta29=beta29, beta30=beta30, r61_ohm=r61_ohm,
                  r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm)
    probe = conditional_bottom_bias_dc(**common, ladder_bottom_injection_a=0)
    base_current_sum_a = probe["q29_base_current_a"] + probe["q30_base_current_a"]
    weighted_drop_v = sum(sum(resistances[:i + 1]) * current
                          for i, current in enumerate(tap_withdrawals_a))
    injection_a = (plus - weighted_drop_v + r61_ohm * base_current_sum_a) / (
        sum(resistances) + r61_ohm)
    lower = conditional_bottom_bias_dc(**common, ladder_bottom_injection_a=injection_a)
    spine = conditional_spine_dc(bottom_v=lower["bottom_v"],
                                 tap_withdrawals_a=tap_withdrawals_a)
    return {
        "bottom_injection_a": injection_a,
        "spine_lower_coupling_residual_a": injection_a - spine["bottom_injection_a"],
        "base_current_sum_shift_residual_a": (
            base_current_sum_a - lower["q29_base_current_a"]
            - lower["q30_base_current_a"]),
        "bottom_v": lower["bottom_v"],
        "tail_v": lower["tail_v"],
        "q28_forward_active_candidate": lower["q28_forward_active_candidate"],
        "bottom_inside_nominal_rails_candidate": lower["bottom_inside_nominal_rails_candidate"],
        "r61_ohm_selected": r61_ohm,
        "spine": spine,
        "lower": lower,
        "tap_withdrawals_imposed": True,
        "ladder_collector_bias_known": False,
    }


if __name__ == "__main__":
    cutoff_inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                           scale_active_ohm=250, contour_pin16_v=0),
                         range_fraction_from_ground=0.1, is26_a=1e-14,
                         is28_a=1e-14, beta26=100, beta28=100,
                         temperature_k=298.15)
    for r61 in (200, 200000):
        out = conditional_spine_bottom_dc(
            cutoff_inputs=cutoff_inputs, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100, r61_ohm=r61,
            r73_bottom_side_to_wiper_ohm=500,
            tap_withdrawals_a=(0, 0, 0, 0))
        print(json.dumps({"r61_ohm": r61, "bottom_injection_a": out["bottom_injection_a"],
                          "bottom_v": out["bottom_v"], "tail_v": out["tail_v"],
                          "q28_forward_active_candidate": out["q28_forward_active_candidate"]},
                         indent=2))
