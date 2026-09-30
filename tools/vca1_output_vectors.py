"""Independent 25-variable first-VCA-through-J7 transient oracle.

Uses full 22-node Python DC KCL, numerical Jacobian and separate board-3
nonlinear solve. Rust nested ports and their analytic derivatives are unused.
"""

from __future__ import annotations

import json
from pathlib import Path

from filter_panel_output_transient_reference import panel_load_reduction
from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_conversion_c4_vectors import _newton
from output_diode_reference import diode_model_from_reference
from vca_cascaded_output_dc_reference import (
    DEVICE_NAMES, NODES as CHAIN_NODES, _evaluate as chain_evaluate,
    conditional_cascaded_output_dc)

NODES = ("C6_LEFT",) + CHAIN_NODES + ("C2_RIGHT", "R21_WIPER")


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
    controls = dict(recover_collector_v=5.0, loudness_v=2.0,
                    q21_base_v=2.0, first_balance_left_ohm=12.5,
                    second_balance_left_ohm=50.0, plus_v=10.0, minus_v=-10.0)
    p = full["network_parameters"]
    headphone = dict(transistor_is_a=1e-14, beta_forward=160.0,
                     beta_reverse=5.0, temperature_k=temperature,
                     diode_model=diode)
    reduced = panel_load_reduction(
        r20_wiper_to_ground_ohm=2500.0,
        hi_load_ohm=10000.0, lo_load_ohm=100000.0)
    dt = 1.0 / 48000.0

    def chain(y: list[float], b: dict) -> list[float]:
        first = dict(p["first_parameters"])
        core = dict(first["core_parameters"])
        core.update(loudness_v=b["loudness_v"],
                    left_ohm=b["first_balance_left_ohm"],
                    minus_v=b["minus_v"])
        first["core_parameters"] = core
        second = dict(p["second_parameters"])
        second.update(q21_base_v=b["q21_base_v"],
                      left_ohm=b["second_balance_left_ohm"],
                      minus_v=b["minus_v"])
        residual, _ = chain_evaluate(
            y[1:23], first_parameters=first, second_parameters=second,
            output_parameters=p["output_parameters"], plus_v=b["plus_v"])
        return residual

    x_dc = [controls["recover_collector_v"]] + [v[n] for n in CHAIN_NODES]
    old_c6 = x_dc[0] - x_dc[1]
    old_c15 = x_dc[2]
    old_c4 = x_dc[16] - controls["plus_v"]
    old_c2 = x_dc[22]
    old_amp = initial_headphone_amp_state(**headphone)
    initial = dict(node_v=x_dc[:23], c6_capacitor_v=old_c6,
                   c15_capacitor_v=old_c15, c4_capacitor_v=old_c4,
                   c2_right_v=0.0, c2_capacitor_v=old_c2,
                   r21_wiper_v=0.0, amp_node_v=list(old_amp["node_v"]),
                   amp_capacitor_v=dict(old_amp["capacitor_v"]),
                   max_dc_kcl_residual_a=full["max_kcl_residual_a"])
    x = x_dc + [0.0, 0.0]
    rows = []
    for index in range(12):
        b = dict(controls)
        b["recover_collector_v"] += 0.5 if index >= 2 else 0.0
        b["loudness_v"] += 0.03 if index >= 4 else 0.0
        b["q21_base_v"] += 0.02 if index >= 8 else 0.0
        sw18 = index < 6 or index >= 10
        main = reduced["equivalent_main_load_ohm"] if sw18 else 2500.0
        previous_amp = old_amp
        previous_caps = old_c6, old_c15, old_c4, old_c2

        def transient(y: list[float]):
            amp = nonlinear_headphone_amp_step(
                previous_state=previous_amp, pin7_v=y[24], dt_s=dt,
                tip_load_ohm=32.0, ring_load_ohm=32.0, **headphone)
            i19 = 2.5e-6 / dt * (amp["capacitor_v"]["C19"]
                                  - previous_amp["capacitor_v"]["C19"])
            i6 = 0.33e-6 / dt * (y[0] - y[1] - previous_caps[0])
            i15 = 220e-6 / dt * (y[2] - previous_caps[1])
            i4 = 220e-6 / dt * (y[16] - b["plus_v"] - previous_caps[2])
            i2 = 10e-6 / dt * (y[22] - y[23] - previous_caps[3])
            residual = chain(y, b)
            residual[0] += i6
            residual[1] -= i15
            residual[15] -= i4
            residual[21] -= i2
            left = (b["recover_collector_v"] - y[0]) / 82000.0 - i6
            right = y[23] / (1000.0 + main) + (y[23] - y[24]) / 4000.0 - i2
            wiper = (y[24] - y[23]) / 4000.0 + y[24] / 2000.0 + i19
            return [left] + residual + [right, wiper], amp

        x, amp, error = _newton(x, transient, f"vca1-output/{index}")
        pin21 = x[23] * main / (1000.0 + main)
        hi = pin21 * reduced["hi_to_pin21_ratio"] if sw18 else 0.0
        lo = hi * reduced["lo_to_hi_ratio"] if sw18 else 0.0
        rows.append(dict(boundary=b, sw18_on=sw18, node_v=x[:23],
                         c6_capacitor_v=x[0]-x[1], c15_capacitor_v=x[2],
                         c4_capacitor_v=x[16]-b["plus_v"],
                         c2_right_v=x[23], c2_capacitor_v=x[22]-x[23],
                         r21_wiper_v=x[24], j7_v=amp["j7_tip_v"],
                         j4_hi_v=hi, j5_lo_v=lo,
                         max_kcl_residual_a=error,
                         amp_node_v=list(amp["node_v"]),
                         amp_capacitor_v=dict(amp["capacitor_v"])))
        old_c6, old_c15 = x[0]-x[1], x[2]
        old_c4, old_c2 = x[16]-b["plus_v"], x[22]-x[23]
        old_amp = amp
    return dict(
        schema="rf-d/vca1-output-vectors/v1",
        sources=["SVC-9 Fig. 9-11 PDF p. 13",
                 "SVC-9 Table 7-8 PDF pp. 30-31",
                 "SVC-9 Fig. 9-8 PDF p. 10",
                 "SVC-9 Fig. 9-17 PDF p. 19"],
        node_order=list(NODES),
        method="25-variable finite-difference Newton; independent board-3 solve",
        units=dict(voltage="V", current="A", time="s", resistance="ohm",
                   capacitance="F", temperature="K"),
        case=dict(id="nominal_loaded_switch", dt_s=dt,
                  r20_lower_ohm=2500.0, r21_lower_ohm=2000.0,
                  hi_load_ohm=10000.0, lo_load_ohm=100000.0,
                  tip_ring_load_ohm=32.0,
                  vca_parameters=dict(is_a=1e-14, beta_forward=100.0,
                                      beta_reverse=5.0,
                                      temperature_k=temperature),
                  output_parameters=dict(is_a=1e-14, beta_forward=100.0,
                                         beta_reverse=5.0,
                                         temperature_k=temperature,
                                         diode_model=dict(is_a=diode["is_a"],
                                                          ideality=diode["ideality"])),
                  headphone_parameters=dict(is_a=1e-14, beta_forward=160.0,
                                            beta_reverse=5.0,
                                            temperature_k=temperature,
                                            diode_model=dict(is_a=diode["is_a"],
                                                             ideality=diode["ideality"])),
                  initial_boundary=controls, initial=initial, steps=rows),
        interpretation="Conditional laboratory parameters, no vintage measurement.")


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "evidence" / "vca1_output_vectors.json"
    destination.write_text(json.dumps(generate_vectors(), indent=2) + "\n",
                           encoding="utf-8")
