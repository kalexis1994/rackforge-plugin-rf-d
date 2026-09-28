"""Conditional Q14/Q13/Q21 second multiplier at four voltage boundaries.

Q14/Q13 base currents are observable loads for eventual coupling to Q16/Q15.
R51 loads the imposed Q21-base source. No conversion/output stage is included.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _device, _solve_linear
from semiconductor_ideal import thermal_voltage_v


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "vca2_active_core.json"
DEVICES = ("Q14", "Q13", "Q21")
NODES = ("PAIR2_EMITTER", "Q21_COLLECTOR", "Q21_EMITTER",
         "Q14_COLLECTOR", "Q13_COLLECTOR")
EXPECTED = {"R11": 150, "R12": 100, "R18": 330, "R21": 330, "R33": 470,
            "R42": 3300, "R44": 150000, "R51": 33000}


def _parts() -> dict[str, float]:
    source = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parts = {row["ref"]: row["ohm"] for row in source["resistors"]}
    if (source["schematic"]["figure"], source["parts_list"]["table"],
            tuple(source["devices"]), parts) != ("9-11", "7-8", DEVICES, EXPECTED):
        raise ValueError("second-VCA core differs from documentary graph")
    return parts


def _evaluate(x: list[float], *, r: dict[str, float],
              q14_base_v: float, q13_base_v: float, q21_base_v: float,
              wiper_v: float, minus_v: float, left_ohm: float, vt: float,
              is_a: dict[str, float], beta_forward: dict[str, float],
              beta_reverse: dict[str, float]) -> tuple[list[float], dict]:
    q14 = _device(q14_base_v, x[3], x[0], is_a["Q14"],
                  beta_forward["Q14"], beta_reverse["Q14"], vt)
    q13 = _device(q13_base_v, x[4], x[0], is_a["Q13"],
                  beta_forward["Q13"], beta_reverse["Q13"], vt)
    q21 = _device(q21_base_v, x[1], x[2], is_a["Q21"],
                  beta_forward["Q21"], beta_reverse["Q21"], vt)
    residual = [
        q14["emitter_a"] + q13["emitter_a"] - (x[0] - x[1]) / r["R33"],
        (x[0] - x[1]) / r["R33"] - q21["collector_a"],
        q21["emitter_a"] - x[2] / r["R42"]
        - (x[2] - minus_v) / r["R44"],
        (wiper_v - x[3]) / (r["R18"] + left_ohm) - q14["collector_a"],
        (wiper_v - x[4]) / (r["R21"] + r["R12"] - left_ohm)
        - q13["collector_a"],
    ]
    return residual, {"Q14": q14, "Q13": q13, "Q21": q21}


def conditional_vca2_dc(*, q14_base_v: float, q13_base_v: float,
                        q21_base_v: float, wiper_v: float,
                        balance_left_ohm: float,
                        is_a: dict[str, float], beta_forward: dict[str, float],
                        beta_reverse: dict[str, float], temperature_k: float,
                        minus_v: float = -10.0) -> dict:
    """Solve the second multiplier, reporting imposed-source base currents."""
    if not all(math.isfinite(v) for v in (q14_base_v, q13_base_v,
                                         q21_base_v, wiper_v,
                                         balance_left_ohm, minus_v)):
        raise ValueError("finite second-VCA boundaries required")
    r = _parts()
    if not 0 <= balance_left_ohm <= r["R12"]:
        raise ValueError("second balance segment outside 0..100 ohm")
    if set(is_a) != set(DEVICES) or set(beta_forward) != set(DEVICES) or set(beta_reverse) != set(DEVICES):
        raise ValueError("provide Is and both betas for Q14/Q13/Q21")
    if not all(math.isfinite(v) and v > 0 for v in is_a.values()):
        raise ValueError("positive finite Is required")
    if not all(math.isfinite(v) and v > 1 for v in beta_forward.values()):
        raise ValueError("finite forward beta > 1 required")
    if not all(math.isfinite(v) and v > 0 for v in beta_reverse.values()):
        raise ValueError("positive finite reverse beta required")
    params = dict(r=r, q14_base_v=q14_base_v, q13_base_v=q13_base_v,
                  q21_base_v=q21_base_v, wiper_v=wiper_v,
                  minus_v=minus_v, left_ohm=balance_left_ohm,
                  vt=thermal_voltage_v(temperature_k),
                  is_a=is_a, beta_forward=beta_forward,
                  beta_reverse=beta_reverse)
    b = (q14_base_v + q13_base_v) / 2
    x = [b - 0.6, b - 0.8, q21_base_v - 0.6,
         wiper_v - 0.05, wiper_v - 0.05]
    scales = [1e-3] * 5
    for iteration in range(100):
        residual, devices = _evaluate(x, **params)
        error = max(abs(v / s) for v, s in zip(residual, scales))
        if max(abs(v) for v in residual) < 1e-12 and error < 1e-7:
            break
        jacobian = [[0.0] * 5 for _ in range(5)]
        for col in range(5):
            trial = x.copy()
            trial[col] += 1e-6
            high, _ = _evaluate(trial, **params)
            for row in range(5):
                jacobian[row][col] = (high[row] - residual[row]) / 1e-6 / scales[row]
        direction = _solve_linear(jacobian,
                                  [-v / s for v, s in zip(residual, scales)])
        for power in range(30):
            candidate = [v + 0.5 ** power * dv for v, dv in zip(x, direction)]
            try:
                candidate_residual, _ = _evaluate(candidate, **params)
            except ValueError:
                continue
            if max(abs(v / s) for v, s in zip(candidate_residual, scales)) < error:
                x = candidate
                break
        else:
            raise ValueError("second-VCA Newton step did not decrease residual")
    else:
        raise ValueError("second-VCA Newton iteration did not converge")
    residual, devices = _evaluate(x, **params)
    return {
        "nodes_v": dict(zip(NODES, x)), "devices": devices,
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_kcl_residual_a": max(abs(v) for v in residual),
        "first_vca_collector_load_currents_a": (
            devices["Q14"]["base_a"], devices["Q13"]["base_a"]),
        "external_q21_base_source_current_a": (
            devices["Q21"]["base_a"] + q21_base_v / r["R51"]),
        "iterations": iteration,
        "network_parameters": params,
        "forward_biased_base_collector_devices": tuple(
            name for name, device in devices.items() if device["v_bc_v"] > 0),
        "all_base_and_balance_voltages_imposed": True,
        "output_conversion_base_currents_imposed_zero": True,
    }


if __name__ == "__main__":
    import json

    from vca1_active_core_dc_reference import DEVICES as FIRST_DEVICES
    from vca1_balance_supply_dc_reference import conditional_vca1_supplied_dc

    first = conditional_vca1_supplied_dc(
        second_wiper_v=9, loudness_v=2, balance_left_ohm=12.5,
        is_a={n: 1e-14 for n in FIRST_DEVICES},
        beta_forward={n: 100 for n in FIRST_DEVICES},
        beta_reverse={n: 5 for n in FIRST_DEVICES}, temperature_k=298.15)
    out = conditional_vca2_dc(
        q14_base_v=first["nodes_v"]["Q16_COLLECTOR"],
        q13_base_v=first["nodes_v"]["Q15_COLLECTOR"],
        q21_base_v=2, wiper_v=9, balance_left_ohm=50,
        is_a={n: 1e-14 for n in DEVICES},
        beta_forward={n: 100 for n in DEVICES},
        beta_reverse={n: 5 for n in DEVICES}, temperature_k=298.15)
    print(json.dumps({"nodes_v": out["nodes_v"],
                      "first_vca_collector_load_currents_a": out[
                          "first_vca_collector_load_currents_a"],
                      "max_kcl_residual_a": out["max_kcl_residual_a"]}, indent=2))
