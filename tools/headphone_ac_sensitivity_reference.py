"""324 conditional BUS-to-J7 AC scenarios across controls, loads and devices."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

from headphone_coupled_ac_reference import coupled_headphone_ac
from headphone_transient_stress_reference import _scenario, reference_dc
from output_diode_reference import diode_model_from_reference


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "headphone_ac_sensitivity_grid.json"


def sensitivity_grid() -> dict:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    grid = data["assumed_grid"]
    if (grid["frequency_hz"], grid["r21_wiper_to_ground_ohm"],
            grid["board3_beta_forward"],
            grid["diode_forward_voltage_at_100ma_v"],
            grid["tip_ring_ohm"], grid["sw18_on"]) != (
            [30, 100, 1000], [500, 2500, 4500], [80, 160, 300],
            [0.65, 0.7, 0.75], [None, 32], [False, True]):
        raise ValueError("headphone AC sensitivity grid changed")
    base = reference_dc(_scenario())
    if grid["temperature_k"] != base["temperature_k"]:
        raise ValueError("board-3 and board-4 temperature boundary differs")
    base["transistor_is_a"] = grid["board3_is_a"]
    base["beta_reverse"] = grid["board3_beta_reverse"]
    rows = []
    for frequency, r21, beta, vf, load, switch in itertools.product(
            grid["frequency_hz"], grid["r21_wiper_to_ground_ohm"],
            grid["board3_beta_forward"],
            grid["diode_forward_voltage_at_100ma_v"],
            grid["tip_ring_ohm"], grid["sw18_on"]):
        diode = diode_model_from_reference(
            ideality=grid["diode_ideality"],
            forward_voltage_at_100ma_v=vf,
            temperature_k=grid["temperature_k"])
        result = coupled_headphone_ac(
            **(base | {"beta_forward": beta, "diode_model": diode}),
            frequency_hz=frequency,
            r14_pin7_to_pin6_ohm=grid["r14_pin7_to_pin6_ohm"],
            r73_bottom_side_to_wiper_ohm=grid["r73_bottom_side_to_wiper_ohm"],
            r20_wiper_to_ground_ohm=grid["r20_wiper_to_ground_ohm"],
            hi_load_ohm=grid["hi_load_ohm"],
            lo_load_ohm=grid["lo_load_ohm"],
            r21_wiper_to_ground_ohm=r21,
            tip_load_ohm=load, ring_load_ohm=load,
            sw18_on=switch)
        rows.append({"frequency_hz": frequency,
                     "r21_wiper_to_ground_ohm": r21,
                     "board3_beta_forward": beta,
                     "diode_forward_voltage_at_100ma_v": vf,
                     "tip_ring_ohm": load, "sw18_on": switch,
                     "abs_j7_v_per_bus_v": abs(result["j7_tip_v_per_bus_v"]),
                     "abs_r21_v_per_bus_v": abs(result["r21_wiper_v_per_bus_v"]),
                     "abs_hi_v_per_bus_v": abs(result["j4_hi_v_per_bus_v"]),
                     "max_kcl_residual_a_per_bus_v": max(
                         result["max_upstream_kcl_residual_a_per_bus_v"],
                         result["max_amp_kcl_residual_a_per_pin7_v"])})
    envelopes = []
    for frequency, load in itertools.product(grid["frequency_hz"],
                                             grid["tip_ring_ohm"]):
        group = [row for row in rows if row["frequency_hz"] == frequency
                 and row["tip_ring_ohm"] == load]
        envelopes.append({"frequency_hz": frequency,
                          "tip_ring_ohm": load,
                          "min_abs_j7_v_per_bus_v": min(
                              row["abs_j7_v_per_bus_v"] for row in group),
                          "max_abs_j7_v_per_bus_v": max(
                              row["abs_j7_v_per_bus_v"] for row in group),
                          "scenario_count": len(group)})
    return {"scenario_count": len(rows),
            "max_kcl_residual_a_per_bus_v": max(
                row["max_kcl_residual_a_per_bus_v"] for row in rows),
            "envelopes": envelopes, "rows": rows,
            "interpretation": "Conditional local AC derivative; no vintage population or audio measurement."}


if __name__ == "__main__":
    result = sensitivity_grid()
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
