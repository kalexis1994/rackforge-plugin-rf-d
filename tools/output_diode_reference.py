"""Conditioned 1N458A Shockley family, not a vintage-device fit."""

from __future__ import annotations

import json
import math
from pathlib import Path

from semiconductor_ideal import thermal_voltage_v


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "output_diode_1n458a.json"


def diode_model_from_reference(*, ideality: float,
                               forward_voltage_at_100ma_v: float,
                               temperature_k: float) -> dict[str, float]:
    """Infer one Is for an imposed point satisfying the manufacturer bounds."""
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    limits = data["limits_25c"]
    if (limits["forward_current_a"] != 0.1
            or limits["forward_voltage_max_v"] != 1.0
            or limits["reverse_leakage_max_a"] != 25e-9):
        raise ValueError("1N458A documentary limits changed")
    if (not all(math.isfinite(v) for v in (
            ideality, forward_voltage_at_100ma_v, temperature_k))
            or not 1 <= ideality <= 2
            or not 0 < forward_voltage_at_100ma_v <= 1.0):
        raise ValueError("finite exploratory ideality and forward point required")
    vt = thermal_voltage_v(temperature_k)
    is_a = limits["forward_current_a"] / math.expm1(
        forward_voltage_at_100ma_v/(ideality*vt))
    if is_a > limits["reverse_leakage_max_a"]:
        raise ValueError("implied reverse saturation exceeds data-sheet bound")
    return {"is_a": is_a, "ideality": ideality,
            "reference_forward_v": forward_voltage_at_100ma_v,
            "reference_current_a": limits["forward_current_a"],
            "temperature_k": temperature_k,
            "manufacturer_leakage_bound_a": limits["reverse_leakage_max_a"]}


def diode_current_a(v_anode_minus_cathode: float, *,
                    model: dict[str, float], vt: float) -> float:
    """Signed anode-to-cathode current under one imposed Shockley law."""
    exponent = v_anode_minus_cathode/(model["ideality"]*vt)
    if not math.isfinite(exponent) or exponent > 45:
        raise ValueError("diode trial exceeds finite exponential domain")
    return model["is_a"]*math.expm1(exponent)
