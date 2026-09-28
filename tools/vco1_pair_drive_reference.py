"""Conditional DC drive of the CA3046 Qa/Qb bases on the Model D old VCO board.

Assumes ideal IC1, fixed -5 V rail, negligible base currents and open C2 at DC.
R42's effect on IC1, moving frequency trim, and device mismatch are excluded.
This yields a base-voltage increment, never a frequency or current estimate.
Sources: SVC-9 Fig. 9-3 (PDF p. 5) and Table 7-5 (PDF pp. 24-25).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from vco1_cv_reference import ideal_ic1_delta_v


GRAPH_PATH = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ramp_graph.json"


def ideal_pair_base_gain(r8_fraction_from_low: float) -> float:
    """Return d(V_Qb - V_Qa)/d(V_IC1_out) for an unloaded DC divider."""
    if not math.isfinite(r8_fraction_from_low) or not 0 <= r8_fraction_from_low <= 1:
        raise ValueError("R8 wiper fraction must be finite and within 0..1")
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["parts"]}
    if parts["R8"]["terminals"] != {"high": "R8_TOP", "wiper": "QB_BASE", "low": "R8_BOTTOM"}:
        raise ValueError("R8 topology is not the traced VCO 1 network")
    if set(parts["R9"]["terminals"].values()) != {"IC1_OUT", "R8_TOP"}:
        raise ValueError("R9 topology is not the traced VCO 1 network")
    if set(parts["R19"]["terminals"].values()) != {"R8_BOTTOM", "NEG5_V"}:
        raise ValueError("R19 topology is not the traced VCO 1 network")
    if set(parts["R7"]["terminals"].values()) != {"QA_BASE", "NEG5_V"}:
        raise ValueError("Qa reference topology is not the traced VCO 1 network")
    r8 = parts["R8"]["value_end_to_end"]
    r9 = parts["R9"]["value"]
    r19 = parts["R19"]["value"]
    if any(not isinstance(r, (int, float)) or not math.isfinite(r) or r <= 0 for r in (r8, r9, r19)):
        raise ValueError("divider resistances must be finite and positive")
    return (r19 + r8_fraction_from_low * r8) / (r9 + r8 + r19)


def ideal_pair_base_delta_v(control_deltas_v: dict[str, float], r8_fraction_from_low: float) -> float:
    """Return conditional DC delta of V_Qb - V_Qa, not an octave law."""
    return ideal_pair_base_gain(r8_fraction_from_low) * ideal_ic1_delta_v(control_deltas_v)


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r8-fraction", type=float, required=True, help="0 at -5 V side, 1 at IC1 side")
    for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range"):
        parser.add_argument(f"--{name.replace('_', '-')}-v", type=float, default=0.0)
    args = parser.parse_args()
    deltas = {
        name.upper(): getattr(args, f"{name}_v")
        for name in ("bend", "tune", "keyboard", "mod", "ext", "osc1_range")
    }
    try:
        gain = ideal_pair_base_gain(args.r8_fraction)
        ic1_delta = ideal_ic1_delta_v(deltas)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({
        "model": "ideal_incremental_Qa_Qb_DC_drive_only",
        "control_deltas_v": deltas,
        "r8_fraction_from_low": args.r8_fraction,
        "delta_ic1_output_v": ic1_delta,
        "delta_qb_minus_qa_base_v": gain * ic1_delta,
        "converts_to_current_or_frequency": False,
        "excluded": ["base currents", "C2 dynamics", "R42 feedback", "R11 trim motion", "rail movement", "transistor mismatch"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
