"""Conditional eight-node Q5-Q8 recovery DC from SVC-9 Fig. 9-11.

Both BJT junctions are included; C1/C5/C9/C10 are open at DC. This model
does not infer transistor parameters or resolve the vintage board population.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _device, _solve_linear
from semiconductor_ideal import thermal_voltage_v


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "filter_recovery_active_dc.json"
NODES = ("Q8_BASE", "Q6_BASE", "Q8_EMITTER_Q7_BASE",
         "Q6_EMITTER_Q5_BASE", "RECOVER_TAIL", "RECOVER_COLLECTOR",
         "RECOVER_R7_R3", "RECOVER_R6_R7")
DEVICES = ("Q8", "Q6", "Q7", "Q5")


def _resistors() -> dict[str, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parts = {part["ref"]: part["ohm"] for part in data["resistors"]}
    if (data["schematic"]["figure"], data["parts_list"]["table"], parts,
            tuple(data["dc_open_capacitors"])) != (
                "9-11", "7-8",
                {"R31": 47000, "R38": 47000, "R24": 220000,
                 "R20": 100000, "R26": 1000, "R3": 1000,
                 "R7": 180, "R6": 47}, ("C1", "C5", "C9", "C10")):
        raise ValueError("recovery DC values differ from documentary source")
    return parts


def _evaluate(x: list[float], *, resistance: dict[str, float], plus: float,
              minus: float, vt: float, is_a: dict[str, float],
              beta_forward: dict[str, float], beta_reverse: dict[str, float]) -> tuple[list[float], dict]:
    q8 = _device(x[0], x[5], x[2], is_a["Q8"], beta_forward["Q8"], beta_reverse["Q8"], vt)
    q6 = _device(x[1], plus, x[3], is_a["Q6"], beta_forward["Q6"], beta_reverse["Q6"], vt)
    q7 = _device(x[2], x[5], x[4], is_a["Q7"], beta_forward["Q7"], beta_reverse["Q7"], vt)
    q5 = _device(x[3], plus, x[4], is_a["Q5"], beta_forward["Q5"], beta_reverse["Q5"], vt)
    r = resistance
    residual = [
        -x[0] / r["R31"] - q8["base_a"],
        -x[1] / r["R38"] - q6["base_a"],
        q8["emitter_a"] - (x[2] - minus) / r["R24"] - q7["base_a"],
        q6["emitter_a"] - (x[3] - minus) / r["R20"] - q5["base_a"],
        q7["emitter_a"] + q5["emitter_a"] - (x[4] - minus) / r["R26"],
        (x[6] - x[5]) / r["R3"] - q8["collector_a"] - q7["collector_a"],
        (x[7] - x[6]) / r["R7"] - (x[6] - x[5]) / r["R3"],
        (plus - x[7]) / r["R6"] - (x[7] - x[6]) / r["R7"],
    ]
    return residual, {"Q8": q8, "Q6": q6, "Q7": q7, "Q5": q5}


def conditional_recovery_dc(*, is_a: dict[str, float],
                            beta_forward: dict[str, float],
                            beta_reverse: dict[str, float],
                            temperature_k: float,
                            plus_v: float = 10.0,
                            minus_v: float = -10.0) -> dict:
    """Solve Q5-Q8 DC, including base-shunt loading and possible saturation."""
    if set(is_a) != set(DEVICES) or set(beta_forward) != set(DEVICES) or set(beta_reverse) != set(DEVICES):
        raise ValueError("provide Is and both gains for Q5/Q6/Q7/Q8")
    if not all(math.isfinite(value) and value > 0 for value in is_a.values()):
        raise ValueError("positive finite Is required")
    if not all((not math.isnan(value)) and value > 1 for value in beta_forward.values()):
        raise ValueError("forward beta must exceed one")
    if not all(math.isfinite(value) and value > 0 for value in beta_reverse.values()):
        raise ValueError("positive finite reverse beta required")
    if not all(math.isfinite(value) for value in (plus_v, minus_v)) or plus_v <= minus_v:
        raise ValueError("ordered finite supply rails required")
    resistance = _resistors()
    vt = thermal_voltage_v(temperature_k)
    parameters = dict(resistance=resistance, plus=plus_v, minus=minus_v,
                      vt=vt, is_a=is_a, beta_forward=beta_forward,
                      beta_reverse=beta_reverse)
    x = [0.0, 0.0, -0.6, -0.6, -1.3, 0.0, 8.0, 9.5]
    scales = [1e-6, 1e-6, 1e-4, 1e-4, 1e-4, 1e-4, 1e-4, 1e-4]
    iterations = 0
    for iteration in range(100):
        residual, devices = _evaluate(x, **parameters)
        error = max(abs(value / scale) for value, scale in zip(residual, scales))
        if max(abs(value) for value in residual) < 1e-10 and error < 1e-4:
            iterations = iteration
            break
        jacobian = [[0.0] * 8 for _ in range(8)]
        for column in range(8):
            shifted = x.copy()
            shifted[column] += 1e-5
            high, _ = _evaluate(shifted, **parameters)
            for row in range(8):
                jacobian[row][column] = (high[row] - residual[row]) / 1e-5 / scales[row]
        direction = _solve_linear(jacobian,
                                  [-value / scale for value, scale in zip(residual, scales)])
        accepted = False
        for power in range(28):
            step = 0.5 ** power
            trial = [value + step * change for value, change in zip(x, direction)]
            try:
                trial_residual, _ = _evaluate(trial, **parameters)
            except ValueError:
                continue
            if max(abs(value / scale) for value, scale in zip(trial_residual, scales)) < error:
                x = trial
                accepted = True
                break
        if not accepted:
            raise ValueError("recovery DC Newton iteration did not decrease KCL residual")
    else:
        raise ValueError("recovery DC Newton iteration did not converge")
    residual, devices = _evaluate(x, **parameters)
    conductance = [[0.0] * 8 for _ in range(8)]
    for column in range(8):
        high_x, low_x = x.copy(), x.copy()
        high_x[column] += 1e-6
        low_x[column] -= 1e-6
        high, _ = _evaluate(high_x, **parameters)
        low, _ = _evaluate(low_x, **parameters)
        for row in range(8):
            conductance[row][column] = (high[row] - low[row]) / 2e-6
    return {
        "nodes_v": dict(zip(NODES, x)),
        "devices": devices,
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_kcl_residual_a": max(abs(value) for value in residual),
        "conductance_matrix_s": tuple(tuple(row) for row in conductance),
        "iterations": iterations,
        "forward_biased_base_collector_devices": tuple(
            name for name, device in devices.items() if device["v_bc_v"] > 0),
        "network_parameters": parameters,
        "device_parameters_imposed": True,
    }


if __name__ == "__main__":
    result = conditional_recovery_dc(
        is_a={name: 1e-14 for name in DEVICES},
        beta_forward={name: 100 for name in DEVICES},
        beta_reverse={name: 5 for name in DEVICES},
        temperature_k=298.15)
    print(json.dumps({"nodes_v": result["nodes_v"],
                      "forward_biased_base_collector_devices": result[
                          "forward_biased_base_collector_devices"],
                      "max_kcl_residual_a": result["max_kcl_residual_a"],
                      "iterations": result["iterations"]}, indent=2))
