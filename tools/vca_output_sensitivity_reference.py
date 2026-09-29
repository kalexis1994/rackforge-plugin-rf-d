"""Scenario sweep of coupled VCA/output bias and loaded 100 Hz transfer."""

from __future__ import annotations

import json
from pathlib import Path

from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, conditional_ladder_ebers_moll_dc)
from filter_recovery_active_dc_reference import (
    DEVICES as RECOVERY_DEVICES, conditional_recovery_dc)
from filter_vca_output_small_signal_reference import filter_with_output
from vca_cascaded_output_dc_reference import (
    DEVICE_NAMES, conditional_cascaded_output_dc)


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "vca_output_sensitivity_grid.json"


def sensitivity_grid() -> dict:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    documented, scenario = data["documented_grid"], data["assumed_grid"]
    if (documented["second_balance_left_ohm"],
            scenario["q17_is_ratio_to_other_bjt"],
            scenario["q17_beta_forward"],
            scenario["main_load_ohm"]) != (
            [0, 50, 100], [0.5, 1, 2], [50, 100, 200],
            [1000, 10000, 100000]):
        raise ValueError("output sensitivity grid differs from declared scenarios")
    is_base = scenario["all_other_is_a"]
    bf_base = scenario["all_other_beta_forward"]
    br = scenario["all_beta_reverse"]
    temp = scenario["temperature_k"]
    recovery = conditional_recovery_dc(
        is_a={n: is_base for n in RECOVERY_DEVICES},
        beta_forward={n: bf_base for n in RECOVERY_DEVICES},
        beta_reverse={n: br for n in RECOVERY_DEVICES},
        temperature_k=temp)
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250, contour_pin16_v=0),
                  range_fraction_from_ground=0.1,
                  is26_a=is_base, is28_a=is_base,
                  beta26=bf_base, beta28=bf_base,
                  temperature_k=temp)
    r73 = scenario["r73_bottom_side_to_wiper_ohm"]
    ladder = conditional_ladder_ebers_moll_dc(
        cutoff_inputs=cutoff, is29_a=is_base, is30_a=is_base,
        beta29=bf_base, beta30=bf_base,
        upper_is_a={n: is_base for n in UPPER},
        upper_beta={n: bf_base for n in UPPER},
        reverse_beta={n: br for n in DEVICE_NODES},
        r61_ohm=scenario["r61_ohm_schematic_candidate"],
        r73_bottom_side_to_wiper_ohm=r73)
    rows = []
    for balance in documented["second_balance_left_ohm"]:
        for ratio in scenario["q17_is_ratio_to_other_bjt"]:
            for beta17 in scenario["q17_beta_forward"]:
                values_is = {n: is_base for n in DEVICE_NAMES}
                values_is["Q17"] *= ratio
                values_bf = {n: bf_base for n in DEVICE_NAMES}
                values_bf["Q17"] = beta17
                dc = conditional_cascaded_output_dc(
                    first_loudness_v=scenario["first_loudness_v"],
                    second_loudness_base_v=scenario["second_loudness_base_v"],
                    first_balance_left_ohm=scenario["first_balance_left_ohm"],
                    second_balance_left_ohm=balance,
                    is_a=values_is, beta_forward=values_bf,
                    beta_reverse={n: br for n in DEVICE_NAMES},
                    temperature_k=temp)
                for main_load in scenario["main_load_ohm"]:
                    ac = filter_with_output(
                        ladder_dc=ladder, recovery_dc=recovery,
                        cascaded_output_dc=dc,
                        frequency_hz=scenario["frequency_hz"],
                        r14_pin7_to_pin6_ohm=scenario[
                            "r14_pin7_to_pin6_ohm"],
                        r73_bottom_side_to_wiper_ohm=r73,
                        main_load_ohm=main_load,
                        headphone_input_ohm=scenario[
                            "headphone_input_ohm"])
                    rows.append({
                        "second_balance_left_ohm": balance,
                        "q17_is_ratio": ratio,
                        "q17_beta_forward": beta17,
                        "main_load_ohm": main_load,
                        "q17_collector_dc_v": dc["q17_collector_output_v"],
                        "q1_base_dc_v": dc["nodes_v"]["Q1_BASE"],
                        "main_pin21_magnitude_v_per_bus_v": abs(ac[
                            "main_pin21_v_per_bus_v"]),
                        "max_dc_kcl_residual_a": dc[
                            "max_kcl_residual_a"],
                        "max_ac_kcl_residual_a_per_v": ac[
                            "max_linear_kcl_residual_a_per_bus_v"],
                    })
    metric = "main_pin21_magnitude_v_per_bus_v"
    return {
        "scenario_count": len(rows), "rows": rows,
        "minimum": min(rows, key=lambda row: row[metric]),
        "maximum": max(rows, key=lambda row: row[metric]),
        "max_dc_kcl_residual_a": max(
            row["max_dc_kcl_residual_a"] for row in rows),
        "max_ac_kcl_residual_a_per_v": max(
            row["max_ac_kcl_residual_a_per_v"] for row in rows),
        "parameter_distribution_assumed": False,
    }


if __name__ == "__main__":
    result = sensitivity_grid()
    print(json.dumps({key: value for key, value in result.items()
                      if key != "rows"}, indent=2))
