"""Reproducible assumption sweep for the conditional active ladder DC model.

These are deliberately hypothetical corner cases, not measured populations.
"""

from __future__ import annotations

import json
from itertools import product

from filter_ladder_active_dc_reference import UPPER, conditional_ladder_active_dc


RANGE_FRACTIONS = (0.02, 0.1, 0.5, 0.9)
BETAS = (50, 100, 200)
SATURATION_CURRENTS_A = (1e-15, 1e-14, 1e-13)
R61_CANDIDATES_OHM = (200, 200000)


def sweep() -> dict:
    """Evaluate all 72 grid points; retain failure type and worst margin."""
    results = {}
    for r61 in R61_CANDIDATES_OHM:
        cases = []
        for range_fraction, beta, saturation_a in product(
                RANGE_FRACTIONS, BETAS, SATURATION_CURRENTS_A):
            cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                            scale_active_ohm=250, contour_pin16_v=0),
                          range_fraction_from_ground=range_fraction,
                          is26_a=saturation_a, is28_a=saturation_a,
                          beta26=beta, beta28=beta, temperature_k=298.15)
            assumption = dict(range_fraction=range_fraction, beta=beta,
                              is_a=saturation_a)
            try:
                out = conditional_ladder_active_dc(
                    cutoff_inputs=cutoff, is29_a=saturation_a,
                    is30_a=saturation_a, beta29=beta, beta30=beta,
                    upper_is_a={name: saturation_a for name in UPPER},
                    upper_beta={name: beta for name in UPPER},
                    r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)
                cases.append(assumption | dict(
                    outcome="active_candidate" if out["all_ten_forward_active_candidates"]
                    else "headroom_or_bias_failure",
                    minimum_v_cb_v=min(out["v_cb_margins_v"].values()),
                    q28_forward_active_candidate=out["q28_forward_active_candidate"],
                    bottom_v=out["bottom_v"]))
            except ValueError as exc:
                cases.append(assumption | dict(outcome="solver_domain_error",
                                               reason=str(exc)))
        results[str(r61)] = cases
    return {
        "scope": "Hypothetical equal-parameter corner grid, not component tolerances",
        "cases_per_r61": len(RANGE_FRACTIONS) * len(BETAS) * len(SATURATION_CURRENTS_A),
        "r61_candidates_ohm": R61_CANDIDATES_OHM,
        "results": results,
    }


def summary(data: dict) -> dict:
    """Counts and numerical extrema without treating a sweep as evidence of parts."""
    counts = {}
    for r61, cases in data["results"].items():
        outcomes = {label: sum(case["outcome"] == label for case in cases)
                    for label in ("active_candidate", "headroom_or_bias_failure",
                                  "solver_domain_error")}
        finite = [case["minimum_v_cb_v"] for case in cases
                  if "minimum_v_cb_v" in case]
        counts[r61] = outcomes | {
            "minimum_margin_v": min(finite) if finite else None,
            "maximum_margin_v": max(finite) if finite else None,
        }
    return {"cases_per_r61": data["cases_per_r61"], "counts": counts,
            "interpretation": "numerical sensitivity only; physical R61 unresolved"}


if __name__ == "__main__":
    print(json.dumps(summary(sweep()), indent=2))
