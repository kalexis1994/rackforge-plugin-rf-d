"""Conditional DC coupling of panel, Q26 PNP and Q28 NPN in SVC-9 Fig. 9-11.

Finite beta only supplies base-current loading. Collector laws remain ideal
forward-active exponentials; saturation currents, gains, TAIL and panel
source parameters are imposed, not Model D calibrations.
"""

from __future__ import annotations

import json
import math

from filter_cutoff_pair_reference import _circuit, _exponential_current
from filter_cutoff_panel_reference import conditional_panel_q26_base
from semiconductor_ideal import thermal_voltage_v


def conditional_coupled_cutoff_dc(*, panel_inputs: dict,
                                  range_fraction_from_ground: float,
                                  is26_a: float, is28_a: float,
                                  beta26: float, beta28: float,
                                  temperature_k: float, tail_v: float) -> dict:
    """Solve Q26 collector current and derive both base voltages/currents.

    ``panel_inputs`` are arguments for ``conditional_panel_q26_base`` except
    q26_base_current_a and transient arguments, which this DC solver owns.
    ``math.inf`` beta selects the old infinite-beta limit for comparison.
    """
    if not isinstance(panel_inputs, dict) or any(k in panel_inputs for k in
                                                  ("q26_base_current_a", "previous_base_v", "step_s")):
        raise ValueError("panel_inputs must describe only DC panel boundaries")
    if (not math.isfinite(range_fraction_from_ground)
            or not 0 <= range_fraction_from_ground <= 1
            or not all(math.isfinite(x) and x > 0 for x in (is26_a, is28_a))
            or not math.isfinite(tail_v)):
        raise ValueError("finite range/tail boundaries and positive Is required")
    for beta in (beta26, beta28):
        if math.isnan(beta) or beta <= 1:
            raise ValueError("beta must exceed one or be positive infinity")
    vt = thermal_voltage_v(temperature_k)
    r39, r46, r45, r60, plus, minus = _circuit()
    range_v = plus * range_fraction_from_ground
    range_rth = r39 * range_fraction_from_ground * (1 - range_fraction_from_ground)
    source_ohm = r46 + range_rth
    passive = conditional_panel_q26_base(**panel_inputs, q26_base_current_a=0)
    vbase_unloaded = passive["q26_base_v"]
    conductance_s = passive["node_conductance_s"]
    inverse_beta26 = 0 if math.isinf(beta26) else 1 / beta26
    inverse_beta28 = 0 if math.isinf(beta28) else 1 / beta28

    def state(ic26_a: float) -> tuple[float, float, float, float, float]:
        vbase = vbase_unloaded + ic26_a * inverse_beta26 / conductance_s
        shared_v = vbase + vt * math.log(ic26_a / is26_a)
        ic28_a = _exponential_current(is28_a, shared_v / vt)
        source_a = (range_v - shared_v) / source_ohm
        emitter26_a = ic26_a * (1 + inverse_beta26)
        ib28_a = 0 if inverse_beta28 == 0 else ic28_a * inverse_beta28
        return vbase, shared_v, ic28_a, source_a, source_a - emitter26_a - ib28_a

    high_a = max(is26_a, 1e-12)
    for _ in range(200):
        if state(high_a)[-1] <= 0:
            break
        high_a *= 2
        if not math.isfinite(high_a):
            raise ValueError("could not bracket Q26 collector current")
    else:
        raise ValueError("could not bracket Q26 collector current")
    low_a = 0.0
    for _ in range(140):
        middle_a = (low_a + high_a) / 2
        if middle_a == 0 or state(middle_a)[-1] > 0:
            low_a = middle_a
        else:
            high_a = middle_a
    ic26_a = (low_a + high_a) / 2
    if ic26_a <= 0:
        raise ValueError("Q26 current below representable positive domain")
    vbase, shared_v, ic28_a, source_a, shared_residual_a = state(ic26_a)
    if not all(math.isfinite(x) for x in
               (vbase, shared_v, ic28_a, source_a, shared_residual_a)):
        raise ValueError("ideal law exceeds finite numeric domain")
    ib26_signed_a = -ic26_a * inverse_beta26
    ib28_a = ic28_a * inverse_beta28
    loaded_panel = conditional_panel_q26_base(
        **panel_inputs, q26_base_current_a=ib26_signed_a)
    vc26 = minus + ic26_a * r45
    vc28 = tail_v - ic28_a * r60
    return {
        "q26_base_v": vbase,
        "q26_base_unloaded_v": vbase_unloaded,
        "shared_node_v": shared_v,
        "q26_collector_current_a": ic26_a,
        "q26_base_current_signed_from_node_a": ib26_signed_a,
        "q26_emitter_current_a": ic26_a * (1 + inverse_beta26),
        "q28_collector_current_a_candidate": ic28_a,
        "q28_base_current_a": ib28_a,
        "range_source_current_a": source_a,
        "q26_collector_v": vc26,
        "q28_collector_v_candidate": vc28,
        "q26_forward_active_candidate": vc26 < vbase < shared_v,
        "q28_forward_active_candidate": 0 < shared_v < vc28,
        "shared_kcl_residual_a": shared_residual_a,
        "base_kcl_residual_a": loaded_panel["resistive_kcl_residual_a"],
        "base_coupling_residual_v": vbase - loaded_panel["q26_base_v"],
        "q26_exponential_residual_v": shared_v - vbase - vt * math.log(ic26_a / is26_a),
        "range_thevenin_v": range_v,
        "range_thevenin_ohm": range_rth,
        "source_total_ohm": source_ohm,
        "beta26_imposed": beta26,
        "beta28_imposed": beta28,
        "is26_a_imposed": is26_a,
        "is28_a_imposed": is28_a,
        "temperature_k_imposed": temperature_k,
        "tail_v_imposed": tail_v,
        "panel": loaded_panel,
        "absolute_device_parameters_known": False,
    }


if __name__ == "__main__":
    out = conditional_coupled_cutoff_dc(
        panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                          scale_active_ohm=250, contour_pin16_v=0),
        range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
        beta26=100, beta28=100, temperature_k=298.15, tail_v=2)
    print(json.dumps(out, indent=2))
