"""Conditional DC closure of Q29/Q30 bases, BOTTOM and TAIL, SVC-9 Fig. 9-11.

The upper-ladder current entering BOTTOM is imposed. R61 is an explicit
200-ohm or 200-kohm documentary candidate. All transistor parameters are
imposed; collector-rail headroom and complete ladder bias remain unknown.
"""

from __future__ import annotations

import json
import math

from filter_bottom_tail_dc_reference import conditional_bottom_tail_dc
from filter_cutoff_coupled_dc_reference import conditional_coupled_cutoff_dc
from filter_input_reference import _parts
from filter_regeneration_reference import _values as _regen_values, EVIDENCE as REGEN_EVIDENCE
from semiconductor_ideal import thermal_voltage_v


def conditional_bottom_bias_dc(*, cutoff_inputs: dict,
                               is29_a: float, is30_a: float,
                               beta29: float, beta30: float,
                               r61_ohm: int,
                               r73_bottom_side_to_wiper_ohm: float,
                               ladder_bottom_injection_a: float) -> dict:
    """Resolve BOTTOM, both bases and TAIL for imposed upper-ladder injection.

    Positive ``ladder_bottom_injection_a`` enters BOTTOM from above. In DC,
    C27/C24/C10 are open and pin 6 has no source through the R14 path.
    """
    parts = _parts()
    r61_candidates = parts["R61"]["candidate_ohm"]
    if r61_ohm not in r61_candidates:
        raise ValueError("select the 200 or 200000 ohm R61 documentary candidate")
    r54 = parts["R54"]["ohm"]
    _, _, r73_total, r76 = _regen_values()
    regen = json.loads(REGEN_EVIDENCE.read_text(encoding="utf-8"))
    if (regen["parts"]["R14_PANEL"]["lower_terminal"] != "OPEN in Fig. 9-17"
            or regen["parts"]["R73_BOARD4"]["wiper_at"] != "REGEN_BASE"):
        raise ValueError("regeneration DC return differs from source drawing")
    if (not math.isfinite(r73_bottom_side_to_wiper_ohm)
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total
            or not math.isfinite(ladder_bottom_injection_a)):
        raise ValueError("finite R73 electrical segment and ladder injection required")
    # The lower-pair solver validates Is/beta, but we need those parameters
    # before calling it to solve the one-dimensional current split.
    if not all(math.isfinite(x) and x > 0 for x in (is29_a, is30_a)):
        raise ValueError("positive finite lower-pair saturation currents required")
    for beta in (beta29, beta30):
        if math.isnan(beta) or beta <= 1:
            raise ValueError("lower-pair beta must exceed one or be positive infinity")
    if not isinstance(cutoff_inputs, dict) or "tail_v" in cutoff_inputs:
        raise ValueError("cutoff_inputs must omit TAIL")
    cutoff = conditional_coupled_cutoff_dc(**cutoff_inputs, tail_v=None)
    tail_current_a = cutoff["q28_collector_current_a_candidate"]
    if tail_current_a <= 0:
        raise ValueError("Q28 current below positive domain")
    vt = thermal_voltage_v(cutoff["temperature_k_imposed"])
    inv29 = 0 if math.isinf(beta29) else 1 / beta29
    inv30 = 0 if math.isinf(beta30) else 1 / beta30
    base_fraction29 = inv29 / (1 + inv29)  # Ib/Ie = 1/(beta+1)
    base_fraction30 = inv30 / (1 + inv30)
    r30_bottom = r76 + r73_bottom_side_to_wiper_ohm
    log_weight_ratio = (math.log(is29_a) - math.log(is30_a)
                        + math.log1p(inv29) - math.log1p(inv30))

    def split_residual(fraction29: float) -> float:
        ib29 = tail_current_a * fraction29 * base_fraction29
        ib30 = tail_current_a * (1 - fraction29) * base_fraction30
        base_difference_v = -r54 * ib29 + r30_bottom * ib30
        return (math.log(fraction29) - math.log1p(-fraction29)
                - log_weight_ratio - base_difference_v / vt)

    low, high = 0.0, 1.0
    for _ in range(100):
        middle = (low + high) / 2
        if middle == low or middle == high:
            break
        if split_residual(middle) < 0:
            low = middle
        else:
            high = middle
    share29 = (low + high) / 2
    ib29 = tail_current_a * share29 * base_fraction29
    ib30 = tail_current_a * (1 - share29) * base_fraction30
    bottom_v = r61_ohm * (ladder_bottom_injection_a - ib29 - ib30)
    base29_v = bottom_v - r54 * ib29
    base30_v = bottom_v - r30_bottom * ib30
    lower = conditional_bottom_tail_dc(
        cutoff_inputs=cutoff_inputs, q29_base_v=base29_v, q30_base_v=base30_v,
        is29_a=is29_a, is30_a=is30_a, beta29=beta29, beta30=beta30)
    return {
        "bottom_v": bottom_v,
        "q29_base_v": base29_v,
        "q30_base_v": base30_v,
        "q29_base_current_a": ib29,
        "q30_base_current_a": ib30,
        "q29_emitter_current_fraction": share29,
        "tail_v": lower["tail_v"],
        "q28_forward_active_candidate": lower["q28_forward_active_candidate"],
        "q29_q30_collector_headroom_known": False,
        "bottom_inside_nominal_rails_candidate": -10 <= bottom_v <= 10,
        "q29_base_kcl_residual_a": (base29_v - bottom_v) / r54 + ib29,
        "q30_base_kcl_residual_a": (base30_v - bottom_v) / r30_bottom + ib30,
        "bottom_kcl_residual_a": (bottom_v / r61_ohm + ib29 + ib30
                                   - ladder_bottom_injection_a),
        "q29_current_coupling_residual_a": (
            ib29 - lower["q29_base_current_a"]),
        "q30_current_coupling_residual_a": (
            ib30 - lower["q30_base_current_a"]),
        "split_log_residual": split_residual(share29),
        "r61_ohm_selected": r61_ohm,
        "r73_bottom_side_to_wiper_ohm_imposed": r73_bottom_side_to_wiper_ohm,
        "r30_bottom_path_ohm": r30_bottom,
        "ladder_bottom_injection_a_imposed": ladder_bottom_injection_a,
        "lower_pair": lower,
        "ladder_collector_bias_known": False,
    }


if __name__ == "__main__":
    cutoff_inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                           scale_active_ohm=250, contour_pin16_v=0),
                         range_fraction_from_ground=0.1, is26_a=1e-14,
                         is28_a=1e-14, beta26=100, beta28=100,
                         temperature_k=298.15)
    for candidate, injection in ((200, 5.5e-3), (200000, 5.5e-6)):
        out = conditional_bottom_bias_dc(
            cutoff_inputs=cutoff_inputs, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100, r61_ohm=candidate,
            r73_bottom_side_to_wiper_ohm=500,
            ladder_bottom_injection_a=injection)
        print(json.dumps({key: value for key, value in out.items()
                          if key != "lower_pair"}, indent=2))
