"""Ideal incremental IC1 summer for the documented CA3046 board.

Read component identity from evidence/vco1_ca3046_parts.json. This computes
only the ideal inverting op-amp *change* with a fixed non-inverting reference,
fixed trims, and no R42 positive feedback. It does not output VCO frequency.
Sources: SVC-204D Fig. 9-3, SVC-9 PDF pp. 5, 24-26.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


EVIDENCE_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ca3046_parts.json"


def load_evidence(path: Path = EVIDENCE_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = data["components"]
    by_ref = {}
    inputs = set()
    for part in parts:
        ref = part["ref"]
        if ref in by_ref:
            raise ValueError(f"duplicate designator: {ref}")
        by_ref[ref] = part
        status = part["status"]
        if status not in ("matched", "conflict"):
            raise ValueError(f"unknown evidence status for {ref}")
        if (part["schematic"] == part["bom"]) != (status == "matched"):
            raise ValueError(f"schematic/BOM status disagrees for {ref}")
        if part["unit"] in ("ohm", "farad"):
            for source in ("schematic", "bom"):
                value = part[source]
                if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                    raise ValueError(f"invalid {source} value for {ref}")
        if part["role"] == "cv_input":
            if part["target_node"] != "IC1_SUM":
                raise ValueError(f"unresolved CV target for {ref}")
            name = part["source_node"]
            if name in inputs:
                raise ValueError(f"duplicate control input: {name}")
            inputs.add(name)
    if by_ref["R20"]["role"] != "ic1_feedback_temperature_compensating":
        raise ValueError("R20 must be the verified IC1 feedback component")
    if by_ref["R21"]["source_node"] != "TUNE" or by_ref["R2"]["role"] != "pulse_former":
        raise ValueError("R21 and R2 must remain distinct")
    return data


def ideal_ic1_delta_v(control_deltas_v: dict[str, float], evidence: dict | None = None) -> float:
    """Return the fixed-temperature ideal op-amp delta, not a measured law.

    For a fixed virtual summing node: delta(Vout) = -Rf * sum(delta(Vin)/Ri).
    This excludes R11/R8 trim movement, IC1 limits and R42 feedback.
    """
    evidence = load_evidence() if evidence is None else evidence
    parts = evidence["components"]
    input_resistors = {
        part["source_node"]: part["schematic"]
        for part in parts if part["role"] == "cv_input"
    }
    unknown = set(control_deltas_v) - set(input_resistors)
    if unknown:
        raise ValueError(f"unknown control input: {', '.join(sorted(unknown))}")
    feedback_ohms = next(part["schematic"] for part in parts if part["ref"] == "R20")
    current_delta = 0.0
    for name, delta_v in control_deltas_v.items():
        if not math.isfinite(delta_v):
            raise ValueError(f"non-finite voltage delta for {name}")
        current_delta += delta_v / input_resistors[name]
    return -feedback_ohms * current_delta


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range"):
        parser.add_argument(f"--{name.replace('_', '-')}-v", type=float, default=0.0)
    args = parser.parse_args()
    deltas = {
        name.upper(): getattr(args, f"{name}_v")
        for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range")
    }
    try:
        evidence = load_evidence()
        delta_out = ideal_ic1_delta_v(deltas, evidence)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({
        "model": "ideal_incremental_IC1_summer_only",
        "control_deltas_v": deltas,
        "delta_ic1_output_v": delta_out,
        "converts_to_current_or_frequency": False,
        "excluded": ["R11/R8 trim motion", "R42 feedback", "IC1 limits", "temperature change"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
