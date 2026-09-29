"""Conditional semiconductor/temperature sensitivity of a BUS-to-J7 trace."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from headphone_transient_stress_reference import _scenario, reference_dc
from output_diode_reference import diode_model_from_reference


EVIDENCE = (Path(__file__).resolve().parents[1] / "evidence"
            / "headphone_transient_semiconductor_grid.json")


def semiconductor_grid(*, newton_max_iterations: int = 80,
                       line_search_max_halvings: int = 32,
                       linear_solver: str = "python") -> dict:
    assumption = _scenario()
    if (assumption["board3_beta_forward"] != 160
            or assumption["diode_forward_voltage_at_100ma_v"] != 0.7
            or assumption["temperature_k"] != 298.15):
        raise ValueError("headphone baseline assumption changed")
    panel = dict(
        r14_pin7_to_pin6_ohm=assumption["r14_pin7_to_pin6_ohm"],
        r73_bottom_side_to_wiper_ohm=assumption["r73_bottom_side_to_wiper_ohm"],
        r20_wiper_to_ground_ohm=assumption["r20_wiper_to_ground_ohm"],
        hi_load_ohm=assumption["hi_load_ohm"],
        lo_load_ohm=assumption["lo_load_ohm"],
        r21_wiper_to_ground_ohm=assumption["r21_wiper_to_ground_ohm"])
    cases = [(298.15, 298.15, beta, vf, "both")
             for beta, vf in itertools.product(
                 (80, 160, 300), (0.65, 0.7, 0.75))]
    for temp in (285.0, 315.0):
        cases.extend(((298.15, temp, 160, 0.7, "board3_only"),
                      (temp, 298.15, 160, 0.7, "board4_only"),
                      (temp, temp, 160, 0.7, "both")))
    rows = []
    grid_halvings_max = 0
    board4_bases = {}
    for board4_temp, board3_temp, beta, forward_v, scope in cases:
        source = assumption | {"temperature_k": board4_temp}
        if board4_temp not in board4_bases:
            board4_bases[board4_temp] = reference_dc(source)
        base = board4_bases[board4_temp].copy()
        base["temperature_k"] = board3_temp
        base["beta_forward"] = beta
        base["diode_model"] = diode_model_from_reference(
            ideality=assumption["diode_ideality"],
            forward_voltage_at_100ma_v=forward_v,
            temperature_k=board3_temp)
        state = initial_coupled_headphone_state(**base)
        samples = []
        worst_kcl = 0.0
        most_iterations = 0
        for n in range(1, 97):
            bus = 0.5*math.sin(2*math.pi*100*n/9600)
            state = nonlinear_coupled_headphone_step(
                **base, **panel, previous_state=state,
                bus_v=bus, dt_s=1/9600, sw18_on=True,
                tip_load_ohm=32, ring_load_ohm=32,
                linear_solver=linear_solver,
                newton_max_iterations=newton_max_iterations,
                line_search_max_halvings=line_search_max_halvings)
            samples.append((state["j7_tip_v"], state["r21_wiper_v"],
                            state["c2_right_v"]))
            worst_kcl = max(worst_kcl,
                            state["max_charge_kcl_residual_a"])
            most_iterations = max(most_iterations, state["iterations"])
            grid_halvings_max = max(grid_halvings_max,
                                   state["max_halvings_used"])
        j7 = [row[0] for row in samples]
        rows.append({
            "board4_temperature_k": board4_temp,
            "board3_temperature_k": board3_temp,
            "temperature_scope": scope,
            "board3_beta_forward": beta,
            "diode_forward_voltage_at_100ma_v": forward_v,
            "steps": len(samples),
            "j7_rms_v": math.sqrt(sum(v*v for v in j7)/len(j7)),
            "j7_max_abs_v": max(abs(v) for v in j7),
            "r21_max_abs_v": max(abs(row[1]) for row in samples),
            "c2_max_abs_v": max(abs(row[2]) for row in samples),
            "max_kcl_residual_a": worst_kcl,
            "max_newton_iterations": most_iterations})
    baseline = next(row for row in rows if
                    (row["board4_temperature_k"],
                     row["board3_temperature_k"], row["board3_beta_forward"],
                     row["diode_forward_voltage_at_100ma_v"])
                    == (298.15, 298.15, 160, 0.7))
    return {
        "scenario_count": len(rows),
        "total_steps": sum(row["steps"] for row in rows),
        "stimulus": {"bus_sine_hz": 100, "bus_amplitude_v": 0.5,
                     "duration_s": 0.01, "sample_rate_hz": 9600,
                     "sw18_on": True, "tip_ring_ohm": 32},
        "baseline_j7_rms_v": baseline["j7_rms_v"],
        "board3_grid_j7_rms_min_v": min(row["j7_rms_v"] for row in rows
                                        if row["board4_temperature_k"] == 298.15
                                        and row["board3_temperature_k"] == 298.15),
        "board3_grid_j7_rms_max_v": max(row["j7_rms_v"] for row in rows
                                        if row["board4_temperature_k"] == 298.15
                                        and row["board3_temperature_k"] == 298.15),
        "temperature_grid_j7_rms_min_v": min(row["j7_rms_v"] for row in rows
                                             if row["temperature_scope"] == "both"
                                             and row["board3_beta_forward"] == 160
                                             and row["diode_forward_voltage_at_100ma_v"] == 0.7),
        "temperature_grid_j7_rms_max_v": max(row["j7_rms_v"] for row in rows
                                             if row["temperature_scope"] == "both"
                                             and row["board3_beta_forward"] == 160
                                             and row["diode_forward_voltage_at_100ma_v"] == 0.7),
        "max_kcl_residual_a": max(row["max_kcl_residual_a"] for row in rows),
        "max_newton_iterations": max(row["max_newton_iterations"] for row in rows),
        "max_halvings_used": grid_halvings_max,
        "rows": rows,
        "interpretation": "One synthetic BUS cycle from DC, not steady-state or vintage measurements."}


if __name__ == "__main__":
    print(json.dumps(semiconductor_grid(), indent=2))
