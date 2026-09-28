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

from vco1_pair_drive_reference import ideal_pair_base_delta_v


K_BOLTZMANN_J_PER_K = 1.380649e-23
ELEMENTARY_CHARGE_C = 1.602176634e-19
GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"


def thermal_voltage_v(temperature_k: float) -> float:
    if not math.isfinite(temperature_k) or temperature_k <= 0:
        raise ValueError("junction temperature must be finite and above 0 K")
    return K_BOLTZMANN_J_PER_K * temperature_k / ELEMENTARY_CHARGE_C


def conditional_qb_collector_current_a() -> float:
    """R50 current if IC3 holds Qb collector at its -4 V reference."""
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
    drop_v = labels["GND"] - labels["NEG4_REF"]
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
        current_b = conditional_qb_collector_current_a()
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
        "qb_current_a_if_ic3_ideal": current_b,
        "qa_current_and_frequency_ratio": ratio,
        "absolute_current_or_frequency_known": False,
        "excluded": ["IC1 R42 feedback", "base and opamp input currents", "IC3 finite gain/limits", "BJT nonideality", "reset time", "ramp parasitics", "R20 temperature law"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
