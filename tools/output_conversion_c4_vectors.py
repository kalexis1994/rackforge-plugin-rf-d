"""Nine-variable Python oracle for Q1_BASE/C4/Q1/Q12/Q17/C2/panel/board3.

The second VCA balance wiper and Q12/Q17 bases are imposed boundaries.
Every Newton column is differentiated numerically, independently of Rust.
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
    DEVICES, NODES as STAGE_NODES, _evaluate,
    conditional_output_conversion_dc)


NODES = ("Q1_BASE",) + STAGE_NODES


def _newton(initial: list[float], evaluate, label: str) -> tuple[list[float], dict, float]:
    x = initial.copy()
    for _ in range(30):
        residual, extra = evaluate(x)
        error = max(abs(v) for v in residual)
        if error < 1e-11:
            return x, extra, error
        jacobian = [[0.0] * len(x) for _ in x]
        for column in range(len(x)):
            shifted = x.copy()
            shifted[column] += 1e-6
            higher, _ = evaluate(shifted)
            for row in range(len(x)):
                jacobian[row][column] = (higher[row] - residual[row]) / 1e-6
        direction = _solve_linear(jacobian, [-v for v in residual])
        for power in range(24):
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
            raise ValueError(f"line search failed: {label}")
    raise ValueError(f"iteration budget failed: {label}")


def generate_vectors() -> dict:
    cases = []
    for name, temperature, dt, jack, step_count in (
            ("nominal_loaded", 298.15, 1 / 48000, 32.0, 16),
            ("cool_open", 285.0, 1 / 9600, None, 12)):
        diode = diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.7,
            temperature_k=temperature)
        headphone = dict(transistor_is_a=1e-14, beta_forward=160.0,
                         beta_reverse=5.0, temperature_k=temperature,
                         diode_model=diode)
        devices = dict(is_a={n: 1e-14 for n in DEVICES},
                       beta_forward={n: 100.0 for n in DEVICES},
                       beta_reverse={n: 5.0 for n in DEVICES})
        base = dict(second_balance_wiper_v=6.2, q12_base_v=7.75,
                    q17_base_v=7.75, plus_v=10.0)
        stage_seed = conditional_output_conversion_dc(
            q1_base_v=8.3, q12_base_v=base["q12_base_v"],
            q17_base_v=base["q17_base_v"], plus_v=10.0,
            temperature_k=temperature, diode_model=diode, **devices)
        network = dict(stage_seed["network_parameters"])

        def stage(y: list[float], controls: dict):
            parameters = dict(network)
            parameters.update(q1_base_v=y[0],
                              q12_base_v=controls["q12_base_v"],
                              q17_base_v=controls["q17_base_v"],
                              plus_v=controls["plus_v"])
            return _evaluate(y[1:7], **parameters)

        def dc_evaluate(y: list[float]):
            currents, transistors = stage(y, base)
            q1b = ((y[0] - base["plus_v"]) / 120.0
                   + (y[0] - base["second_balance_wiper_v"]) / 150.0
                   - transistors["Q1"]["base_a"])
            return [q1b] + currents, transistors

        x_dc, _, dc_error = _newton(
            [8.3] + [stage_seed["nodes_v"][n] for n in STAGE_NODES],
            dc_evaluate, f"{name}/dc")
        old_c4 = x_dc[0] - base["plus_v"]
        old_c2 = x_dc[6]
        old_amp = initial_headphone_amp_state(**headphone)
        x = x_dc + [0.0, 0.0]
        initial = {
            "node_v": x_dc, "c4_capacitor_v": old_c4,
            "c2_right_v": 0.0, "c2_capacitor_v": old_c2,
            "r21_wiper_v": 0.0, "amp_node_v": list(old_amp["node_v"]),
            "amp_capacitor_v": dict(old_amp["capacitor_v"]),
            "max_dc_kcl_residual_a": dc_error}
        reduced = panel_load_reduction(
            r20_wiper_to_ground_ohm=2500.0,
            hi_load_ohm=10000.0, lo_load_ohm=100000.0)
        rows = []
        for index in range(step_count):
            controls = dict(base)
            controls["second_balance_wiper_v"] += 0.06 if index >= 4 else 0.0
            controls["q12_base_v"] -= 0.012 if index >= 8 else 0.0
            controls["q17_base_v"] += (0.018 if index < 4 else
                                         -0.025 if index < 8 else 0.036)
            sw18 = name == "cool_open" or index < 6 or index >= 11
            main = reduced["equivalent_main_load_ohm"] if sw18 else 2500.0
            previous_c4, previous_c2, previous_amp = old_c4, old_c2, old_amp

            def transient(y: list[float]):
                currents, transistors = stage(y, controls)
                i4 = 220e-6 / dt * (y[0] - controls["plus_v"]
                                    - previous_c4)
                q1b = ((y[0] - controls["plus_v"]) / 120.0
                       + (y[0] - controls["second_balance_wiper_v"]) / 150.0
                       + i4 - transistors["Q1"]["base_a"])
                amp = nonlinear_headphone_amp_step(
                    previous_state=previous_amp, pin7_v=y[8], dt_s=dt,
                    tip_load_ohm=jack, ring_load_ohm=jack, **headphone)
                i19 = 2.5e-6 / dt * (amp["capacitor_v"]["C19"]
                                      - previous_amp["capacitor_v"]["C19"])
                i2 = 10e-6 / dt * (y[6] - y[7] - previous_c2)
                currents[5] -= i2  # stage convention: incoming minus outgoing
                fx = y[7] / (1000.0 + main) + (y[7] - y[8]) / 4000.0 - i2
                fw = (y[8] - y[7]) / 4000.0 + y[8] / 2000.0 + i19
                return [q1b] + currents + [fx, fw], amp

            x, amp, error = _newton(x, transient, f"{name}/{index}")
            _, transistors = stage(x, controls)
            pin21 = x[7] * main / (1000.0 + main)
            hi = pin21 * reduced["hi_to_pin21_ratio"] if sw18 else 0.0
            lo = hi * reduced["lo_to_hi_ratio"] if sw18 else 0.0
            rows.append({
                "boundary": controls, "sw18_on": sw18,
                "node_v": x[:7], "c4_capacitor_v": x[0] - controls["plus_v"],
                "c2_right_v": x[7], "c2_capacitor_v": x[6] - x[7],
                "r21_wiper_v": x[8], "board4_pin21_v": pin21,
                "j4_hi_v": hi, "j5_lo_v": lo, "j7_v": amp["j7_tip_v"],
                "c2_current_a": 10e-6 / dt * (x[6] - x[7] - old_c2),
                "c4_current_a": 220e-6 / dt * (
                    x[0] - controls["plus_v"] - old_c4),
                "upstream_port_current_a": [
                    (controls["second_balance_wiper_v"] - x[0]) / 150.0,
                    transistors["Q12"]["base_a"],
                    transistors["Q17"]["base_a"],
                ],
                "max_kcl_residual_a": error,
                "amp_node_v": list(amp["node_v"]),
                "amp_capacitor_v": dict(amp["capacitor_v"])})
            old_c4 = x[0] - controls["plus_v"]
            old_c2 = x[6] - x[7]
            old_amp = amp
        cases.append({
            "id": name, "dt_s": dt, "tip_ring_load_ohm": jack,
            "r20_lower_ohm": 2500.0, "r21_lower_ohm": 2000.0,
            "hi_load_ohm": 10000.0, "lo_load_ohm": 100000.0,
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
            "initial_boundary": base, "initial": initial, "steps": rows})
    return {
        "schema": "rf-d/output-conversion-c4-vectors/v1",
        "sources": ["SVC-9 Fig. 9-11 PDF p. 13",
                    "SVC-9 Table 7-8 PDF pp. 30-31",
                    "SVC-9 Fig. 9-8 PDF p. 10",
                    "SVC-9 Fig. 9-17 PDF p. 19"],
        "node_order": list(NODES),
        "method": "Nine-variable Python finite-difference Newton with separate board-3 solve; second VCA wiper and Q12/Q17 bases imposed; implicit Euler",
        "units": {"voltage": "V", "current": "A", "time": "s",
                  "resistance": "ohm", "temperature": "K"},
        "cases": cases,
        "interpretation": "Conditional circuit scenario, not vintage measurement."}


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "evidence" / "output_conversion_c4_vectors.json"
    destination.write_text(json.dumps(generate_vectors(), indent=2) + "\n", encoding="utf-8")
