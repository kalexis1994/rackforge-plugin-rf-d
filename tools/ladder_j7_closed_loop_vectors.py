"""Frozen 62-node BUS-to-J7 oracle with C10/EMPHASIS closed.

The offline monolithic finite-difference/hybrid Newton reference is independent
of the native nested-port implementation. Device values are imposed scenarios.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, NODE_NAMES, conditional_ladder_ebers_moll_dc)
from filter_recovery_active_dc_reference import (
    DEVICES as RECOVERY_DEVICES, conditional_recovery_dc)
from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from output_diode_reference import diode_model_from_reference
from vca_cascaded_output_dc_reference import (
    DEVICE_NAMES, conditional_cascaded_output_dc)


OUTPUT = Path(__file__).resolve().parents[1] / "evidence" / "ladder_j7_closed_loop_vectors.json"


def generate_vectors() -> dict:
    temperature = 298.15
    diode = diode_model_from_reference(
        ideality=1.5, forward_voltage_at_100ma_v=0.7,
        temperature_k=temperature)
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250,
                                    contour_pin16_v=0),
                  range_fraction_from_ground=0.1,
                  is26_a=1e-14, is28_a=1e-14,
                  beta26=100, beta28=100, temperature_k=temperature)
    recovery = conditional_recovery_dc(
        is_a={name: 1e-14 for name in RECOVERY_DEVICES},
        beta_forward={name: 100 for name in RECOVERY_DEVICES},
        beta_reverse={name: 5 for name in RECOVERY_DEVICES},
        temperature_k=temperature)
    output_dc = conditional_cascaded_output_dc(
        first_loudness_v=2, second_loudness_base_v=2,
        first_balance_left_ohm=12.5, second_balance_left_ohm=50,
        is_a={name: 1e-14 for name in DEVICE_NAMES},
        beta_forward={name: 100 for name in DEVICE_NAMES},
        beta_reverse={name: 5 for name in DEVICE_NAMES},
        temperature_k=temperature, diode_model=diode)
    headphone = dict(transistor_is_a=1e-14, beta_forward=160,
                     beta_reverse=5, temperature_k=temperature,
                     diode_model=diode)
    rows = []
    audio_initial = None
    audio_ladder = None
    for r61 in (200, 200000):
        ladder = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)
        state = initial_coupled_headphone_state(
            ladder_dc=ladder, recovery_dc=recovery,
            cascaded_output_dc=output_dc, **headphone)
        initial = state
        if r61 == 200:
            audio_initial, audio_ladder = initial, ladder
        trace = []
        for index, (bus, r14) in enumerate(((0.0, 0.0), (0.001, 0.0),
                                            (0.01, 25000.0),
                                            (-0.01, 50000.0),
                                            (0.0, 25000.0))):
            state = nonlinear_coupled_headphone_step(
                ladder_dc=ladder, recovery_dc=recovery,
                cascaded_output_dc=output_dc, previous_state=state,
                bus_v=bus, dt_s=1/48000,
                r14_pin7_to_pin6_ohm=r14,
                r73_bottom_side_to_wiper_ohm=500,
                r20_wiper_to_ground_ohm=2500,
                hi_load_ohm=10000, lo_load_ohm=100000,
                r21_wiper_to_ground_ohm=2000,
                tip_load_ohm=32, ring_load_ohm=32,
                linear_solver="python", jacobian_method="hybrid",
                **headphone)
            trace.append(dict(index=index, bus_v=bus, r14_ohm=r14,
                              ladder_recovery_node_v=list(state["node_v"][:24]),
                              c10_capacitor_v=state["c10_capacitor_v"],
                              j7_v=state["j7_tip_v"],
                              j4_hi_v=state["j4_hi_v"],
                              j5_lo_v=state["j5_lo_v"],
                              max_kcl_residual_a=state["max_charge_kcl_residual_a"]))
        rows.append(dict(r61_ohm=r61,
                         r30_ohm=ladder["network_parameters"]["r30"],
                         tail_current_a=ladder["tail_current_a"],
                         initial_ladder_node_v=list(initial["node_v"][:16]),
                         trace=trace))
    state = audio_initial
    audio_trace = []
    checkpoints = {0, 63, 64, 95, 96, 127, 128, 191}
    for index in range(192):
        bus = 0.1 * math.sin(2 * math.pi * 100 * index / 48000)
        r14 = (0.0 if index < 64 else 25000.0 if index < 128
               else 50000.0)
        sw18 = not 96 <= index < 128
        state = nonlinear_coupled_headphone_step(
            ladder_dc=audio_ladder, recovery_dc=recovery,
            cascaded_output_dc=output_dc, previous_state=state,
            bus_v=bus, dt_s=1/48000,
            r14_pin7_to_pin6_ohm=r14,
            r73_bottom_side_to_wiper_ohm=500,
            r20_wiper_to_ground_ohm=2500,
            hi_load_ohm=10000, lo_load_ohm=100000,
            r21_wiper_to_ground_ohm=2000,
            tip_load_ohm=32, ring_load_ohm=32,
            sw18_on=sw18, linear_solver="python",
            jacobian_method="hybrid", **headphone)
        audio_trace.append(dict(index=index, bus_v=bus, r14_ohm=r14,
                                sw18_on=sw18, j7_v=state["j7_tip_v"],
                                j4_hi_v=state["j4_hi_v"],
                                j5_lo_v=state["j5_lo_v"],
                                c10_capacitor_v=state["c10_capacitor_v"],
                                ladder_recovery_node_v=(
                                    list(state["node_v"][:24])
                                    if index in checkpoints else None)))
    return dict(schema="rf-d/ladder-j7-closed-loop-vectors/v1",
                sources=["SVC-9 Fig. 9-11 PDF p. 13",
                         "SVC-9 Fig. 9-8 PDF p. 10",
                         "SVC-9 Fig. 9-17 PDF p. 19",
                         "SVC-9 Table 7-8 PDF pp. 30-31"],
                method="62-node monolithic hybrid finite-difference Newton",
                units=dict(voltage="V", current="A", time="s",
                           resistance="ohm", capacitance="F"),
                node_order=list(NODE_NAMES),
                dt_s=1/48000, headphone=headphone,
                output_diode=diode, scenarios=rows,
                audio_trace=audio_trace)


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(generate_vectors(), indent=2) + "\n",
                      encoding="utf-8")
