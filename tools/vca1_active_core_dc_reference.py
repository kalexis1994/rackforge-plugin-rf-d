"""Conditional Q16/Q15/Q18 first-VCA DC with both BJT junctions.

The first balance wiper and far side of loudness R59 are voltage boundaries.
Second-VCA base currents are zero. This is an offline reference, not DSP.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _device, _solve_linear
from semiconductor_ideal import thermal_voltage_v


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "vca1_active_core.json"
NODES = ("Q16_BASE", "Q15_BASE", "PAIR_EMITTER", "Q18_COLLECTOR",
         "Q18_EMITTER", "Q16_COLLECTOR", "Q15_COLLECTOR", "Q18_BASE")
DEVICES = ("Q16", "Q15", "Q18")
EXPECTED = {"R14_BOARD4": 25, "R13": 120, "R19": 100, "R23": 100, "R22": 120,
            "R34": 820, "R35": 1000, "R36": 510, "R37": 6800,
            "R43": 270000, "R59": 68000}


def _parts() -> dict[str, float]:
    source = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parts = {row["ref"]: row["ohm"] for row in source["resistors"]}
    if (source["schematic"]["figure"], source["parts_list"]["table"],
            tuple(source["devices"]), tuple(source["dc_open_capacitors"]),
            parts) != ("9-11", "7-8", DEVICES, ("C6", "C15"), EXPECTED):
        raise ValueError("first-VCA core differs from documentary graph")
    return parts


def _evaluate(x: list[float], *, r: dict[str, float], wiper_v: float,
              loudness_v: float, minus_v: float, left_ohm: float,
              vt: float, is_a: dict[str, float], beta_forward: dict[str, float],
              beta_reverse: dict[str, float]) -> tuple[list[float], dict]:
    q16 = _device(x[0], x[5], x[2], is_a["Q16"],
                  beta_forward["Q16"], beta_reverse["Q16"], vt)
    q15 = _device(x[1], x[6], x[2], is_a["Q15"],
                  beta_forward["Q15"], beta_reverse["Q15"], vt)
    q18 = _device(x[7], x[3], x[4], is_a["Q18"],
                  beta_forward["Q18"], beta_reverse["Q18"], vt)
    # All rows use incoming minus outgoing; currents are amperes.
    residual = [
        (x[1] - x[0]) / r["R34"] - q16["base_a"],
        (wiper_v - x[1]) / r["R22"] + (x[0] - x[1]) / r["R34"]
        - x[1] / r["R36"] - q15["base_a"],
        q16["emitter_a"] + q15["emitter_a"]
        - (x[2] - x[3]) / r["R35"],
        (x[2] - x[3]) / r["R35"] - q18["collector_a"],
        q18["emitter_a"] - x[4] / r["R37"]
        - (x[4] - minus_v) / r["R43"],
        (wiper_v - x[5]) / (r["R19"] + left_ohm) - q16["collector_a"],
        (wiper_v - x[6]) / (r["R23"] + r["R14_BOARD4"] - left_ohm)
        - q15["collector_a"],
        (loudness_v - x[7]) / r["R59"] - q18["base_a"],
    ]
    return residual, {"Q16": q16, "Q15": q15, "Q18": q18}


def conditional_vca1_dc(*, wiper_v: float, loudness_v: float,
                        balance_left_ohm: float, is_a: dict[str, float],
                        beta_forward: dict[str, float],
                        beta_reverse: dict[str, float],
                        temperature_k: float, minus_v: float = -10.0) -> dict:
    """Solve first multiplier at explicitly imposed external boundaries."""
    if not all(math.isfinite(v) for v in (wiper_v, loudness_v, minus_v,
                                         balance_left_ohm)):
        raise ValueError("finite boundary voltages and trim resistance required")
    r = _parts()
    if not 0 <= balance_left_ohm <= r["R14_BOARD4"]:
        raise ValueError("balance segment outside 0..25 ohm")
    if set(is_a) != set(DEVICES) or set(beta_forward) != set(DEVICES) or set(beta_reverse) != set(DEVICES):
        raise ValueError("provide Is and both betas for Q16/Q15/Q18")
    if not all(math.isfinite(v) and v > 0 for v in is_a.values()):
        raise ValueError("positive finite Is required")
    if not all(math.isfinite(v) and v > 1 for v in beta_forward.values()):
        raise ValueError("finite forward beta > 1 required")
    if not all(math.isfinite(v) and v > 0 for v in beta_reverse.values()):
        raise ValueError("positive finite reverse beta required")
    vt = thermal_voltage_v(temperature_k)
    params = dict(r=r, wiper_v=wiper_v, loudness_v=loudness_v,
                  minus_v=minus_v, left_ohm=balance_left_ohm, vt=vt,
                  is_a=is_a, beta_forward=beta_forward,
                  beta_reverse=beta_reverse)
    base = wiper_v * r["R36"] / (r["R22"] + r["R36"])
    x = [base, base, base - 0.65, base - 1.2, -0.1,
         wiper_v - 0.05, wiper_v - 0.05, 0.6]
    if loudness_v <= 0.25:
        # Envelope near zero: both multipliers are almost off. Starting from
        # the conducting branch makes a finite-difference Jacobian singular.
        x = [base, base, base + 0.1, base + 0.1, -0.24,
             wiper_v, wiper_v, loudness_v]
    scales = [1e-5, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-5]
    for iteration in range(100):
        residual, devices = _evaluate(x, **params)
        error = max(abs(v / s) for v, s in zip(residual, scales))
        if max(abs(v) for v in residual) < 1e-12 and error < 1e-7:
            break
        jacobian = [[0.0] * 8 for _ in range(8)]
        for col in range(8):
            trial = x.copy()
            trial[col] += 1e-6
            shifted, _ = _evaluate(trial, **params)
            for row in range(8):
                jacobian[row][col] = (shifted[row] - residual[row]) / 1e-6 / scales[row]
        step = _solve_linear(jacobian, [-v / s for v, s in zip(residual, scales)])
        for power in range(30):
            proposed = [v + 0.5 ** power * dv for v, dv in zip(x, step)]
            try:
                new_residual, _ = _evaluate(proposed, **params)
            except ValueError:
                continue
            if max(abs(v / s) for v, s in zip(new_residual, scales)) < error:
                x = proposed
                break
        else:
            raise ValueError("first-VCA Newton step did not reduce KCL residual")
    else:
        raise ValueError("first-VCA Newton iteration did not converge")
    residual, devices = _evaluate(x, **params)
    conductance = [[0.0] * 8 for _ in range(8)]
    for col in range(8):
        high_x, low_x = x.copy(), x.copy()
        high_x[col] += 1e-6
        low_x[col] -= 1e-6
        high, _ = _evaluate(high_x, **params)
        low, _ = _evaluate(low_x, **params)
        for row in range(8):
            conductance[row][col] = (high[row] - low[row]) / 2e-6
    return {
        "nodes_v": dict(zip(NODES, x)), "devices": devices,
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_kcl_residual_a": max(abs(v) for v in residual),
        "conductance_matrix_s": tuple(tuple(row) for row in conductance),
        "iterations": iteration, "network_parameters": params,
        "forward_biased_base_collector_devices": tuple(
            name for name, device in devices.items() if device["v_bc_v"] > 0),
        "external_wiper_and_loudness_voltages_imposed": True,
        "second_vca_base_currents_imposed_zero": True,
        "device_parameters_imposed": True,
    }


if __name__ == "__main__":
    result = conditional_vca1_dc(
        wiper_v=5, loudness_v=2, balance_left_ohm=12.5,
        is_a={name: 1e-14 for name in DEVICES},
        beta_forward={name: 100 for name in DEVICES},
        beta_reverse={name: 5 for name in DEVICES},
        temperature_k=298.15)
    print(json.dumps({key: result[key] for key in (
        "nodes_v", "devices", "max_kcl_residual_a", "iterations",
        "forward_biased_base_collector_devices")}, indent=2))
