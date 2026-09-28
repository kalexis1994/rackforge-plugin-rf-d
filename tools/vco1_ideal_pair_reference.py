"""Conditional BJT-pair frequency *ratio* for the old Model D VCO 1.

Combines separately documented ideal IC1, unloaded R8 divider, ideal IC3
feedback, BJT exponential law and ideal C1 event timing. The result is a
normalized ratio, not an absolute tuning curve or a vintage measurement.
Sources: SVC-9 Fig. 9-3 PDF p. 5, Table 7-5 pp. 24-26;
TI SLOA059B PDF p. 6, Equations (3)-(4).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from semiconductor_ideal import thermal_voltage_v
from vco1_pair_drive_reference import ideal_pair_base_delta_v


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"


def unloaded_neg4_reference_v() -> float:
    """R166/R174 divider voltage at DC with no other -4 V rail load."""
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    if set(parts["R166"]["terminals"].values()) != {"NEG10_V", "NEG4_REF"}:
        raise ValueError("R166 is not the documented reference divider leg")
    if set(parts["R174"]["terminals"].values()) != {"NEG4_REF", "GND"}:
        raise ValueError("R174 is not the documented reference divider leg")
    if set(parts["C14"]["terminals"].values()) != {"NEG4_REF", "GND"}:
        raise ValueError("C14 is not the documented reference bypass")
    r166 = parts["R166"]["value"]
    r174 = parts["R174"]["value"]
    if any(not isinstance(r, (int, float)) or not math.isfinite(r) or r <= 0 for r in (r166, r174)):
        raise ValueError("reference divider resistances must be finite and positive")
    labels = graph["schematic_voltage_labels_v"]
    return (labels["NEG10_V"] * r174 + labels["GND"] * r166) / (r166 + r174)


def conditional_qb_collector_current_a(reference_v: float | None = None) -> float:
    """R50 current if IC3 holds Qb collector at a specified reference.

    The default is the schematic's rounded -4 V label. It is not an observed
    voltage or a prediction of the loaded reference divider.
    """
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    if parts["IC3"]["terminals"]["noninverting"] != "QB_COLLECTOR":
        raise ValueError("IC3 feedback sense is not Qb collector")
    if parts["IC3"]["terminals"]["inverting"] != "NEG4_REF":
        raise ValueError("IC3 reference is not the documented -4 V node")
    if set(parts["R50"]["terminals"].values()) != {"GND", "QB_COLLECTOR"}:
        raise ValueError("R50 is not the documented Qb collector load")
    load_ohm = parts["R50"]["value"]
    labels = graph["schematic_voltage_labels_v"]
    if not math.isfinite(load_ohm) or load_ohm <= 0:
        raise ValueError("R50 must be finite and positive")
    reference_v = labels["NEG4_REF"] if reference_v is None else reference_v
    if not isinstance(reference_v, (int, float)) or not math.isfinite(reference_v):
        raise ValueError("reference voltage must be finite")
    drop_v = labels["GND"] - reference_v
    if not math.isfinite(drop_v) or drop_v <= 0:
        raise ValueError("the documented Qb collector drop must be positive")
    return drop_v / load_ohm


def ideal_qa_current_and_frequency_ratio(
    control_deltas_v: dict[str, float], r8_fraction_from_low: float, temperature_k: float = 298.15
) -> float:
    """Return change relative to the same circuit state, under the stated ideals."""
    conditional_qb_collector_current_a()  # Check the reference loop evidence.
    delta_qb_minus_qa = ideal_pair_base_delta_v(control_deltas_v, r8_fraction_from_low)
    exponent = -delta_qb_minus_qa / thermal_voltage_v(temperature_k)
    try:
        ratio = math.exp(exponent)
    except OverflowError as error:
        raise ValueError("ideal exponential leaves the finite numeric domain") from error
    if not math.isfinite(ratio) or ratio == 0:
        raise ValueError("ideal exponential leaves the finite numeric domain")
    return ratio


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r8-fraction", type=float, required=True, help="0 at -5 V side, 1 at IC1 side")
    parser.add_argument("--temperature-c", type=float, default=25.0, help="hypothetical junction temperature")
    for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range"):
        parser.add_argument(f"--{name.replace('_', '-')}-v", type=float, default=0.0)
    args = parser.parse_args()
    deltas = {
        name.upper(): getattr(args, f"{name}_v")
        for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range")
    }
    temperature_k = args.temperature_c + 273.15
    try:
        current_b_label = conditional_qb_collector_current_a()
        unloaded_ref_v = unloaded_neg4_reference_v()
        current_b_unloaded = conditional_qb_collector_current_a(unloaded_ref_v)
        ratio = ideal_qa_current_and_frequency_ratio(deltas, args.r8_fraction, temperature_k)
        vt = thermal_voltage_v(temperature_k)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({
        "model": "conditional_ideal_CA3046_pair_normalized_only",
        "control_deltas_v": deltas,
        "r8_fraction_from_low": args.r8_fraction,
        "junction_temperature_c_hypothetical": args.temperature_c,
        "thermal_voltage_v": vt,
        "unloaded_r166_r174_reference_v": unloaded_ref_v,
        "qb_current_a_if_ic3_holds_minus4_label": current_b_label,
        "qb_current_a_if_ic3_holds_unloaded_divider": current_b_unloaded,
        "loaded_reference_and_actual_qb_current_known": False,
        "qa_current_and_frequency_ratio": ratio,
        "absolute_current_or_frequency_known": False,
        "excluded": ["IC1 R42 feedback", "base and opamp input currents", "IC3 finite gain/limits", "BJT nonideality", "reset time", "ramp parasitics", "R20 temperature law"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
