"""Conditional ten-transistor ladder DC bias from SVC-9 Fig. 9-11.

Finite-beta base loads close the resistor spine. Forward-active BJT laws are
only evaluated candidates; failed collector/base headroom invalidates them.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_bottom_bias_dc_reference import conditional_bottom_bias_dc
from filter_ladder_spine_dc_reference import conditional_spine_bottom_dc
from semiconductor_ideal import thermal_voltage_v


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_ladder_dc_active_stacks.json"
LEFT = ("Q29", "Q23", "Q19", "Q10", "Q2")
RIGHT = ("Q30", "Q24", "Q20", "Q11", "Q3")
UPPER = LEFT[1:] + RIGHT[1:]


def conditional_ladder_active_dc(*, cutoff_inputs: dict,
                                 is29_a: float, is30_a: float,
                                 beta29: float, beta30: float,
                                 upper_is_a: dict[str, float],
                                 upper_beta: dict[str, float],
                                 r61_ohm: int,
                                 r73_bottom_side_to_wiper_ohm: float) -> dict:
    """Calculate a forward-active candidate and report all ten Vcb margins.

    Each upper transistor's Is and beta are explicitly imposed. The model
    has no Early effect, saturation law, tolerance distribution or dynamics.
    """
    topology = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if (tuple(topology["left_bottom_to_top"]) != LEFT
            or tuple(topology["right_bottom_to_top"]) != RIGHT
            or [tuple(x["pair"]) for x in topology["shared_bases_top_to_bottom"]]
            != [("Q2", "Q3"), ("Q10", "Q11"), ("Q19", "Q20"), ("Q23", "Q24")]):
        raise ValueError("active ladder topology differs from documentary source")
    if set(upper_is_a) != set(UPPER) or set(upper_beta) != set(UPPER):
        raise ValueError("provide Is and beta for all eight upper transistors")
    for name in UPPER:
        if not math.isfinite(upper_is_a[name]) or upper_is_a[name] <= 0:
            raise ValueError("upper Is must be positive and finite")
        beta = upper_beta[name]
        if math.isnan(beta) or beta <= 1:
            raise ValueError("upper beta must exceed one or be positive infinity")

    common = dict(cutoff_inputs=cutoff_inputs, is29_a=is29_a, is30_a=is30_a,
                  beta29=beta29, beta30=beta30, r61_ohm=r61_ohm,
                  r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm)
    probe = conditional_bottom_bias_dc(**common, ladder_bottom_injection_a=0)
    lower = probe["lower_pair"]
    currents = {}
    for side, start in ((LEFT, lower["q29_collector_current_a_candidate"]),
                        (RIGHT, lower["q30_collector_current_a_candidate"])):
        emitter = start
        for name in side[1:]:
            beta = upper_beta[name]
            base = 0.0 if math.isinf(beta) else emitter / (beta + 1)
            collector = emitter - base
            currents[name] = dict(emitter_a=emitter, collector_a=collector,
                                  base_a=base)
            emitter = collector
    pairs = (("Q2", "Q3"), ("Q10", "Q11"), ("Q19", "Q20"), ("Q23", "Q24"))
    withdrawals = tuple(sum(currents[name]["base_a"] for name in pair)
                        for pair in pairs)
    coupled = conditional_spine_bottom_dc(**common, tap_withdrawals_a=withdrawals)
    lower = coupled["lower"]["lower_pair"]
    vt = thermal_voltage_v(cutoff_inputs["temperature_k"])
    tap_voltages = coupled["spine"]["tap_voltages_top_to_bottom_v"]
    for pair, base_v in zip(pairs, tap_voltages):
        for name in pair:
            device = currents[name]
            device["base_v"] = base_v
            device["v_be_v"] = vt * math.log(device["collector_a"] / upper_is_a[name])
            device["emitter_v"] = base_v - device["v_be_v"]
    margins = {}
    for side, low_name, low_base in ((LEFT, "Q29", coupled["lower"]["q29_base_v"]),
                                     (RIGHT, "Q30", coupled["lower"]["q30_base_v"])):
        margins[low_name] = currents[side[1]]["emitter_v"] - low_base
        for lower_name, higher_name in zip(side[1:], side[2:]):
            collector_v = currents[higher_name]["emitter_v"]
            currents[lower_name]["collector_v"] = collector_v
            margins[lower_name] = collector_v - currents[lower_name]["base_v"]
        currents[side[-1]]["collector_v"] = 10
        margins[side[-1]] = 10 - currents[side[-1]]["base_v"]
    for name in UPPER:
        currents[name]["v_cb_v"] = margins[name]
    return {
        "tap_withdrawals_a_derived": withdrawals,
        "upper_devices": currents,
        "v_cb_margins_v": margins,
        "all_ten_forward_active_candidates": all(v >= 0 for v in margins.values())
            and all(currents[name]["v_be_v"] > 0 for name in UPPER)
            and coupled["lower"]["lower_pair"]["q29_be_forward_biased_candidate"]
            and coupled["lower"]["lower_pair"]["q30_be_forward_biased_candidate"]
            and coupled["q28_forward_active_candidate"],
        "q28_forward_active_candidate": coupled["q28_forward_active_candidate"],
        "bottom_v": coupled["bottom_v"],
        "tail_v": coupled["tail_v"],
        "bottom_injection_a": coupled["bottom_injection_a"],
        "spine": coupled["spine"],
        "lower": coupled["lower"],
        "upper_device_parameters_imposed": True,
        "early_and_saturation_not_modeled": True,
        "physical_r61_unresolved": True,
    }


if __name__ == "__main__":
    cutoff = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                    scale_active_ohm=250, contour_pin16_v=0),
                  range_fraction_from_ground=0.1, is26_a=1e-14,
                  is28_a=1e-14, beta26=100, beta28=100, temperature_k=298.15)
    for candidate in (200, 200000):
        result = conditional_ladder_active_dc(
            cutoff_inputs=cutoff, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
        print(json.dumps({"r61_ohm": candidate, "bottom_v": result["bottom_v"],
                          "tap_withdrawals_a": result["tap_withdrawals_a_derived"],
                          "v_cb_margins_v": result["v_cb_margins_v"],
                          "all_ten_forward_active_candidates": result[
                              "all_ten_forward_active_candidates"]}, indent=2))
