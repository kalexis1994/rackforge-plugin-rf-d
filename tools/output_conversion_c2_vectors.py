"""Independent eight-variable board-4/C2/panel/board-3 transient oracle.

The three PNP bases are imposed. Newton differentiates the complete Python
residual numerically; it does not call the Rust port or its Schur tangent.
"""

from __future__ import annotations

import json
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_panel_output_transient_reference import panel_load_reduction
from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_diode_reference import diode_model_from_reference
from vca_output_conversion_dc_reference import (
    DEVICES, NODES, _evaluate, conditional_output_conversion_dc)


def generate_vectors() -> dict:
    cases = []
    for name, temperature, dt, jack_load in (
            ("nominal_switch", 298.15, 1 / 48000, 32.0),
            ("cool_open", 285.0, 1 / 9600, None)):
        diode = diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.7,
            temperature_k=temperature)
        semiconductor = dict(transistor_is_a=1e-14, beta_forward=160.0,
                             beta_reverse=5.0, temperature_k=temperature,
                             diode_model=diode)
        base = dict(q1_base_v=8.3, q12_base_v=7.75,
                    q17_base_v=7.75, plus_v=10.0)
        device = dict(is_a={n: 1e-14 for n in DEVICES},
                      beta_forward={n: 100.0 for n in DEVICES},
                      beta_reverse={n: 5.0 for n in DEVICES})
        dc = conditional_output_conversion_dc(
            **base, **device, temperature_k=temperature,
            diode_model=diode)
        old_amp = initial_headphone_amp_state(**semiconductor)
        old_c2 = dc["nodes_v"]["Q17_COLLECTOR"]
        x = [dc["nodes_v"][n] for n in NODES] + [0.0, 0.0]
        initial = {
            "conversion_node_v": x[:6], "c2_right_v": 0.0,
            "c2_capacitor_v": old_c2, "r21_wiper_v": 0.0,
            "amp_node_v": list(old_amp["node_v"]),
            "amp_capacitor_v": dict(old_amp["capacitor_v"])}
        reduction = panel_load_reduction(
            r20_wiper_to_ground_ohm=2500.0,
            hi_load_ohm=10000.0, lo_load_ohm=100000.0)
        steps = []
        for index in range(16):
            controls = dict(base)
            controls["q1_base_v"] += 0.008 if index >= 4 else 0.0
            controls["q12_base_v"] += -0.012 if index >= 8 else 0.0
            controls["q17_base_v"] += (0.018 if index < 4 else
                                         -0.025 if index < 8 else
                                         0.036 if index < 12 else 0.0)
            sw18_on = name == "cool_open" or index < 6 or index >= 11
            main = (reduction["equivalent_main_load_ohm"] if sw18_on
                    else 2500.0)
            r75_leg = 1000.0 + main
            r77_leg = 4000.0
            previous_amp = old_amp
            previous_c2 = old_c2

            def evaluate(y: list[float]) -> tuple[list[float], dict]:
                network = dict(dc["network_parameters"])
                network.update({k: controls[k] for k in base})
                stage, _ = _evaluate(y[:6], **network)
                amp = nonlinear_headphone_amp_step(
                    previous_state=previous_amp, pin7_v=y[7], dt_s=dt,
                    tip_load_ohm=jack_load, ring_load_ohm=jack_load,
                    **semiconductor)
                i19 = 2.5e-6 / dt * (
                    amp["capacitor_v"]["C19"]
                    - previous_amp["capacitor_v"]["C19"])
                i2 = 10e-6 / dt * (y[5] - y[6] - previous_c2)
                stage[5] -= i2  # Python stage convention: incoming minus outgoing.
                fx = y[6] / r75_leg + (y[6] - y[7]) / r77_leg - i2
                fw = (y[7] - y[6]) / r77_leg + y[7] / 2000.0 + i19
                return stage + [fx, fw], amp

            for iteration in range(20):
                residual, amp = evaluate(x)
                error = max(abs(v) for v in residual)
                if error < 1e-11:
                    break
                jacobian = [[0.0] * 8 for _ in range(8)]
                for col in range(8):
                    h = 1e-6
                    shifted = x.copy()
                    shifted[col] += h
                    high, _ = evaluate(shifted)
                    for row in range(8):
                        jacobian[row][col] = (high[row] - residual[row]) / h
                direction = _solve_linear(jacobian, [-v for v in residual])
                for power in range(20):
                    candidate = [v + 2.0 ** -power * dv
                                 for v, dv in zip(x, direction)]
                    try:
                        next_residual, _ = evaluate(candidate)
                    except (ValueError, OverflowError):
                        continue
                    if max(abs(v) for v in next_residual) < error:
                        x = candidate
                        break
                else:
                    raise ValueError(f"joint line search: {name}/{index}")
            else:
                raise ValueError(f"joint iteration budget: {name}/{index}")
            pin21 = x[6] * main / r75_leg
            hi = pin21 * reduction["hi_to_pin21_ratio"] if sw18_on else 0.0
            lo = hi * reduction["lo_to_hi_ratio"] if sw18_on else 0.0
            steps.append({
                "boundary": controls, "sw18_on": sw18_on,
                "conversion_node_v": x[:6], "c2_right_v": x[6],
                "c2_capacitor_v": x[5] - x[6], "r21_wiper_v": x[7],
                "board4_pin21_v": pin21, "j4_hi_v": hi, "j5_lo_v": lo,
                "j7_v": amp["j7_tip_v"],
                "c2_current_a": 10e-6 / dt * (x[5] - x[6] - old_c2),
                "max_kcl_residual_a": error,
                "amp_node_v": list(amp["node_v"]),
                "amp_capacitor_v": dict(amp["capacitor_v"])})
            old_c2 = x[5] - x[6]
            old_amp = amp
        cases.append({
            "id": name, "dt_s": dt, "tip_ring_load_ohm": jack_load,
            "conversion_parameters": {
                "is_a": 1e-14, "beta_forward": 100.0,
                "beta_reverse": 5.0, "temperature_k": temperature,
                "diode_model": {"is_a": diode["is_a"],
                                "ideality": diode["ideality"]}},
            "headphone_parameters": {
                "is_a": 1e-14, "beta_forward": 160.0,
                "beta_reverse": 5.0, "temperature_k": temperature,
                "diode_model": {"is_a": diode["is_a"],
                                "ideality": diode["ideality"]}},
            "initial_boundary": base, "initial": initial,
            "r20_lower_ohm": 2500.0, "r21_lower_ohm": 2000.0,
            "hi_load_ohm": 10000.0, "lo_load_ohm": 100000.0,
            "steps": steps})
    return {
        "schema": "rf-d/output-conversion-c2-vectors/v1",
        "sources": ["SVC-9 Fig. 9-8 PDF p. 10",
                    "SVC-9 Fig. 9-11 PDF p. 13",
                    "SVC-9 Table 7-8 PDF pp. 30-31",
                    "SVC-9 Fig. 9-17 PDF p. 19"],
        "node_order": list(NODES),
        "method": "Eight-variable Python finite-difference Newton with separate board-3 solve; bases imposed; implicit Euler",
        "units": {"voltage": "V", "current": "A", "time": "s",
                  "resistance": "ohm", "temperature": "K"},
        "cases": cases,
        "interpretation": "Conditional circuit scenario, not a measured vintage unit."}


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "evidence" / "output_conversion_c2_vectors.json"
    destination.write_text(json.dumps(generate_vectors(), indent=2) + "\n", encoding="utf-8")
