"""Conditional 54-scenario sweep of both volume cursors and SW18 state."""

from __future__ import annotations

import json
from pathlib import Path

from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, conditional_ladder_ebers_moll_dc)
from filter_recovery_active_dc_reference import (
    DEVICES as RECOVERY_DEVICES, conditional_recovery_dc)
from filter_panel_headphone_reference import filter_with_panel_and_headphone
from vca_cascaded_output_dc_reference import (
    DEVICE_NAMES, conditional_cascaded_output_dc)


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "output_panel_sensitivity_grid.json"


def panel_sensitivity_grid() -> dict:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    scenario = data["assumed_grid"]
    if (data["documented_domains"],
            scenario["r20_wiper_to_ground_ohm"],
            scenario["r21_wiper_to_ground_ohm"],
            scenario["headphone_wiper_load_ohm"]) != (
            {"sw18_on": [False, True], "r20_total_ohm": 5000,
             "r21_total_ohm": 5000},
            [500, 2500, 4500], [500, 2500, 4500],
            [100, 32000, 1000000]):
        raise ValueError("panel sensitivity grid differs from declared scenarios")
    is_a, bf, br = (scenario["all_is_a"],
                    scenario["all_beta_forward"],
                    scenario["all_beta_reverse"])
    temp = scenario["temperature_k"]
    recovery = conditional_recovery_dc(
        is_a={n: is_a for n in RECOVERY_DEVICES},
        beta_forward={n: bf for n in RECOVERY_DEVICES},
        beta_reverse={n: br for n in RECOVERY_DEVICES},
        temperature_k=temp)
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250, contour_pin16_v=0),
                  range_fraction_from_ground=0.1,
                  is26_a=is_a, is28_a=is_a,
                  beta26=bf, beta28=bf, temperature_k=temp)
    ladder = conditional_ladder_ebers_moll_dc(
        cutoff_inputs=cutoff, is29_a=is_a, is30_a=is_a,
        beta29=bf, beta30=bf,
        upper_is_a={n: is_a for n in UPPER},
        upper_beta={n: bf for n in UPPER},
        reverse_beta={n: br for n in DEVICE_NODES},
        r61_ohm=scenario["r61_ohm_schematic_candidate"],
        r73_bottom_side_to_wiper_ohm=scenario[
            "r73_bottom_side_to_wiper_ohm"])
    dc = conditional_cascaded_output_dc(
        first_loudness_v=scenario["first_loudness_v"],
        second_loudness_base_v=scenario["second_loudness_base_v"],
        first_balance_left_ohm=scenario["first_balance_left_ohm"],
        second_balance_left_ohm=scenario["second_balance_left_ohm"],
        is_a={n: is_a for n in DEVICE_NAMES},
        beta_forward={n: bf for n in DEVICE_NAMES},
        beta_reverse={n: br for n in DEVICE_NAMES},
        temperature_k=temp)
    rows = []
    for sw18_on in data["documented_domains"]["sw18_on"]:
        for r20 in scenario["r20_wiper_to_ground_ohm"]:
            for r21 in scenario["r21_wiper_to_ground_ohm"]:
                for load in scenario["headphone_wiper_load_ohm"]:
                    ac = filter_with_panel_and_headphone(
                        ladder_dc=ladder, recovery_dc=recovery,
                        cascaded_output_dc=dc,
                        frequency_hz=scenario["frequency_hz"],
                        r14_pin7_to_pin6_ohm=scenario[
                            "r14_pin7_to_pin6_ohm"],
                        r73_bottom_side_to_wiper_ohm=scenario[
                            "r73_bottom_side_to_wiper_ohm"],
                        r20_wiper_to_ground_ohm=r20,
                        hi_load_ohm=scenario["hi_load_ohm"],
                        lo_load_ohm=scenario["lo_load_ohm"],
                        r21_wiper_to_ground_ohm=r21,
                        headphone_wiper_load_ohm=load,
                        sw18_on=sw18_on)
                    rows.append({
                        "sw18_on": sw18_on,
                        "r20_wiper_to_ground_ohm": r20,
                        "r21_wiper_to_ground_ohm": r21,
                        "headphone_wiper_load_ohm": load,
                        "hi_magnitude_v_per_bus_v": abs(
                            ac["j4_hi_v_per_bus_v"]),
                        "lo_magnitude_v_per_bus_v": abs(
                            ac["j5_lo_v_per_bus_v"]),
                        "r21_wiper_magnitude_v_per_bus_v": abs(
                            ac["r21_wiper_v_per_bus_v"]),
                        "c2_right_magnitude_v_per_bus_v": abs(
                            ac["c2_right_v_per_bus_v"]),
                        "max_ac_kcl_residual_a_per_v": ac[
                            "max_linear_kcl_residual_a_per_bus_v"],
                    })
    return {"scenario_count": len(rows), "rows": rows,
            "max_dc_kcl_residual_a": dc["max_kcl_residual_a"],
            "max_ac_kcl_residual_a_per_v": max(
                row["max_ac_kcl_residual_a_per_v"] for row in rows),
            "parameter_distribution_assumed": False}


if __name__ == "__main__":
    grid = panel_sensitivity_grid()
    for sw18 in (False, True):
        subset = [r for r in grid["rows"] if r["sw18_on"] == sw18]
        print(sw18, "HI", min(r["hi_magnitude_v_per_bus_v"] for r in subset),
              max(r["hi_magnitude_v_per_bus_v"] for r in subset),
              "R21", min(r["r21_wiper_magnitude_v_per_bus_v"] for r in subset),
              max(r["r21_wiper_magnitude_v_per_bus_v"] for r in subset))
    print("max AC residual", grid["max_ac_kcl_residual_a_per_v"])
