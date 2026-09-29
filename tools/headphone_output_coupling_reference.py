"""Isolated board-3 C21/R56 boundary, driven from an imposed ideal amp node."""

from __future__ import annotations

import json
import math
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "headphone_output_board3.json"


def _output_parts() -> tuple[float, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    values = {row["ref"]: (row["farad"] if "farad" in row else row["ohm"])
              for row in data["components"]}
    if (data["source"] != "SVC-9 Fig. 9-8 board 3 headphone amplifier, PDF p. 10 (SVC-204D PDF p. 66)"
            or values != {"C21": 400e-6, "R56": 390}):
        raise ValueError("headphone output differs from schematic")
    return values["C21"], values["R56"]


def _shunt_conductance_s(tip_load_ohm: float | None,
                         ring_load_ohm: float | None) -> float:
    _, r56 = _output_parts()
    conductance = 1/r56
    for load in (tip_load_ohm, ring_load_ohm):
        if load is not None:
            if not math.isfinite(load) or load <= 0:
                raise ValueError("tip/ring loads must be positive finite resistance or None")
            conductance += 1/load
    return conductance


def output_corner_hz(*, tip_load_ohm: float | None = None,
                     ring_load_ohm: float | None = None) -> float:
    """Ideal-source single-pole corner; tip and ring share board-3 pin 8."""
    cap, _ = _output_parts()
    return _shunt_conductance_s(tip_load_ohm, ring_load_ohm)/(2*math.pi*cap)


def output_ac(*, frequency_hz: float, tip_load_ohm: float | None = None,
              ring_load_ohm: float | None = None) -> dict:
    """Complex J7 voltage and currents for 1 V incremental pre-C21 drive."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    cap, _ = _output_parts()
    conductance = _shunt_conductance_s(tip_load_ohm, ring_load_ohm)
    y_cap = 2j*math.pi*frequency_hz*cap
    jack_v = y_cap/(conductance+y_cap)
    cap_current = y_cap*(1-jack_v)
    load_current = conductance*jack_v
    return {"frequency_hz": frequency_hz,
            "j7_tip_v_per_pre_c21_v": jack_v,
            "j7_ring_v_per_pre_c21_v": jack_v,
            "c21_current_a_per_pre_c21_v": cap_current,
            "total_shunt_current_a_per_pre_c21_v": load_current,
            "max_linear_kcl_residual_a_per_pre_c21_v": abs(cap_current-load_current),
            "total_shunt_conductance_s": conductance,
            "active_amp_output_resistance_assumed_zero": True}


def output_backward_euler_step(*, previous_capacitor_pre_minus_jack_v: float,
                               pre_c21_v: float, dt_s: float,
                               tip_load_ohm: float | None = None,
                               ring_load_ohm: float | None = None) -> dict:
    """One passive step; the active amp voltage is imposed at C21's left side."""
    if (not math.isfinite(previous_capacitor_pre_minus_jack_v)
            or not math.isfinite(pre_c21_v)
            or not math.isfinite(dt_s) or dt_s <= 0):
        raise ValueError("finite voltages and positive finite dt required")
    cap, _ = _output_parts()
    conductance = _shunt_conductance_s(tip_load_ohm, ring_load_ohm)
    cap_admittance = cap/dt_s
    jack_v = cap_admittance*(pre_c21_v-previous_capacitor_pre_minus_jack_v)/(cap_admittance+conductance)
    next_cap_v = pre_c21_v-jack_v
    cap_current = cap_admittance*(next_cap_v-previous_capacitor_pre_minus_jack_v)
    shunt_current = conductance*jack_v
    return {"j7_tip_v": jack_v, "j7_ring_v": jack_v,
            "capacitor_pre_minus_jack_v": next_cap_v,
            "c21_current_a": cap_current,
            "total_shunt_current_a": shunt_current,
            "max_charge_kcl_residual_a": abs(cap_current-shunt_current)}
