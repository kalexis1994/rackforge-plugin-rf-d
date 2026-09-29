"""Independent 2D Newton oracle for imposed Q17c→C2→main/R77/J7."""

from __future__ import annotations

import json
import math

from filter_panel_output_transient_reference import panel_load_reduction
from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_diode_reference import diode_model_from_reference


C2_F = 10e-6
C19_F = 2.5e-6
R75 = 1000.0
R77 = 1000.0
R21 = 5000.0


def generate_vectors() -> dict:
    cases = []
    for name, temperature, dt, load in (
            ("loaded_switch", 300.0, 1/48000, 32),
            ("open_sine", 300.0, 1/9600, None),
            ("cool_loaded", 285.0, 1/4800, 32)):
        diode = diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.7,
            temperature_k=temperature)
        p = dict(transistor_is_a=1e-14, beta_forward=160,
                 beta_reverse=5, temperature_k=temperature,
                 diode_model=diode)
        old_amp = initial_headphone_amp_state(**p)
        old_c2 = 5.0
        x = w = 0.0
        lower21 = 2000.0
        series = R77 + R21 - lower21
        r20_lower = 2500.0
        reduced = panel_load_reduction(
            r20_wiper_to_ground_ohm=r20_lower,
            hi_load_ohm=10000.0, lo_load_ohm=100000.0)
        initial = {"c2_right_v": x, "c2_capacitor_v": old_c2,
                   "r21_wiper_v": w, "amp_node_v": list(old_amp["node_v"]),
                   "amp_capacitor_v": dict(old_amp["capacitor_v"])}
        steps = []
        for index in range(32):
            if name == "loaded_switch":
                q17 = (5.0 if index == 0 else 5.1 if index < 8
                       else 5.5 if index < 16 else 4.5 if index < 24
                       else 5.0)
                sw18_on = index < 12 or index >= 24
            elif name == "open_sine":
                q17 = 5.0+0.5*math.sin(2*math.pi*100*(index+1)/9600)
                sw18_on = True
            else:
                q17 = 5.5 if index < 12 else 4.5 if index < 24 else 5.0
                sw18_on = True
            main_load = (reduced["equivalent_main_load_ohm"] if sw18_on
                         else 5000.0-r20_lower)

            def evaluate(candidate_x: float, candidate_w: float
                         ) -> tuple[float, float, dict, float]:
                amp = nonlinear_headphone_amp_step(
                    previous_state=old_amp, pin7_v=candidate_w,
                    dt_s=dt, tip_load_ohm=load,
                    ring_load_ohm=load, **p)
                i19 = C19_F/dt*(amp["capacitor_v"]["C19"]
                                - old_amp["capacitor_v"]["C19"])
                i2 = C2_F/dt*(q17-candidate_x-old_c2)
                fx = (candidate_x/(R75+main_load)
                      +(candidate_x-candidate_w)/series-i2)
                fw = ((candidate_w-candidate_x)/series
                      +candidate_w/lower21+i19)
                return fx, fw, amp, i19

            for iteration in range(16):
                fx, fw, amp, i19 = evaluate(x, w)
                error = max(abs(fx), abs(fw))
                if error < 1e-10:
                    break
                h = 1e-5
                i19_plus = evaluate(x, w+h)[3]
                i19_minus = evaluate(x, w-h)[3]
                di19_dw = (i19_plus-i19_minus)/(2*h)
                a = 1/(R75+main_load)+1/series+C2_F/dt
                b = -1/series
                c = -1/series
                d = 1/series+1/lower21+di19_dw
                det = a*d-b*c
                dx = (-fx*d+b*fw)/det
                dw = (c*fx-a*fw)/det
                for power in range(16):
                    trial_x = x+2.0**-power*dx
                    trial_w = w+2.0**-power*dw
                    try:
                        next_fx, next_fw, _, _ = evaluate(trial_x, trial_w)
                    except ValueError:
                        continue
                    if max(abs(next_fx), abs(next_fw)) < error:
                        x, w = trial_x, trial_w
                        break
                else:
                    raise ValueError(f"C2 line search failed: {name}/{index}")
            else:
                raise ValueError(f"C2 budget failed: {name}/{index}")
            pin21 = x*main_load/(R75+main_load)
            hi = pin21*reduced["hi_to_pin21_ratio"] if sw18_on else 0.0
            lo = hi*reduced["lo_to_hi_ratio"] if sw18_on else 0.0
            steps.append({
                "q17_collector_v": q17, "sw18_on": sw18_on,
                "c2_right_v": x, "c2_capacitor_v": q17-x,
                "board4_pin21_v": pin21, "j4_hi_v": hi, "j5_lo_v": lo,
                "r21_wiper_v": w, "j7_v": amp["j7_tip_v"],
                "c2_current_a": C2_F/dt*(q17-x-old_c2),
                "r75_current_a": x/(R75+main_load),
                "r77_current_a": (x-w)/series,
                "c2_right_kcl_residual_a": abs(fx),
                "r21_wiper_kcl_residual_a": abs(fw),
                "amp_node_v": list(amp["node_v"]),
                "amp_capacitor_v": dict(amp["capacitor_v"])})
            old_c2 = q17-x
            old_amp = amp
        cases.append({
            "id": name, "dt_s": dt, "tip_ring_load_ohm": load,
            "r20_lower_ohm": r20_lower, "r21_lower_ohm": lower21,
            "hi_load_ohm": 10000.0, "lo_load_ohm": 100000.0,
            "parameters": {**p, "diode_model": {
                "is_a": diode["is_a"], "ideality": diode["ideality"]}},
            "initial": initial, "steps": steps})
    return {
        "schema": "rf-d/c2-panel-board3-vectors/v1",
        "sources": ["SVC-9 Fig. 9-8 PDF p. 10",
                    "SVC-9 Fig. 9-11 PDF p. 13",
                    "SVC-9 Fig. 9-17 PDF p. 19"],
        "method": "15-node conditioned implicit Euler; 2D outer Newton with finite-difference C19 derivative and independent Python board-3 solve",
        "units": {"voltage": "V", "current": "A", "resistance": "ohm",
                  "time": "s", "temperature": "K"},
        "cases": cases,
        "interpretation": "Q17 collector imposed; no vintage measurement or full 62-node coupling."}


if __name__ == "__main__":
    print(json.dumps(generate_vectors(), indent=2))
