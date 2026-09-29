"""Bipolar BUS steps, SW18 switching and loaded J7 over 384 lab samples."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from time import perf_counter

from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from headphone_transient_stress_reference import _scenario, reference_dc


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "headphone_transient_bipolar_grid.json"


def bipolar_stress() -> dict:
    config = json.loads(EVIDENCE.read_text(encoding="utf-8"))["scenario"]
    if (config["dt_s"] != [1/48000, 1/4800]
            or config["bus_segments"] != [[1.0, 32], [-1.0, 32],
                                          [1.0, 32], [-1.0, 32], [0.0, 64]]
            or config["sw18_segments"] != [[True, 64], [False, 64], [True, 64]]
            or config["tip_ring_ohm"] != [None, 32]):
        raise ValueError("bipolar stress scenarios changed")
    bus = [value for voltage, count in config["bus_segments"]
           for value in [voltage]*count]
    switches = [value for switch, count in config["sw18_segments"]
                for value in [switch]*count]
    if len(bus) != len(switches) or len(bus) != 192:
        raise ValueError("BUS and SW18 timelines differ")
    base = reference_dc(_scenario())
    panel = dict(r20_wiper_to_ground_ohm=config["r20_wiper_to_ground_ohm"],
                 r21_wiper_to_ground_ohm=config["r21_wiper_to_ground_ohm"],
                 hi_load_ohm=config["hi_load_ohm"],
                 lo_load_ohm=config["lo_load_ohm"],
                 r14_pin7_to_pin6_ohm=config["r14_pin7_to_pin6_ohm"],
                 r73_bottom_side_to_wiper_ohm=config["r73_bottom_side_to_wiper_ohm"])
    rows = []
    for dt, load in itertools.product(config["dt_s"],
                                      config["tip_ring_ohm"]):
        state = initial_coupled_headphone_state(**base)
        j7 = []
        kcl_max = 0.0
        iteration_max = 0
        off_hi_max = 0.0
        start = perf_counter()
        for bus_v, sw18_on in zip(bus, switches):
            state = nonlinear_coupled_headphone_step(
                **base, **panel, previous_state=state,
                bus_v=bus_v, dt_s=dt,
                tip_load_ohm=load, ring_load_ohm=load,
                sw18_on=sw18_on)
            j7.append(state["j7_tip_v"])
            kcl_max = max(kcl_max, state["max_charge_kcl_residual_a"])
            iteration_max = max(iteration_max, state["iterations"])
            if not sw18_on:
                off_hi_max = max(off_hi_max, abs(state["j4_hi_v"]),
                                 abs(state["j5_lo_v"]))
            if not all(math.isfinite(v) for v in state["node_v"]):
                raise ValueError("nonfinite bipolar transient state")
        rows.append({"dt_s": dt, "tip_ring_ohm": load, "steps": len(bus),
                     "min_j7_v": min(j7), "max_j7_v": max(j7),
                     "last_j7_v": j7[-1],
                     "max_kcl_residual_a": kcl_max,
                     "max_newton_iterations": iteration_max,
                     "max_off_hi_lo_v": off_hi_max,
                     "elapsed_s": perf_counter()-start})
    return {"scenario_count": len(rows),
            "step_count": len(bus)*len(rows),
            "rows": rows,
            "interpretation": "Numerical bipolar/switching stress only; no audio fidelity inference."}


if __name__ == "__main__":
    print(json.dumps(bipolar_stress(), indent=2))
