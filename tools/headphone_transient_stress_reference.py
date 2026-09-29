"""Reproducible 16-scenario numerical stress of the 62-node lab oracle."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from time import perf_counter

from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
from filter_recovery_active_dc_reference import DEVICES as RECOVERY_DEVICES, conditional_recovery_dc
from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from output_diode_reference import diode_model_from_reference
from vca_cascaded_output_dc_reference import DEVICE_NAMES, conditional_cascaded_output_dc


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "headphone_transient_stress_grid.json"


def _scenario() -> dict:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    grid = data["assumed_grid"]
    if (grid["bus_peak_v"] != [0.1, 1.0]
            or grid["dt_s"] != [1/48000, 1/96000]
            or grid["sw18_on"] != [False, True]
            or grid["tip_ring_ohm"] != [None, 32]
            or grid["steps_per_scenario"] != 16):
        raise ValueError("transient stress grid differs from declared scenarios")
    return grid


def reference_dc(scenario: dict) -> dict:
    """Common imposed board-4 DC condition for headphone experiments."""
    is_a = scenario["board4_is_a"]
    beta = scenario["board4_beta_forward"]
    reverse = scenario["board4_beta_reverse"]
    temp = scenario["temperature_k"]
    recovery = conditional_recovery_dc(
        is_a={n: is_a for n in RECOVERY_DEVICES},
        beta_forward={n: beta for n in RECOVERY_DEVICES},
        beta_reverse={n: reverse for n in RECOVERY_DEVICES},
        temperature_k=temp)
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250,
                                    contour_pin16_v=0),
                  range_fraction_from_ground=0.1,
                  is26_a=is_a, is28_a=is_a, beta26=beta, beta28=beta,
                  temperature_k=temp)
    ladder = conditional_ladder_ebers_moll_dc(
        cutoff_inputs=cutoff, is29_a=is_a, is30_a=is_a,
        beta29=beta, beta30=beta,
        upper_is_a={n: is_a for n in UPPER},
        upper_beta={n: beta for n in UPPER},
        reverse_beta={n: reverse for n in DEVICE_NODES},
        r61_ohm=scenario["r61_ohm_schematic_candidate"],
        r73_bottom_side_to_wiper_ohm=scenario["r73_bottom_side_to_wiper_ohm"])
    output = conditional_cascaded_output_dc(
        first_loudness_v=scenario["first_loudness_v"],
        second_loudness_base_v=scenario["second_loudness_base_v"],
        first_balance_left_ohm=scenario["first_balance_left_ohm"],
        second_balance_left_ohm=scenario["second_balance_left_ohm"],
        is_a={n: is_a for n in DEVICE_NAMES},
        beta_forward={n: beta for n in DEVICE_NAMES},
        beta_reverse={n: reverse for n in DEVICE_NAMES},
        temperature_k=temp)
    diode = diode_model_from_reference(
        ideality=scenario["diode_ideality"],
        forward_voltage_at_100ma_v=scenario["diode_forward_voltage_at_100ma_v"],
        temperature_k=temp)
    base = dict(ladder_dc=ladder, recovery_dc=recovery,
                cascaded_output_dc=output,
                transistor_is_a=scenario["board3_is_a"],
                beta_forward=scenario["board3_beta_forward"],
                beta_reverse=scenario["board3_beta_reverse"],
                temperature_k=temp, diode_model=diode)
    return base


def stress_grid(*, newton_max_iterations: int = 80,
                line_search_max_halvings: int = 32,
                linear_solver: str = "python") -> dict:
    scenario = _scenario()
    base = reference_dc(scenario)
    panel = dict(r14_pin7_to_pin6_ohm=scenario["r14_pin7_to_pin6_ohm"],
                 r73_bottom_side_to_wiper_ohm=scenario["r73_bottom_side_to_wiper_ohm"],
                 r20_wiper_to_ground_ohm=scenario["r20_wiper_to_ground_ohm"],
                 hi_load_ohm=scenario["hi_load_ohm"],
                 lo_load_ohm=scenario["lo_load_ohm"],
                 r21_wiper_to_ground_ohm=scenario["r21_wiper_to_ground_ohm"])
    rows = []
    for peak, dt, switch, load in itertools.product(
            scenario["bus_peak_v"], scenario["dt_s"],
            scenario["sw18_on"], scenario["tip_ring_ohm"]):
        state = initial_coupled_headphone_state(**base)
        worst_kcl = 0.0
        max_iterations = 0
        max_halvings = 0
        max_j7 = 0.0
        start = perf_counter()
        for index in range(scenario["steps_per_scenario"]):
            bus = peak*min(index/7, 1)
            state = nonlinear_coupled_headphone_step(
                **base, **panel, previous_state=state,
                bus_v=bus, dt_s=dt,
                tip_load_ohm=load, ring_load_ohm=load,
                sw18_on=switch, linear_solver=linear_solver,
                newton_max_iterations=newton_max_iterations,
                line_search_max_halvings=line_search_max_halvings)
            worst_kcl = max(worst_kcl, state["max_charge_kcl_residual_a"])
            max_iterations = max(max_iterations, state["iterations"])
            max_halvings = max(max_halvings, state["max_halvings_used"])
            max_j7 = max(max_j7, abs(state["j7_tip_v"]))
            if not all(math.isfinite(value) for value in state["node_v"]):
                raise ValueError("nonfinite transient state")
        elapsed = perf_counter()-start
        rows.append({"bus_peak_v": peak, "dt_s": dt,
                     "sw18_on": switch, "tip_ring_ohm": load,
                     "steps": scenario["steps_per_scenario"],
                     "max_kcl_residual_a": worst_kcl,
                     "max_newton_iterations": max_iterations,
                     "max_halvings_used": max_halvings,
                     "max_abs_j7_v": max_j7,
                     "elapsed_s": elapsed,
                     "mean_step_s": elapsed/scenario["steps_per_scenario"]})
    return {"scenario_count": len(rows), "step_count": sum(r["steps"] for r in rows),
            "max_kcl_residual_a": max(r["max_kcl_residual_a"] for r in rows),
            "max_newton_iterations": max(r["max_newton_iterations"] for r in rows),
            "max_halvings_used": max(r["max_halvings_used"] for r in rows),
            "total_elapsed_s": sum(r["elapsed_s"] for r in rows),
            "rows": rows,
            "interpretation": "Numerical stress only; timing is host-dependent and no vintage audio is measured."}


if __name__ == "__main__":
    print(json.dumps(stress_grid(), indent=2))
