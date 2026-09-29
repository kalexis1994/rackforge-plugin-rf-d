"""Compare 62-node implicit transient at three steps for the same BUS sine."""

from __future__ import annotations

import json
import math
from pathlib import Path

from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from headphone_transient_stress_reference import _scenario, reference_dc


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "headphone_transient_dt_convergence.json"


def convergence_grid() -> dict:
    config = json.loads(EVIDENCE.read_text(encoding="utf-8"))["scenario"]
    if (config["frequency_hz"] != 100
            or config["bus_amplitude_v"] != 0.5
            or config["duration_s"] != 0.02
            or config["sample_rates_hz"] != [4800, 9600, 19200]
            or config["tip_ring_ohm"] != 32
            or config["sw18_on"] is not True):
        raise ValueError("time-step convergence scenario changed")
    base = reference_dc(_scenario())
    panel = dict(r20_wiper_to_ground_ohm=config["r20_wiper_to_ground_ohm"],
                 r21_wiper_to_ground_ohm=config["r21_wiper_to_ground_ohm"],
                 hi_load_ohm=config["hi_load_ohm"],
                 lo_load_ohm=config["lo_load_ohm"],
                 r14_pin7_to_pin6_ohm=config["r14_pin7_to_pin6_ohm"],
                 r73_bottom_side_to_wiper_ohm=config["r73_bottom_side_to_wiper_ohm"])
    traces = {}
    residual_max = 0.0
    iteration_max = 0
    for rate in config["sample_rates_hz"]:
        state = initial_coupled_headphone_state(**base)
        trace = []
        step_count = round(config["duration_s"]*rate)
        for n in range(1, step_count+1):
            t = n/rate
            bus = config["bus_amplitude_v"]*math.sin(
                2*math.pi*config["frequency_hz"]*t)
            state = nonlinear_coupled_headphone_step(
                **base, **panel, previous_state=state,
                bus_v=bus, dt_s=1/rate,
                tip_load_ohm=config["tip_ring_ohm"],
                ring_load_ohm=config["tip_ring_ohm"],
                sw18_on=True)
            trace.append((state["j7_tip_v"], state["r21_wiper_v"],
                          state["c2_right_v"]))
            residual_max = max(residual_max, state["max_charge_kcl_residual_a"])
            iteration_max = max(iteration_max, state["iterations"])
        traces[rate] = trace

    def compare(coarse_rate: int, fine_rate: int) -> dict:
        coarse, fine = traces[coarse_rate], traces[fine_rate]
        ratio = fine_rate//coarse_rate
        if fine_rate != 2*coarse_rate or len(fine) != ratio*len(coarse):
            raise ValueError("rates or physical windows cannot be aligned")
        names = ("j7_v", "r21_wiper_v", "c2_right_v")
        return {name: {
            "max_abs_error_v": max(abs(a[index]-fine[ratio*(n+1)-1][index])
                                   for n, a in enumerate(coarse)),
            "rms_error_v": math.sqrt(sum(
                (a[index]-fine[ratio*(n+1)-1][index])**2
                for n, a in enumerate(coarse))/len(coarse))}
            for index, name in enumerate(names)}

    low = compare(4800, 9600)
    high = compare(9600, 19200)
    return {"sample_counts": {str(rate): len(trace) for rate, trace in traces.items()},
            "total_steps": sum(len(trace) for trace in traces.values()),
            "max_kcl_residual_a": residual_max,
            "max_newton_iterations": iteration_max,
            "coarse_to_medium": low,
            "medium_to_fine": high,
            "max_error_ratios": {name: low[name]["max_abs_error_v"]
                                 / high[name]["max_abs_error_v"]
                                 for name in low},
            "interpretation": "Two physical cycles, three implicit-Euler steps; numerical convergence only."}


if __name__ == "__main__":
    print(json.dumps(convergence_grid(), indent=2))
