"""Frozen isolated board-3 traces for the first native circuit slice."""

from __future__ import annotations

import json
import math
from pathlib import Path

from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_diode_reference import diode_model_from_reference


EVIDENCE = (Path(__file__).resolve().parents[1] / "evidence"
            / "headphone_board3_port_vectors.json")


def board3_vectors() -> dict:
    cases = []
    for name, temperature, dt_s, tip, ring, count in (
            ("loaded_bipolar", 300.0, 1/48000, 32, 32, 48),
            ("open_sine", 300.0, 1/9600, None, None, 96),
            ("cool_loaded", 285.0, 1/4800, 32, 32, 48)):
        model = diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.7,
            temperature_k=temperature)
        parameters = dict(transistor_is_a=1e-14,
                          beta_forward=160, beta_reverse=5,
                          temperature_k=temperature, diode_model=model)
        state = initial_headphone_amp_state(**parameters)
        initial = {"node_v": list(state["node_v"]),
                   "capacitor_v": dict(state["capacitor_v"])}
        steps = []
        for index in range(count):
            if name == "loaded_bipolar":
                pin7 = (0.0 if index == 0 else
                        0.01 if index < 8 else
                        0.1 if index < 16 else
                        1.0 if index < 24 else
                        -1.0 if index < 40 else 0.0)
            elif name == "open_sine":
                pin7 = 0.5*math.sin(2*math.pi*100*(index+1)/9600)
            else:
                pin7 = (1.0 if index < 16 else
                        -1.0 if index < 32 else 0.0)
            state = nonlinear_headphone_amp_step(
                previous_state=state, pin7_v=pin7, dt_s=dt_s,
                tip_load_ohm=tip, ring_load_ohm=ring, **parameters)
            steps.append({"pin7_v": pin7,
                          "node_v": list(state["node_v"]),
                          "capacitor_v": dict(state["capacitor_v"]),
                          "max_kcl_residual_a": state["max_charge_kcl_residual_a"],
                          "iterations": state["iterations"]})
        cases.append({"id": name, "dt_s": dt_s,
                      "tip_load_ohm": tip, "ring_load_ohm": ring,
                      "parameters": {**parameters,
                                     "diode_model": {"is_a": model["is_a"],
                                                     "ideality": model["ideality"]}},
                      "initial": initial, "steps": steps})
    return {"schema": "rf-d/board3-port-vectors/v1",
            "source": "SVC-9 Fig. 9-8 PDF p. 10; Fig. 9-17 PDF p. 19",
            "method": "12-node Ebers-Moll/Shockley implicit Euler, imposed pin 7",
            "node_order": ["Q16_BASE", "Q16_EMITTER_DIODE_TOP",
                           "DIODE_MIDDLE", "DIODE_BOTTOM", "Q11_BASE",
                           "Q11_COLLECTOR", "Q11_EMITTER", "Q10_BASE",
                           "Q10_COLLECTOR", "Q10_EMITTER",
                           "AMP_OUTPUT_BEFORE_C21", "J7_TIP_RING"],
            "units": {"voltage": "V", "time": "s", "current": "A",
                      "temperature": "K", "resistance": "ohm"},
            "cases": cases,
            "interpretation": "Conditional numerical reference; no vintage hardware measurement."}


if __name__ == "__main__":
    print(json.dumps(board3_vectors(), indent=2))
