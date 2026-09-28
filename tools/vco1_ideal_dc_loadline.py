"""Explore the reduced, ideal DC load line of the old VCO 1 CA3046 board.

This couples IC1/R11/R20/R42, the Qa/Qb ideal exponential ratio, Qc's
emitter current and IC3's conditional Qb current. It does not solve IC3's
output, Qc base bias, device saturation or actual tuning. Source: SVC-9
PDF p. 5, Fig. 9-3; TI SLOA059B PDF p. 6, Eqs. (3)-(4).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from neg4_reference import conditional_reference_v
from vco1_cv_reference import load_evidence
from vco1_ideal_pair_reference import thermal_voltage_v
from vco1_pair_drive_reference import ideal_pair_base_gain


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"


def circuit_values() -> dict:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    expected = {
        "R20": {"IC1_OUT", "IC1_SUM"},
        "R42": {"IC1_SUM", "QC_EMITTER"},
        "R79": {"QC_EMITTER", "NEG10_V"},
        "R37": {"R37_TOP", "NEG10_V"},
        "R50": {"GND", "QB_COLLECTOR"},
        "R69": {"IC3_OUT", "QC_BASE"},
    }
    for ref, nodes in expected.items():
        if set(parts[ref]["terminals"].values()) != nodes:
            raise ValueError(f"{ref} no longer has the traced DC topology")
    if parts["R11"]["terminals"] != {"high": "IC1_SUM", "wiper": "IC1_SUM", "low": "R37_TOP"}:
        raise ValueError("R11 wiper topology has changed")
    if parts["IC1"]["terminals"]["noninverting"] != "IC1_PLUS":
        raise ValueError("IC1 reference topology has changed")
    if parts["IC1"]["terminals"]["positive_supply"] != "GND" or parts["IC1"]["terminals"]["negative_supply"] != "NEG10_V":
        raise ValueError("IC1 schematic supply topology has changed")
    if parts["IC3"]["terminals"]["positive_supply"] != "POS10_V" or parts["IC3"]["terminals"]["negative_supply"] != "NEG10_V":
        raise ValueError("IC3 schematic supply topology has changed")
    if parts["R78"]["terminals"] != {"a": "QC_BASE", "b": "NEG10_V"}:
        raise ValueError("R78 DC topology has changed")
    dc_branches = [branch["resistance_ohm"] for branch in parts["R78"]["branches"]
                   if branch["kind"] == "resistor"]
    if len(dc_branches) != 1 or any(branch["kind"] not in ("resistor", "series_rc")
                                     for branch in parts["R78"]["branches"]):
        raise ValueError("R78 DC resistor branch is unresolved")
    if set(parts["R10"]["terminals"].values()) != {"IC1_PLUS", "NEG5_V"}:
        raise ValueError("IC1 noninverting reference has changed")
    evidence = load_evidence()
    inputs = {part["source_node"]: part["schematic"] for part in evidence["components"]
              if part["role"] == "cv_input"}
    if len(inputs) != 6:
        raise ValueError("expected six documented VCO 1 control resistors")
    values = {ref: parts[ref]["value"] for ref in expected}
    values["R11_total"] = parts["R11"]["value_end_to_end"]
    values["R78_dc"] = dc_branches[0]
    values["inputs"] = inputs
    values["V_NEG5"] = graph["schematic_voltage_labels_v"]["NEG5_V"]
    values["V_NEG10"] = graph["schematic_voltage_labels_v"]["NEG10_V"]
    values["V_GND"] = graph["schematic_voltage_labels_v"]["GND"]
    values["V_POS10"] = graph["schematic_voltage_labels_v"]["POS10_V"]
    if any(not math.isfinite(v) or v <= 0 for key, v in values.items()
           if key.startswith("R")):
        raise ValueError("documented resistances must be positive")
    return values


def evaluate_current(qa_current_a: float, control_voltages_v: dict[str, float],
                     r11_active_ohm: float, r8_fraction: float, reference_v: float,
                     mismatch_is_ratio: float, temperature_k: float,
                     values: dict | None = None) -> dict:
    """Return DC KCL/ideal-pair residual for an imposed positive Qa current."""
    values = circuit_values() if values is None else values
    if set(control_voltages_v) != set(values["inputs"]):
        raise ValueError("all six documented control-line voltages are required")
    numbers = [qa_current_a, r11_active_ohm, r8_fraction, reference_v,
               mismatch_is_ratio, temperature_k, *control_voltages_v.values()]
    if any(not isinstance(n, (int, float)) or not math.isfinite(n) for n in numbers):
        raise ValueError("scenario parameters must be finite")
    if qa_current_a <= 0 or mismatch_is_ratio <= 0:
        raise ValueError("Qa current and saturation-current ratio must be positive")
    if not 0 <= r11_active_ohm <= values["R11_total"]:
        raise ValueError("R11 active resistance must be within 0..1000 ohm")
    gain = ideal_pair_base_gain(r8_fraction)
    vt = thermal_voltage_v(temperature_k)
    vs, vn, vg = (values[key] for key in ("V_NEG5", "V_NEG10", "V_GND"))
    if not vn < reference_v < vg:
        raise ValueError("conditional IC3 reference must lie between -10 V and ground")
    ib = (vg - reference_v) / values["R50"]
    emitter = ((qa_current_a + ib) + vn / values["R79"] + vs / values["R42"]) / (
        1 / values["R79"] + 1 / values["R42"])
    control_sum_a = sum((vs - control_voltages_v[name]) / resistance
                        for name, resistance in values["inputs"].items())
    trim_current_a = (vs - vn) / (values["R37"] + r11_active_ohm)
    ic1_out = vs + values["R20"] * (control_sum_a + trim_current_a +
                                      (vs - emitter) / values["R42"])
    qb_base = vs + gain * (ic1_out - vs)
    qa_base = vs
    log_pair_residual = (math.log(qa_current_a) - math.log(ib) - math.log(mismatch_is_ratio)
                         - (qa_base - qb_base) / vt)
    return {
        "qa_current_a_imposed": qa_current_a,
        "qb_current_a_conditional": ib,
        "qc_emitter_v": emitter,
        "ic1_sum_v_ideal": vs,
        "ic1_output_v": ic1_out,
        "qa_base_v_ideal": qa_base,
        "qb_base_v_ideal": qb_base,
        "control_current_from_sum_a": control_sum_a,
        "trim_current_from_sum_a": trim_current_a,
        "log_pair_residual": log_pair_residual,
        "ic1_output_within_schematic_rails": vn < ic1_out < vg,
        "qc_emitter_between_minus10_and_minus5": vn < emitter < vs,
    }


def conditional_qc_drive(root: dict, qc_vbe_v: float, values: dict | None = None) -> dict:
    """Required IC3 output for imposed Qc V_BE with zero Qc base current.

    R78's series-RC branch is open in DC. This is a necessary voltage check,
    not evidence that the CA3046 or 741 can attain the point under load.
    """
    values = circuit_values() if values is None else values
    if not isinstance(qc_vbe_v, (int, float)) or not math.isfinite(qc_vbe_v) or qc_vbe_v <= 0:
        raise ValueError("hypothetical Qc V_BE must be finite and positive")
    base_v = root["qc_emitter_v"] + qc_vbe_v
    vn = values["V_NEG10"]
    r78_current_a = (base_v - vn) / values["R78_dc"]
    ic3_output_v = base_v + values["R69"] * r78_current_a
    return {
        "qc_vbe_v_hypothetical": qc_vbe_v,
        "qc_base_v_conditional": base_v,
        "r78_resistive_branch_current_a_conditional": r78_current_a,
        "ic3_output_v_required_if_zero_base_current": ic3_output_v,
        "ic3_output_between_schematic_rails": vn < ic3_output_v < values["V_POS10"],
    }


def find_candidate_roots(control_voltages_v: dict[str, float], r11_active_ohm: float,
                         r8_fraction: float, reference_v: float, mismatch_is_ratio: float,
                         temperature_k: float, minimum_qa_a: float = 1e-9,
                         maximum_qa_a: float = 1e-3) -> list[dict]:
    """Find all sign crossings in an explicit numeric search interval."""
    if not all(math.isfinite(x) and x > 0 for x in (minimum_qa_a, maximum_qa_a)):
        raise ValueError("search-current bounds must be finite and positive")
    if minimum_qa_a >= maximum_qa_a:
        raise ValueError("search-current minimum must be below maximum")
    values = circuit_values()

    def state(current_a: float) -> dict:
        return evaluate_current(current_a, control_voltages_v, r11_active_ohm,
                                r8_fraction, reference_v, mismatch_is_ratio,
                                temperature_k, values)

    steps = 512
    lo_log, hi_log = math.log(minimum_qa_a), math.log(maximum_qa_a)
    samples = [math.exp(lo_log + (hi_log - lo_log) * i / steps) for i in range(steps + 1)]
    roots = []
    previous_x, previous_f = samples[0], state(samples[0])["log_pair_residual"]
    for x in samples[1:]:
        f = state(x)["log_pair_residual"]
        if previous_f == 0:
            roots.append(state(previous_x))
        elif f == 0:
            roots.append(state(x))
        elif (previous_f < 0 < f) or (f < 0 < previous_f):
            left, right, left_f = previous_x, x, previous_f
            for _ in range(70):
                mid = (left + right) / 2
                mid_f = state(mid)["log_pair_residual"]
                if (left_f < 0 < mid_f) or (mid_f < 0 < left_f):
                    right = mid
                else:
                    left, left_f = mid, mid_f
            roots.append(state((left + right) / 2))
        previous_x, previous_f = x, f
    return [root for i, root in enumerate(roots)
            if i == 0 or abs(root["qa_current_a_imposed"] - roots[i - 1]["qa_current_a_imposed"]) >
            1e-8 * root["qa_current_a_imposed"]]


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range"):
        parser.add_argument(f"--{name.replace('_', '-')}-v", type=float, required=True)
    parser.add_argument("--r11-active-ohm", type=float, required=True)
    parser.add_argument("--r8-fraction", type=float, required=True)
    parser.add_argument("--external-reference-current-ua", type=float, required=True,
                        help="imposed signed sum leaving the shared -4 V divider")
    parser.add_argument("--mismatch-is-ratio", type=float, required=True,
                        help="hypothetical I_Sa/I_Sb, not measured")
    parser.add_argument("--temperature-c", type=float, required=True,
                        help="hypothetical junction temperature")
    parser.add_argument("--qc-vbe-v", type=float, required=True,
                        help="hypothetical Qc base-emitter voltage, not measured")
    parser.add_argument("--search-min-ua", type=float, default=0.001)
    parser.add_argument("--search-max-ua", type=float, default=1000)
    args = parser.parse_args()
    controls = {name.upper(): getattr(args, f"{name}_v")
                for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range")}
    try:
        reference_v = conditional_reference_v(args.external_reference_current_ua * 1e-6)
        roots = find_candidate_roots(controls, args.r11_active_ohm, args.r8_fraction,
                                     reference_v, args.mismatch_is_ratio,
                                     args.temperature_c + 273.15,
                                     args.search_min_ua * 1e-6, args.search_max_ua * 1e-6)
        roots = [{**root, "qc_drive": conditional_qc_drive(root, args.qc_vbe_v)} for root in roots]
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({
        "model": "conditional_reduced_ideal_DC_loadline_only",
        "control_line_voltages_v_imposed": controls,
        "r11_active_ohm_imposed": args.r11_active_ohm,
        "r8_fraction_imposed": args.r8_fraction,
        "reference_external_current_ua_imposed": args.external_reference_current_ua,
        "reference_v_conditional": reference_v,
        "saturation_current_ratio_imposed": args.mismatch_is_ratio,
        "junction_temperature_c_hypothetical": args.temperature_c,
        "qc_vbe_v_hypothetical": args.qc_vbe_v,
        "numeric_search_current_ua": [args.search_min_ua, args.search_max_ua],
        "candidate_roots_within_search": roots,
        "absolute_tuning_or_full_operating_point_known": False,
        "excluded": ["CA3046 absolute saturation currents and Qc V_BE law",
                     "device finite beta and saturation", "741 offset, bias, loaded output swing and compensation",
                     "rail regulation", "C2/R78/C14 dynamics", "reset and loaded ramp"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
