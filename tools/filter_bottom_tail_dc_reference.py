"""Conditional Q29/Q30 emitter-node closure against Q28/R60, SVC-9 Fig. 9-11.

The lower-pair bases and transistor parameters are imposed. The result
determines TAIL and Q28 collector headroom; ladder collector rails remain
unknown, so it cannot prove Q29/Q30 forward-active operation.
"""

from __future__ import annotations

import json
import math

from filter_cutoff_coupled_dc_reference import conditional_coupled_cutoff_dc
from filter_input_pair_reference import EVIDENCE, _check_topology
from semiconductor_ideal import thermal_voltage_v


def conditional_bottom_tail_dc(*, cutoff_inputs: dict,
                               q29_base_v: float, q30_base_v: float,
                               is29_a: float, is30_a: float,
                               beta29: float, beta30: float) -> dict:
    """Find common-emitter voltage for Q29/Q30 emitter current = Q28 Ic.

    ``cutoff_inputs`` supply all parameters of conditional_coupled_cutoff_dc
    except TAIL; a preselected tail voltage is deliberately rejected.
    """
    _check_topology()
    if not isinstance(cutoff_inputs, dict) or "tail_v" in cutoff_inputs:
        raise ValueError("cutoff_inputs must omit TAIL; this solver determines it")
    if not all(math.isfinite(x) for x in (q29_base_v, q30_base_v)):
        raise ValueError("finite lower-pair base voltages required")
    if not all(math.isfinite(x) and x > 0 for x in (is29_a, is30_a)):
        raise ValueError("positive finite lower-pair saturation currents required")
    for beta in (beta29, beta30):
        if math.isnan(beta) or beta <= 1:
            raise ValueError("lower-pair beta must exceed one or be positive infinity")
    cutoff = conditional_coupled_cutoff_dc(**cutoff_inputs, tail_v=None)
    tail_current_a = cutoff["q28_collector_current_a_candidate"]
    if tail_current_a <= 0 or not math.isfinite(tail_current_a):
        raise ValueError("Q28 tail current outside positive finite domain")
    vt = thermal_voltage_v(cutoff["temperature_k_imposed"])
    inv29 = 0 if math.isinf(beta29) else 1 / beta29
    inv30 = 0 if math.isinf(beta30) else 1 / beta30

    # The shared emitter voltage is a log-sum-exp, avoiding overflow when
    # imposed base voltages differ by many thermal voltages.
    log_weight29 = math.log(is29_a) + q29_base_v / vt + math.log1p(inv29)
    log_weight30 = math.log(is30_a) + q30_base_v / vt + math.log1p(inv30)
    if not math.isfinite(log_weight29) or not math.isfinite(log_weight30):
        raise ValueError("lower-pair logarithmic weights outside finite domain")
    largest = max(log_weight29, log_weight30)
    log_sum = largest + math.log(math.exp(log_weight29 - largest)
                                 + math.exp(log_weight30 - largest))
    tail_v = vt * (log_sum - math.log(tail_current_a))
    if not math.isfinite(tail_v):
        raise ValueError("TAIL voltage outside finite numeric domain")
    emitter29_a = tail_current_a * math.exp(log_weight29 - log_sum)
    emitter30_a = tail_current_a - emitter29_a
    collector29_a = emitter29_a / (1 + inv29)
    collector30_a = emitter30_a / (1 + inv30)
    base29_a = collector29_a * inv29
    base30_a = collector30_a * inv30
    r60_ohm = json.loads(EVIDENCE.read_text(encoding="utf-8"))["connections"]["R60"]["ohm"]
    q28_collector_v = tail_v - tail_current_a * r60_ohm
    return {
        "tail_v": tail_v,
        "tail_current_a": tail_current_a,
        "q28_collector_v": q28_collector_v,
        "q28_forward_active_candidate": (
            0 < cutoff["shared_node_v"] < q28_collector_v),
        "q29_collector_current_a_candidate": collector29_a,
        "q30_collector_current_a_candidate": collector30_a,
        "q29_emitter_current_a": emitter29_a,
        "q30_emitter_current_a": emitter30_a,
        "q29_base_current_a": base29_a,
        "q30_base_current_a": base30_a,
        "q29_be_forward_biased_candidate": q29_base_v > tail_v,
        "q30_be_forward_biased_candidate": q30_base_v > tail_v,
        "q29_q30_collector_headroom_known": False,
        "tail_kcl_residual_a": emitter29_a + emitter30_a - tail_current_a,
        "r60_voltage_residual_v": tail_v - q28_collector_v - tail_current_a * r60_ohm,
        "q29_base_v_imposed": q29_base_v,
        "q30_base_v_imposed": q30_base_v,
        "is29_a_imposed": is29_a,
        "is30_a_imposed": is30_a,
        "beta29_imposed": beta29,
        "beta30_imposed": beta30,
        "cutoff": cutoff,
        "absolute_device_parameters_known": False,
    }


if __name__ == "__main__":
    inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250, contour_pin16_v=0),
                  range_fraction_from_ground=0.1, is26_a=1e-14, is28_a=1e-14,
                  beta26=100, beta28=100, temperature_k=298.15)
    out = conditional_bottom_tail_dc(
        cutoff_inputs=inputs, q29_base_v=1.1, q30_base_v=1.1,
        is29_a=1e-14, is30_a=1e-14, beta29=100, beta30=100)
    print(json.dumps(out, indent=2))
