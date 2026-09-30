"""Independent 33-variable Q5-Q8/C1/C5/C9 through VCA/J7 oracle.

The ladder upper emitters are imposed. C10/emphasis is open here. Newton
differences the complete residual and solves board 3 independently of Rust.
"""

from __future__ import annotations

import json
from pathlib import Path

from filter_panel_output_transient_reference import panel_load_reduction
from filter_recovery_active_dc_reference import (
    DEVICES as RECOVERY_DEVICES, NODES as RECOVERY_NODES,
    _evaluate as recovery_evaluate, conditional_recovery_dc)
from headphone_amp_active_transient_reference import (
    initial_headphone_amp_state, nonlinear_headphone_amp_step)
from output_conversion_c4_vectors import _newton
from output_diode_reference import diode_model_from_reference
from vca_cascaded_output_dc_reference import (
    DEVICE_NAMES, NODES as CHAIN_NODES, _evaluate as chain_evaluate,
    conditional_cascaded_output_dc)

NODES = RECOVERY_NODES + ("C6_LEFT",) + CHAIN_NODES + ("C2_RIGHT", "R21_WIPER")


def generate_vectors() -> dict:
    temperature = 298.15
    diode = diode_model_from_reference(
        ideality=1.5, forward_voltage_at_100ma_v=0.7,
        temperature_k=temperature)
    recovery = conditional_recovery_dc(
        is_a={n: 1e-14 for n in RECOVERY_DEVICES},
        beta_forward={n: 100.0 for n in RECOVERY_DEVICES},
        beta_reverse={n: 5.0 for n in RECOVERY_DEVICES},
        temperature_k=temperature)
    chain = conditional_cascaded_output_dc(
        first_loudness_v=2.0, second_loudness_base_v=2.0,
        first_balance_left_ohm=12.5, second_balance_left_ohm=50.0,
        is_a={n: 1e-14 for n in DEVICE_NAMES},
        beta_forward={n: 100.0 for n in DEVICE_NAMES},
        beta_reverse={n: 5.0 for n in DEVICE_NAMES},
        temperature_k=temperature, diode_model=diode)
    rv = recovery["nodes_v"]
    cv = chain["nodes_v"]
    rp = recovery["network_parameters"]
    cp = chain["network_parameters"]
    headphone = dict(transistor_is_a=1e-14, beta_forward=160.0,
                     beta_reverse=5.0, temperature_k=temperature,
                     diode_model=diode)
    controls = dict(ladder_left_v=0.0, ladder_right_v=0.0,
                    loudness_v=2.0, q21_base_v=2.0,
                    first_balance_left_ohm=12.5,
                    second_balance_left_ohm=50.0,
                    plus_v=10.0, minus_v=-10.0)
    reduced = panel_load_reduction(
        r20_wiper_to_ground_ohm=2500.0,
        hi_load_ohm=10000.0, lo_load_ohm=100000.0)
    dt = 1.0/48000.0

    def base_kcl(y: list[float], b: dict) -> list[float]:
        recovery_r, _ = recovery_evaluate(
            y[:8], resistance=rp["resistance"],
            plus=b["plus_v"], minus=b["minus_v"], vt=rp["vt"],
            is_a=rp["is_a"], beta_forward=rp["beta_forward"],
            beta_reverse=rp["beta_reverse"])
        first = dict(cp["first_parameters"])
        core = dict(first["core_parameters"])
        core.update(loudness_v=b["loudness_v"],
                    left_ohm=b["first_balance_left_ohm"],
                    minus_v=b["minus_v"])
        first["core_parameters"] = core
        second = dict(cp["second_parameters"])
        second.update(q21_base_v=b["q21_base_v"],
                      left_ohm=b["second_balance_left_ohm"],
                      minus_v=b["minus_v"])
        chain_r, _ = chain_evaluate(
            y[9:31], first_parameters=first, second_parameters=second,
            output_parameters=cp["output_parameters"], plus_v=b["plus_v"])
        i2 = (y[5]-y[8])/82000.0
        recovery_r[5] -= i2
        return recovery_r + [i2] + chain_r

    x_dc = ([rv[n] for n in RECOVERY_NODES] + [rv["RECOVER_COLLECTOR"]]
            + [cv[n] for n in CHAIN_NODES])
    old_caps = [x_dc[0], x_dc[1], x_dc[7],
                x_dc[8]-x_dc[9], x_dc[10], x_dc[24]-controls["plus_v"],
                x_dc[30]]
    old_amp = initial_headphone_amp_state(**headphone)
    initial = dict(node_v=x_dc, recovery_capacitor_v=old_caps[:3],
                   c6_capacitor_v=old_caps[3], c15_capacitor_v=old_caps[4],
                   c4_capacitor_v=old_caps[5], c2_right_v=0.0,
                   c2_capacitor_v=old_caps[6], r21_wiper_v=0.0,
                   amp_node_v=list(old_amp["node_v"]),
                   max_dc_kcl_residual_a=max(recovery["max_kcl_residual_a"],
                                               chain["max_kcl_residual_a"]))
    x = x_dc + [0.0, 0.0]
    rows = []
    for index in range(16):
        b = dict(controls)
        b["ladder_left_v"] += 0.05 if index >= 3 else 0.0
        b["ladder_right_v"] -= 0.04 if index >= 6 else 0.0
        b["loudness_v"] += 0.02 if index >= 8 else 0.0
        b["q21_base_v"] += 0.015 if index >= 11 else 0.0
        sw18 = index < 5 or index >= 10
        main = reduced["equivalent_main_load_ohm"] if sw18 else 2500.0
        previous_amp = old_amp
        previous_caps = old_caps.copy()

        def transient(y: list[float]):
            amp = nonlinear_headphone_amp_step(
                previous_state=previous_amp, pin7_v=y[32], dt_s=dt,
                tip_load_ohm=32.0, ring_load_ohm=32.0, **headphone)
            i19 = 2.5e-6/dt * (amp["capacitor_v"]["C19"]
                                 - previous_amp["capacitor_v"]["C19"])
            residual = base_kcl(y, b)
            residual[0] -= 0.22e-6/dt * (y[0]-b["ladder_left_v"]-previous_caps[0])
            residual[1] -= 0.22e-6/dt * (y[1]-b["ladder_right_v"]-previous_caps[1])
            residual[7] -= 100e-6/dt * (y[7]-previous_caps[2])
            i6 = 0.33e-6/dt * (y[8]-y[9]-previous_caps[3])
            residual[8] -= i6
            residual[9] += i6
            residual[10] -= 220e-6/dt * (y[10]-previous_caps[4])
            residual[24] -= 220e-6/dt * (y[24]-b["plus_v"]-previous_caps[5])
            i2 = 10e-6/dt * (y[30]-y[31]-previous_caps[6])
            residual[30] -= i2
            right = y[31]/(1000.0+main) + (y[31]-y[32])/4000.0 - i2
            wiper = (y[32]-y[31])/4000.0 + y[32]/2000.0 + i19
            return residual + [right, wiper], amp

        x, amp, error = _newton(x, transient, f"recovery-vca/{index}")
        pin21 = x[31]*main/(1000.0+main)
        hi = pin21*reduced["hi_to_pin21_ratio"] if sw18 else 0.0
        lo = hi*reduced["lo_to_hi_ratio"] if sw18 else 0.0
        rows.append(dict(boundary=b, sw18_on=sw18, node_v=x[:31],
                         upstream_port_current_a=[
                             0.22e-6/dt * (b["ladder_left_v"]-x[0]+previous_caps[0]),
                             0.22e-6/dt * (b["ladder_right_v"]-x[1]+previous_caps[1]),
                         ],
                         recovery_capacitor_v=[x[0]-b["ladder_left_v"],
                                               x[1]-b["ladder_right_v"], x[7]],
                         c6_capacitor_v=x[8]-x[9], c15_capacitor_v=x[10],
                         c4_capacitor_v=x[24]-b["plus_v"],
                         c2_right_v=x[31], c2_capacitor_v=x[30]-x[31],
                         r21_wiper_v=x[32], j7_v=amp["j7_tip_v"],
                         j4_hi_v=hi, j5_lo_v=lo, max_kcl_residual_a=error,
                         amp_node_v=list(amp["node_v"])))
        old_caps = [x[0]-b["ladder_left_v"], x[1]-b["ladder_right_v"],
                    x[7], x[8]-x[9], x[10], x[24]-b["plus_v"],
                    x[30]-x[31]]
        old_amp = amp
    return dict(
        schema="rf-d/recovery-vca-output-vectors/v1",
        sources=["SVC-9 Fig. 9-11 PDF p. 13",
                 "SVC-9 Table 7-8 PDF pp. 30-31",
                 "SVC-9 Fig. 9-8 PDF p. 10",
                 "SVC-9 Fig. 9-17 PDF p. 19"],
        node_order=list(NODES),
        method="33-variable finite-difference Newton; independent board-3 solve",
        units=dict(voltage="V", current="A", time="s", resistance="ohm",
                   capacitance="F", temperature="K"),
        case=dict(dt_s=dt, r20_lower_ohm=2500.0, r21_lower_ohm=2000.0,
                  hi_load_ohm=10000.0, lo_load_ohm=100000.0,
                  tip_ring_load_ohm=32.0,
                  transistor_parameters=dict(is_a=1e-14, beta_forward=100.0,
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
        interpretation="Conditional laboratory parameters and imposed ladder emitters; C10 open; no vintage measurement.")


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "evidence" / "recovery_vca_output_vectors.json"
    destination.write_text(json.dumps(generate_vectors(), indent=2) + "\n",
                           encoding="utf-8")
