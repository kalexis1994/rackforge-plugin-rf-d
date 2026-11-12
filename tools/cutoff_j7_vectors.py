"""Independent monolithic 66-node Q26/Q28/C18-to-J7 regression oracle."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from cutoff_ebers_moll_reference import evaluate as cutoff_kcl, panel_equivalent, solve_dc
from filter_ladder_active_dc_reference import UPPER
from filter_ladder_ebers_moll_dc_reference import (
    DEVICE_NODES, NODE_NAMES, conditional_ladder_ebers_moll_dc, evaluate_nodal_kcl)
from filter_recovery_active_dc_reference import (
    DEVICES as RECOVERY_DEVICES, conditional_recovery_dc)
from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from output_conversion_c4_vectors import _newton
from output_diode_reference import diode_model_from_reference
from vca_cascaded_output_dc_reference import DEVICE_NAMES, conditional_cascaded_output_dc

OUTPUT = Path(__file__).resolve().parents[1]/"evidence"/"cutoff_j7_vectors.json"


def initial_cutoff_ladder(ladder, controls, *, control_seed=None):
    """Twenty-node DC KCL; neither block is treated as a fixed current source."""
    pv, pg = panel_equivalent(controls["panel"])
    lp = ladder["network_parameters"]
    x = [ladder["nodes_v"][name] for name in NODE_NAMES]
    if control_seed is None:
        control_seed = solve_dc(panel=controls["panel"], range_fraction=controls["range_fraction"],
                                tail_v=x[5], q26=controls["q26"], q28=controls["q28"])["node_v"]

    def evaluate(y):
        r, _ = evaluate_nodal_kcl(y[:16], **lp)
        current = (y[5]-y[19])/680
        r[5] += lp["tail_current"]-current
        c, _ = cutoff_kcl(y[16:], panel_v=pv, panel_g=pg,
                         range_fraction=controls["range_fraction"], tail_v=y[5],
                         q26=controls["q26"], q28=controls["q28"])
        return r+c, {}

    y, _, error = _newton(x+list(control_seed), evaluate, "cutoff-ladder/dc")
    coupled = copy.deepcopy(ladder)
    coupled["nodes_v"] = dict(zip(NODE_NAMES, y[:16]))
    coupled["tail_current_a"] = (y[5]-y[19])/680
    return coupled, y[16:], error


def setup(r61=200):
    t = 298.15
    q = dict(is_a=1e-14, beta_forward=100, beta_reverse=5, temperature_k=t)
    panel = dict(cutoff_fraction_from_neg10=0.5, scale_active_ohm=250,
                 contour_pin16_v=0, external_control_v=None, external_source_ohm=0,
                 filter_mod_on=False, modulation_source_v=None, modulation_source_ohm=0,
                 keyboard_1_3_on=False, keyboard_2_3_on=False, keyboard_cv_v=None,
                 keyboard_source_ohm=0)
    controls = dict(panel=panel, range_fraction=0.1, q26=q, q28=q)
    active_inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                           scale_active_ohm=250, contour_pin16_v=0),
                         range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
                         beta26=100, beta28=100, temperature_k=t)
    ladder = conditional_ladder_ebers_moll_dc(
        cutoff_inputs=active_inputs, is29_a=1e-14, is30_a=1e-14, beta29=100, beta30=100,
        upper_is_a={name: 1e-14 for name in UPPER}, upper_beta={name: 100 for name in UPPER},
        reverse_beta={name: 5 for name in DEVICE_NODES}, r61_ohm=r61,
        r73_bottom_side_to_wiper_ohm=500)
    ladder, control_v, dc_error = initial_cutoff_ladder(ladder, controls)
    recovery = conditional_recovery_dc(
        is_a={name: 1e-14 for name in RECOVERY_DEVICES},
        beta_forward={name: 100 for name in RECOVERY_DEVICES},
        beta_reverse={name: 5 for name in RECOVERY_DEVICES}, temperature_k=t)
    diode = diode_model_from_reference(ideality=1.5, forward_voltage_at_100ma_v=0.7,
                                       temperature_k=t)
    output = conditional_cascaded_output_dc(
        first_loudness_v=2, second_loudness_base_v=2, first_balance_left_ohm=12.5,
        second_balance_left_ohm=50, is_a={name: 1e-14 for name in DEVICE_NAMES},
        beta_forward={name: 100 for name in DEVICE_NAMES},
        beta_reverse={name: 5 for name in DEVICE_NAMES}, temperature_k=t, diode_model=diode)
    headphone = dict(transistor_is_a=1e-14, beta_forward=160, beta_reverse=5,
                     temperature_k=t, diode_model=diode)
    state = initial_coupled_headphone_state(ladder_dc=ladder, recovery_dc=recovery,
                                           cascaded_output_dc=output, **headphone)
    state["node_v"] += tuple(control_v)
    state["c18_v"] = control_v[0]
    return ladder, recovery, output, headphone, controls, state, dc_error


def oracle_step(setup_values, state, panel, range_fraction, bus, r14, sw18=True):
    ladder, recovery, output, headphone, controls, _, _ = setup_values
    return nonlinear_coupled_headphone_step(
        ladder_dc=ladder, recovery_dc=recovery, cascaded_output_dc=output,
        previous_state=state, bus_v=bus, dt_s=1/48000,
        r14_pin7_to_pin6_ohm=r14, r73_bottom_side_to_wiper_ohm=500,
        r20_wiper_to_ground_ohm=2500, hi_load_ohm=10000, lo_load_ohm=100000,
        r21_wiper_to_ground_ohm=2000, tip_load_ohm=32, ring_load_ohm=32, sw18_on=sw18,
        jacobian_method="finite_difference", linear_solver="python",
        cutoff_inputs=dict(controls, panel=panel, range_fraction=range_fraction), **headphone)


def generate_vectors():
    cases = []
    for r61 in (200, 200000):
        values = setup(r61)
        _, _, _, _, controls, state, dc_error = values
        initial = copy.deepcopy(state)
        initial["node_v"] = list(initial["node_v"])
        rows = []
        for index in range(64):
            panel = dict(controls["panel"])
            panel["cutoff_fraction_from_neg10"] = 0.5 + (0.04 if index >= 8 else 0)
            panel["contour_pin16_v"] = 0.04 if index >= 16 else 0
            if index >= 24:
                panel.update(keyboard_1_3_on=True, keyboard_2_3_on=True,
                             keyboard_cv_v=0.5, keyboard_source_ohm=1200)
            if index >= 32:
                panel.update(filter_mod_on=True, modulation_source_v=-0.15,
                             modulation_source_ohm=2000)
            if index >= 40:
                panel.update(external_control_v=0.1, external_source_ohm=10000)
            fraction = 0.1 if index < 48 else 0.12
            bus = 0.02*math.sin(2*math.pi*440*index/48000)
            r14 = 0 if index < 32 else 25000
            sw18 = not 48 <= index < 56
            state = oracle_step(values, state, panel, fraction, bus, r14, sw18)
            rows.append(dict(index=index, panel=panel, range_fraction=fraction,
                             bus_v=bus, r14_ohm=r14, sw18_on=sw18,
                             node_v=list(state["node_v"]), c18_v=state["c18_v"],
                             c10_v=state["c10_capacitor_v"],
                             tail_current_a=state["tail_current_a"], j7_v=state["j7_tip_v"],
                             j4_hi_v=state["j4_hi_v"], j5_lo_v=state["j5_lo_v"],
                             max_kcl_residual_a=state["max_charge_kcl_residual_a"]))
        cases.append(dict(r61_ohm=r61, controls=controls, initial=initial,
                          initial_dc_kcl_residual_a=dc_error, rows=rows))
    return dict(schema="rf-d/cutoff-j7-vectors/v1", dt_s=1/48000,
                method="66-node simultaneous full finite-difference Newton",
                sources=["SVC-9 Fig. 9-11 PDF p. 13", "SVC-9 Fig. 9-8 PDF p. 10",
                         "SVC-9 Fig. 9-17 PDF p. 19", "SVC-9 Table 7-8 PDF pp. 30-31"],
                cases=cases)


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(generate_vectors(), indent=2)+"\n", encoding="utf-8")
