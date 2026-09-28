"""Documentary grid over R61, R73, R14 and C10 around conditional DC."""

from __future__ import annotations

import json
from pathlib import Path

from filter_emphasis_loop_small_signal_reference import coupled_emphasis_small_signal
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_emphasis_sensitivity_grid.json"


def sensitivity_grid() -> dict:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    grid = data["grid"]
    if (grid["frequency_hz"], grid["r61_ohm"],
            grid["r73_bottom_side_to_wiper_ohm"],
            grid["r14_pin7_to_pin6_ohm"], grid["c10_farads"]) != (
                [30, 100, 300], [200, 200000], [0, 500, 1000],
                [0, 25000, 50000], [9e-6, 10e-6, 15e-6]):
        raise ValueError("sensitivity grid differs from documented source scenarios")
    model = data["imposed_device_model"]
    is_a, bf, br, temp = (model["is_a_all_ladder_and_recovery_bjt"],
                          model["beta_forward_all"],
                          model["beta_reverse_all"], model["temperature_k"])
    recovery = conditional_recovery_dc(
        is_a={name: is_a for name in DEVICES},
        beta_forward={name: bf for name in DEVICES},
        beta_reverse={name: br for name in DEVICES}, temperature_k=temp)
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250, contour_pin16_v=0),
                  range_fraction_from_ground=0.1,
                  is26_a=is_a, is28_a=is_a, beta26=bf, beta28=bf,
                  temperature_k=temp)
    rows = []
    for r61 in grid["r61_ohm"]:
        for r73_left in grid["r73_bottom_side_to_wiper_ohm"]:
            ladder = conditional_ladder_ebers_moll_dc(
                cutoff_inputs=cutoff, is29_a=is_a, is30_a=is_a,
                beta29=bf, beta30=bf,
                upper_is_a={name: is_a for name in UPPER},
                upper_beta={name: bf for name in UPPER},
                reverse_beta={name: br for name in DEVICE_NODES},
                r61_ohm=r61, r73_bottom_side_to_wiper_ohm=r73_left)
            for frequency in grid["frequency_hz"]:
                for r14 in grid["r14_pin7_to_pin6_ohm"]:
                    for c10 in grid["c10_farads"]:
                        response = coupled_emphasis_small_signal(
                            ladder_dc=ladder, recovery_dc=recovery,
                            frequency_hz=frequency,
                            r14_pin7_to_pin6_ohm=r14,
                            r73_bottom_side_to_wiper_ohm=r73_left,
                            c10_farads=c10)
                        rows.append({
                            "r61_ohm": r61, "r73_left_ohm": r73_left,
                            "frequency_hz": frequency,
                            "r14_e_ohm": r14, "c10_farads": c10,
                            "tap_magnitude_v_per_v": abs(response[
                                "recovery_tap_v_per_bus_v"]),
                            "max_kcl_residual_a_per_v": response[
                                "max_linear_kcl_residual_a_per_bus_v"],
                        })
    summaries = []
    for r61 in grid["r61_ohm"]:
        for frequency in grid["frequency_hz"]:
            group = [row for row in rows
                     if row["r61_ohm"] == r61 and row["frequency_hz"] == frequency]
            summaries.append({
                "r61_ohm": r61, "frequency_hz": frequency,
                "minimum": min(group, key=lambda row: row["tap_magnitude_v_per_v"]),
                "maximum": max(group, key=lambda row: row["tap_magnitude_v_per_v"]),
            })
    return {"scenario_count": len(rows), "rows": rows,
            "summaries": summaries,
            "maximum_kcl_residual_a_per_v": max(
                row["max_kcl_residual_a_per_v"] for row in rows),
            "parameter_distribution_assumed": False}


if __name__ == "__main__":
    result = sensitivity_grid()
    print(json.dumps({key: value for key, value in result.items() if key != "rows"},
                     indent=2))
