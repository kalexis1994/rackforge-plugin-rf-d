"""Conditional DC Q26/Q28 load line, SVC-9 Fig. 9-11 and Table 7-8.

The Q26 base, junction temperature, both saturation currents and TAIL
voltage are imposed. The result is a headroom-checked ideal-law scenario,
not an inferred Model D cutoff current or calibration.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from semiconductor_ideal import thermal_voltage_v


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_cutoff_q26_q28.json"


def _circuit() -> tuple[float, float, float, float, float, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    p, rails = data["parts"], data["rails_v"]
    values = (p["R39"]["ohm"], p["R46"]["ohm"], p["R45"]["ohm"],
              p["R60"]["ohm"], rails["positive"], rails["negative"])
    if (data["schematic"]["figure"], data["parts_list"]["table"], values,
            p["Q26"]["emitter"], p["Q28"]["base"]) != (
                "9-11", "7-8", (10000, 68000, 330, 680, 10, -10),
                "SHARED", "SHARED"):
        raise ValueError("Q26/Q28 evidence differs from documented topology")
    return values


def _exponential_current(is_a: float, exponent: float) -> float:
    if exponent > 709:
        return math.inf
    return is_a * math.exp(exponent)


def conditional_cutoff_current(*, range_fraction_from_ground: float,
                               q26_base_v: float, is26_a: float, is28_a: float,
                               temperature_k: float, tail_v: float) -> dict:
    """Solve the ideal DC SHARED node and report Q26/Q28 forward-active flags.

    R39's loaded wiper is reduced to a Thevenin source. The PNP Q26 draws
    current from this source through R46; its infinite-beta emitter current
    equals collector current. Q28's base current is neglected.
    """
    r39, r46, r45, r60, plus, minus = _circuit()
    if (not math.isfinite(range_fraction_from_ground)
            or not 0 <= range_fraction_from_ground <= 1
            or not all(math.isfinite(v) for v in (q26_base_v, is26_a, is28_a, tail_v))
            or is26_a <= 0 or is28_a <= 0):
        raise ValueError("finite electrical fraction, voltages and positive saturation currents required")
    vt = thermal_voltage_v(temperature_k)
    fraction = range_fraction_from_ground
    range_thevenin_v = plus * fraction
    range_thevenin_ohm = r39 * fraction * (1 - fraction)
    source_ohm = r46 + range_thevenin_ohm

    def balance(shared_v: float) -> float:
        source_a = (range_thevenin_v - shared_v) / source_ohm
        q26_a = _exponential_current(is26_a, (shared_v - q26_base_v) / vt)
        return source_a - q26_a

    high_v = range_thevenin_v
    low_v = high_v - 1
    for _ in range(64):
        if balance(low_v) > 0:
            break
        low_v -= high_v - low_v
    else:
        raise ValueError("could not bracket the ideal shared-node load line")
    for _ in range(100):
        middle_v = (low_v + high_v) / 2
        if balance(middle_v) > 0:
            low_v = middle_v
        else:
            high_v = middle_v
    shared_v = (low_v + high_v) / 2
    q26_current_a = (range_thevenin_v - shared_v) / source_ohm
    q28_current_a = _exponential_current(is28_a, shared_v / vt)
    if not math.isfinite(q28_current_a):
        raise ValueError("ideal Q28 exponential exceeds finite numeric domain")
    q26_collector_v = minus + q26_current_a * r45
    q28_collector_v = tail_v - q28_current_a * r60
    return {
        "shared_node_v": shared_v,
        "range_thevenin_v": range_thevenin_v,
        "range_thevenin_ohm": range_thevenin_ohm,
        "source_total_ohm": source_ohm,
        "q26_collector_current_a": q26_current_a,
        "q28_collector_current_a_candidate_a": q28_current_a,
        "q26_collector_v": q26_collector_v,
        "q28_collector_v_candidate": q28_collector_v,
        "q26_forward_active_candidate": shared_v > q26_base_v and q26_collector_v < q26_base_v,
        "q28_forward_active_candidate": shared_v > 0 and q28_collector_v > shared_v,
        "loadline_residual_a": balance(shared_v),
        "temperature_k_imposed": temperature_k,
        "tail_v_imposed": tail_v,
        "absolute_device_parameters_known": False,
    }


if __name__ == "__main__":
    # The Is values, base voltage, tail voltage and temperature below are a
    # numerical illustration only, not a Model D parameter set.
    out = conditional_cutoff_current(range_fraction_from_ground=0.1,
                                     q26_base_v=0, is26_a=1e-14, is28_a=1e-14,
                                     temperature_k=298.15, tail_v=2)
    print(json.dumps(out, indent=2))
