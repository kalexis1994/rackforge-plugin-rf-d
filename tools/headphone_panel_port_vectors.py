"""Frozen C2_RIGHT→R77/R21/C19→J7 nonlinear panel boundary vectors."""

from __future__ import annotations

import json
import math

from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_diode_reference import diode_model_from_reference


def panel_vectors() -> dict:
    cases = []
    for name, temperature, dt, tip, ring in (
            ("loaded_bipolar", 300.0, 1/48000, 32, 32),
            ("open_sine", 300.0, 1/9600, None, None),
            ("cool_loaded", 285.0, 1/4800, 32, 32)):
        model = diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.7,
            temperature_k=temperature)
        parameters = dict(transistor_is_a=1e-14,
                          beta_forward=160, beta_reverse=5,
                          temperature_k=temperature, diode_model=model)
        old = initial_headphone_amp_state(**parameters)
        initial = {"node_v": list(old["node_v"]),
                   "capacitor_v": dict(old["capacitor_v"]),
                   "r21_wiper_v": 0.0}
        lower = 2000.0
        series = 1000.0 + 5000.0-lower
        steps = []
        wiper = 0.0
        for index in range(32):
            if name == "loaded_bipolar":
                source = (0.0 if index == 0 else 0.1 if index < 8
                          else 0.5 if index < 16 else -0.5 if index < 24
                          else 0.0)
            elif name == "open_sine":
                source = 0.5*math.sin(2*math.pi*100*(index+1)/9600)
            else:
                source = 0.5 if index < 12 else -0.5 if index < 24 else 0.0

            def evaluate(trial_wiper: float) -> tuple[float, dict, float]:
                candidate = nonlinear_headphone_amp_step(
                    previous_state=old, pin7_v=trial_wiper, dt_s=dt,
                    tip_load_ohm=tip, ring_load_ohm=ring, **parameters)
                current = 2.5e-6/dt*(candidate["capacitor_v"]["C19"]
                                       - old["capacitor_v"]["C19"])
                residual = ((trial_wiper-source)/series
                            +trial_wiper/lower+current)
                return residual, candidate, current

            for iteration in range(16):
                residual, candidate, current = evaluate(wiper)
                if abs(residual) < 1e-10:
                    break
                h = 1e-5
                derivative = ((evaluate(wiper+h)[0]-evaluate(wiper-h)[0])
                              /(2*h))
                direction = -residual/derivative
                for power in range(16):
                    trial_wiper = wiper+2.0**-power*direction
                    try:
                        trial_residual, _, _ = evaluate(trial_wiper)
                    except ValueError:
                        continue
                    if abs(trial_residual) < abs(residual):
                        wiper = trial_wiper
                        break
                else:
                    raise ValueError(f"panel line search: {name}/{index}")
            else:
                raise ValueError(f"panel budget: {name}/{index}")
            pin22 = source+(wiper-source)*1000.0/series
            steps.append({"c2_right_v": source, "board4_pin22_v": pin22,
                          "r21_wiper_v": wiper, "j7_v": candidate["j7_tip_v"],
                          "r77_current_a": (source-wiper)/series,
                          "c19_current_a": current,
                          "panel_kcl_residual_a": abs(residual),
                          "node_v": list(candidate["node_v"]),
                          "capacitor_v": dict(candidate["capacitor_v"])})
            old = candidate
        cases.append({"id": name, "dt_s": dt,
                      "r21_lower_ohm": lower,
                      "tip_load_ohm": tip, "ring_load_ohm": ring,
                      "parameters": {**parameters,
                                     "diode_model": {"is_a": model["is_a"],
                                                     "ideality": model["ideality"]}},
                      "initial": initial, "steps": steps})
    return {"schema": "rf-d/panel-board3-port-vectors/v1",
            "sources": ["SVC-9 Fig. 9-8 PDF p. 10",
                        "SVC-9 Fig. 9-17 PDF p. 19"],
            "method": "R77/R21 KCL with dynamic C19, independent Python board-3 solve and finite-difference outer Newton",
            "units": {"voltage": "V", "current": "A", "resistance": "ohm",
                      "time": "s", "temperature": "K"},
            "cases": cases,
            "interpretation": "Conditional numerical reference; C2_RIGHT imposed, no vintage measurement."}


if __name__ == "__main__":
    print(json.dumps(panel_vectors(), indent=2))
