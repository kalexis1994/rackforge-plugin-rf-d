"""Conditional DC sensitivity of the shared -4 V reference on Fig. 9-3.

Positive external current means net current leaving the divider node into
the three oscillator circuits. It is an imposed scenario, not a prediction
of their transistor or op-amp currents. Source: SVC-9 PDF p. 5, Fig. 9-3.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


EVIDENCE_PATH = Path(__file__).resolve().parents[1] / "evidence" / "neg4_reference_loads.json"


def divider_model() -> tuple[float, float]:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    legs = {part["ref"]: part for part in evidence["divider"]}
    if set(legs) != {"R166", "R174"}:
        raise ValueError("reference divider evidence has changed")
    if legs["R166"]["other_node"] != "NEG10_V" or legs["R174"]["other_node"] != "GND":
        raise ValueError("reference divider topology has changed")
    r166, r174 = (legs[ref]["value_ohm"] for ref in ("R166", "R174"))
    if any(not isinstance(r, (float, int)) or not math.isfinite(r) or r <= 0 for r in (r166, r174)):
        raise ValueError("divider resistances must be finite and positive")
    labels = evidence["supply_labels_v"]
    v_th = (labels["NEG10_V"] / r166 + labels["GND"] / r174) / (1 / r166 + 1 / r174)
    r_th = 1 / (1 / r166 + 1 / r174)
    return v_th, r_th


def conditional_reference_v(external_current_a: float) -> float:
    """Thevenin result for imposed signed net current leaving NEG4_REF."""
    if not isinstance(external_current_a, (int, float)) or not math.isfinite(external_current_a):
        raise ValueError("external current must be finite")
    v_th, r_th = divider_model()
    return v_th - r_th * external_current_a


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-current-ua", type=float, required=True,
                        help="signed, imposed net current leaving the -4 V node")
    args = parser.parse_args()
    try:
        v_th, r_th = divider_model()
        conditional_v = conditional_reference_v(args.external_current_ua * 1e-6)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({
        "model": "conditional_shared_reference_DC_Thevenin",
        "unloaded_reference_v": v_th,
        "thevenin_resistance_ohm": r_th,
        "imposed_external_current_ua_positive_leaves_node": args.external_current_ua,
        "conditional_loaded_reference_v": conditional_v,
        "actual_external_current_or_loaded_reference_known": False,
        "excluded": ["transistor base currents", "741 input bias", "supply regulation", "tolerances", "C14 dynamics"],
    }, indent=2))


if __name__ == "__main__":
    run_cli()
