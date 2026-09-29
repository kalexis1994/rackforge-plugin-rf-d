"""Matched 62-node traces with hybrid and full numerical Jacobians."""

from __future__ import annotations

import json
import math
from pathlib import Path
from time import perf_counter

from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from headphone_transient_stress_reference import _scenario, reference_dc


EVIDENCE = (Path(__file__).resolve().parents[1] / "evidence"
            / "headphone_jacobian_trace_comparison.json")


def compare_traces() -> dict:
    scenario = _scenario()
    base = reference_dc(scenario)
    panel = dict(
        r14_pin7_to_pin6_ohm=scenario["r14_pin7_to_pin6_ohm"],
        r73_bottom_side_to_wiper_ohm=scenario["r73_bottom_side_to_wiper_ohm"],
        r20_wiper_to_ground_ohm=scenario["r20_wiper_to_ground_ohm"],
        hi_load_ohm=scenario["hi_load_ohm"],
        lo_load_ohm=scenario["lo_load_ohm"],
        r21_wiper_to_ground_ohm=scenario["r21_wiper_to_ground_ohm"])
    rows = []
    for peak, dt, load in ((0.1, 1/48000, None),
                           (0.1, 1/96000, 32),
                           (1.0, 1/48000, 32),
                           (1.0, 1/96000, None)):
        states = {method: initial_coupled_headphone_state(**base)
                  for method in ("hybrid", "finite_difference")}
        elapsed = {method: 0.0 for method in states}
        worst_node = worst_j7 = worst_kcl = 0.0
        max_iterations = {method: 0 for method in states}
        for index in range(24):
            # Same bipolar BUS waveform and SW18/load changes for both paths.
            bus = (peak*min(index/5, 1) if index < 8 else
                   -peak if index < 16 else 0.0)
            switch = index < 8 or index >= 16
            applied_load = load if index < 12 else (None if load else 32)
            for method in states:
                start = perf_counter()
                states[method] = nonlinear_coupled_headphone_step(
                    **base, **panel, previous_state=states[method],
                    bus_v=bus, dt_s=dt, sw18_on=switch,
                    tip_load_ohm=applied_load,
                    ring_load_ohm=applied_load,
                    jacobian_method=method)
                elapsed[method] += perf_counter()-start
                max_iterations[method] = max(
                    max_iterations[method], states[method]["iterations"])
                worst_kcl = max(worst_kcl,
                                states[method]["max_charge_kcl_residual_a"])
            hybrid, numeric = states["hybrid"], states["finite_difference"]
            worst_node = max(worst_node, *(abs(a-b) for a, b in zip(
                hybrid["node_v"], numeric["node_v"])))
            worst_j7 = max(worst_j7,
                           abs(hybrid["j7_tip_v"]-numeric["j7_tip_v"]))
        if not all(math.isfinite(value) for value in (
                worst_node, worst_j7, worst_kcl, *elapsed.values())):
            raise ValueError("nonfinite comparison")
        rows.append({"bus_peak_v": peak, "dt_s": dt,
                     "initial_tip_ring_ohm": load, "steps": 24,
                     "max_node_difference_v": worst_node,
                     "max_j7_difference_v": worst_j7,
                     "max_kcl_residual_a": worst_kcl,
                     "max_newton_iterations": max_iterations,
                     "elapsed_s": elapsed})
    return {"scenario_count": len(rows),
            "step_count_per_method": sum(row["steps"] for row in rows),
            "max_node_difference_v": max(row["max_node_difference_v"]
                                         for row in rows),
            "max_j7_difference_v": max(row["max_j7_difference_v"]
                                       for row in rows),
            "max_kcl_residual_a": max(row["max_kcl_residual_a"]
                                      for row in rows),
            "elapsed_s": {method: sum(row["elapsed_s"][method] for row in rows)
                          for method in ("hybrid", "finite_difference")},
            "rows": rows}


if __name__ == "__main__":
    print(json.dumps(compare_traces(), indent=2))
