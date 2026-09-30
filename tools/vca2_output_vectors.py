"""Fifteen-variable Python oracle: Q14/Q13/Q21 through C4/C2/J7.

Q16/Q15 collectors, first balance wiper, Q21 base and rails are imposed.
The board-3 nonlinear solve is independent of the Rust three-port tangent.
"""

from __future__ import annotations

import json
from pathlib import Path

from filter_panel_output_transient_reference import panel_load_reduction
from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_conversion_c4_vectors import _newton
from output_diode_reference import diode_model_from_reference
from vca2_active_core_dc_reference import NODES as VCA_NODES, _evaluate as vca_evaluate
from vca_cascaded_output_dc_reference import (
    DEVICE_NAMES, conditional_cascaded_output_dc)
from vca_output_conversion_dc_reference import NODES as STAGE_NODES, _evaluate as stage_evaluate


NODES = VCA_NODES + ("SECOND_BAL_WIPER", "Q1_BASE") + STAGE_NODES


def generate_vectors() -> dict:
    temperature = 298.15
    diode = diode_model_from_reference(
        ideality=1.5, forward_voltage_at_100ma_v=0.7,
        temperature_k=temperature)
    full = conditional_cascaded_output_dc(
        first_loudness_v=2.0, second_loudness_base_v=2.0,
        first_balance_left_ohm=12.5, second_balance_left_ohm=50.0,
        is_a={n: 1e-14 for n in DEVICE_NAMES},
        beta_forward={n: 100.0 for n in DEVICE_NAMES},
        beta_reverse={n: 5.0 for n in DEVICE_NAMES},
        temperature_k=temperature, diode_model=diode)
    v = full["nodes_v"]
    controls = {
        "q14_base_v": v["Q16_COLLECTOR"],
        "q13_base_v": v["Q15_COLLECTOR"],
        "q21_base_v": 2.0,
        "first_balance_wiper_v": v["FIRST_BAL_WIPER"],
        "second_balance_left_ohm": 50.0,
        "minus_v": -10.0,
        "plus_v": 10.0,
    }
    p = full["network_parameters"]
    second = p["second_parameters"]
    output = p["output_parameters"]
    headphone = dict(transistor_is_a=1e-14, beta_forward=160.0,
                     beta_reverse=5.0, temperature_k=temperature,
                     diode_model=diode)
    reduced = panel_load_reduction(
        r20_wiper_to_ground_ohm=2500.0,
        hi_load_ohm=10000.0, lo_load_ohm=100000.0)

    def circuit(y: list[float], boundary: dict, c4_current: float,
                c2_current: float) -> list[float]:
        vca_params = dict(second)
        vca_params.update(q14_base_v=boundary["q14_base_v"],
                          q13_base_v=boundary["q13_base_v"],
                          q21_base_v=boundary["q21_base_v"],
                          wiper_v=y[5], minus_v=boundary["minus_v"])
        vca_r, _ = vca_evaluate(y[:5], **vca_params)
        output_params = dict(output)
        output_params.update(q1_base_v=y[6], q12_base_v=y[3],
                             q17_base_v=y[4], plus_v=boundary["plus_v"])
        stage_r, transistors = stage_evaluate(y[7:13], **output_params)
        vca_r[3] += transistors["Q12"]["base_a"]
        vca_r[4] += transistors["Q17"]["base_a"]
        wiper = ((boundary["first_balance_wiper_v"] - y[5]) / 120.0
                 + (y[6] - y[5]) / 150.0
                 - (y[5] - y[3]) / (330.0 + boundary["second_balance_left_ohm"])
                 - (y[5] - y[4]) / (430.0 - boundary["second_balance_left_ohm"]))
        base = ((boundary["plus_v"] - y[6]) / 120.0
                + transistors["Q1"]["base_a"]
                - (y[6] - y[5]) / 150.0 - c4_current)
        stage_r[5] -= c2_current
        return vca_r + [wiper, base] + stage_r

    x_dc = [v[n] for n in VCA_NODES] + [v["SECOND_BAL_WIPER"],
                                          v["Q1_BASE"]] + [v[n] for n in STAGE_NODES]
    x_dc, _, dc_error = _newton(
        x_dc, lambda y: (circuit(y, controls, 0.0, 0.0), None), "vca2-output/dc")
    old_c4 = x_dc[6] - controls["plus_v"]
    old_c2 = x_dc[12]
    old_amp = initial_headphone_amp_state(**headphone)
    initial = {
        "node_v": x_dc, "c4_capacitor_v": old_c4,
        "c2_right_v": 0.0, "c2_capacitor_v": old_c2,
        "r21_wiper_v": 0.0, "amp_node_v": list(old_amp["node_v"]),
        "amp_capacitor_v": dict(old_amp["capacitor_v"]),
        "max_dc_kcl_residual_a": dc_error,
    }
    x = x_dc + [0.0, 0.0]
    rows = []
    dt = 1.0 / 48000.0
    for index in range(16):
        b = dict(controls)
        b["q14_base_v"] += 0.008 if index >= 4 else 0.0
        b["q13_base_v"] -= 0.006 if index >= 8 else 0.0
        b["q21_base_v"] += 0.02 if index >= 12 else 0.0
        b["first_balance_wiper_v"] += 0.03 if index >= 6 else 0.0
        sw18 = index < 7 or index >= 12
        main = reduced["equivalent_main_load_ohm"] if sw18 else 2500.0
        previous_c4, previous_c2, previous_amp = old_c4, old_c2, old_amp

        def transient(y: list[float]):
            amp = nonlinear_headphone_amp_step(
                previous_state=previous_amp, pin7_v=y[14], dt_s=dt,
                tip_load_ohm=32.0, ring_load_ohm=32.0, **headphone)
            i19 = 2.5e-6 / dt * (amp["capacitor_v"]["C19"]
                                  - previous_amp["capacitor_v"]["C19"])
            i4 = 220e-6 / dt * (y[6] - b["plus_v"] - previous_c4)
            i2 = 10e-6 / dt * (y[12] - y[13] - previous_c2)
            r = circuit(y, b, i4, i2)
            fx = y[13] / (1000.0 + main) + (y[13] - y[14]) / 4000.0 - i2
            fw = (y[14] - y[13]) / 4000.0 + y[14] / 2000.0 + i19
            return r + [fx, fw], amp

        x, amp, error = _newton(x, transient, f"vca2-output/{index}")
        pin21 = x[13] * main / (1000.0 + main)
        hi = pin21 * reduced["hi_to_pin21_ratio"] if sw18 else 0.0
        lo = hi * reduced["lo_to_hi_ratio"] if sw18 else 0.0
        rows.append({
            "boundary": b, "sw18_on": sw18,
            "node_v": x[:13], "c4_capacitor_v": x[6]-b["plus_v"],
            "c2_right_v": x[13], "c2_capacitor_v": x[12]-x[13],
            "r21_wiper_v": x[14], "j7_v": amp["j7_tip_v"],
            "j4_hi_v": hi, "j5_lo_v": lo,
            "max_kcl_residual_a": error,
            "amp_node_v": list(amp["node_v"]),
            "amp_capacitor_v": dict(amp["capacitor_v"]),
        })
        old_c4 = x[6]-b["plus_v"]
        old_c2 = x[12]-x[13]
        old_amp = amp
    return {
        "schema": "rf-d/vca2-output-vectors/v1",
        "sources": ["SVC-9 Fig. 9-11 PDF p. 13",
                    "SVC-9 Table 7-8 PDF pp. 30-31",
                    "SVC-9 Fig. 9-8 PDF p. 10",
                    "SVC-9 Fig. 9-17 PDF p. 19"],
        "node_order": list(NODES),
        "method": "15-variable finite-difference Newton; Q16/Q15 collector and first balance wiper imposed; independent Python board-3 solve",
        "units": {"voltage": "V", "current": "A", "time": "s",
                  "resistance": "ohm", "temperature": "K"},
        "case": {
            "id": "nominal_loaded_switch", "dt_s": dt,
            "r20_lower_ohm": 2500.0, "r21_lower_ohm": 2000.0,
            "hi_load_ohm": 10000.0, "lo_load_ohm": 100000.0,
            "tip_ring_load_ohm": 32.0,
            "vca_parameters": {"is_a": 1e-14, "beta_forward": 100.0,
                               "beta_reverse": 5.0,
                               "temperature_k": temperature},
            "output_parameters": {"is_a": 1e-14,
                                  "beta_forward": 100.0,
                                  "beta_reverse": 5.0,
                                  "temperature_k": temperature,
                                  "diode_model": {"is_a": diode["is_a"],
                                                  "ideality": diode["ideality"]}},
            "headphone_parameters": {"is_a": 1e-14,
                                     "beta_forward": 160.0,
                                     "beta_reverse": 5.0,
                                     "temperature_k": temperature,
                                     "diode_model": {"is_a": diode["is_a"],
                                                     "ideality": diode["ideality"]}},
            "initial_boundary": controls, "initial": initial,
            "steps": rows,
        },
        "interpretation": "Conditional laboratory parameters, no vintage measurement.",
    }


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "evidence" / "vca2_output_vectors.json"
    destination.write_text(json.dumps(generate_vectors(), indent=2) + "\n", encoding="utf-8")
