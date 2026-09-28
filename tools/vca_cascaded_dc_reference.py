"""Coupled 15-node DC for both VCA multipliers and their balance supply.

Q14/Q13 base currents load Q16/Q15 collectors. R13 and R11 supply both
balance wipers. The far end of R11, Q18/Q21 controls and output loads remain
imposed boundaries. This is a conditional offline circuit reference.
"""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from vca1_active_core_dc_reference import DEVICES as FIRST_DEVICES
from vca1_balance_supply_dc_reference import (
    NODES as FIRST_NODES, _evaluate as first_kcl,
    conditional_vca1_supplied_dc,
)
from vca2_active_core_dc_reference import (
    DEVICES as SECOND_DEVICES, NODES as SECOND_NODES,
    _evaluate as second_kcl, conditional_vca2_dc,
)


NODES = FIRST_NODES + SECOND_NODES + ("SECOND_BAL_WIPER",)
DEVICE_NAMES = FIRST_DEVICES + SECOND_DEVICES


def _evaluate(x: list[float], *, upper_supply_v: float,
              first_parameters: dict, second_parameters: dict) -> tuple[list[float], dict]:
    first, first_devices = first_kcl(
        x[:9], **(first_parameters | {"second_wiper_v": x[14]}))
    second_core = second_parameters
    second, second_devices = second_kcl(
        x[9:14], **(second_core | {
            "q14_base_v": x[5], "q13_base_v": x[6], "wiper_v": x[14]}))
    # Two base currents close the interstage load missing from the isolated
    # first-VCA model. first[5/6] are its collector KCL rows.
    first[5] -= second_devices["Q14"]["base_a"]
    first[6] -= second_devices["Q13"]["base_a"]
    r1 = first_parameters["core_parameters"]["r"]
    r2 = second_core["r"]
    w2 = x[14]
    second_wiper_kcl = (
        (upper_supply_v - w2) / r2["R11"]
        - (w2 - x[8]) / r1["R13"]
        - (w2 - x[12]) / (r2["R18"] + second_core["left_ohm"])
        - (w2 - x[13]) / (r2["R21"] + r2["R12"]
                           - second_core["left_ohm"]))
    return first + second + [second_wiper_kcl], first_devices | second_devices


def conditional_cascaded_vca_dc(*, upper_supply_v: float,
                                first_loudness_v: float,
                                second_loudness_base_v: float,
                                first_balance_left_ohm: float,
                                second_balance_left_ohm: float,
                                is_a: dict[str, float],
                                beta_forward: dict[str, float],
                                beta_reverse: dict[str, float],
                                temperature_k: float,
                                minus_v: float = -10.0) -> dict:
    """Resolve six TIS97 devices and both balance cursors simultaneously."""
    if not math.isfinite(upper_supply_v):
        raise ValueError("finite upper-supply boundary required")
    if set(is_a) != set(DEVICE_NAMES) or set(beta_forward) != set(DEVICE_NAMES) or set(beta_reverse) != set(DEVICE_NAMES):
        raise ValueError("provide parameters for all six VCA transistors")
    first = conditional_vca1_supplied_dc(
        second_wiper_v=upper_supply_v - 0.1,
        loudness_v=first_loudness_v,
        balance_left_ohm=first_balance_left_ohm,
        is_a={n: is_a[n] for n in FIRST_DEVICES},
        beta_forward={n: beta_forward[n] for n in FIRST_DEVICES},
        beta_reverse={n: beta_reverse[n] for n in FIRST_DEVICES},
        temperature_k=temperature_k, minus_v=minus_v)
    second = conditional_vca2_dc(
        q14_base_v=first["nodes_v"]["Q16_COLLECTOR"],
        q13_base_v=first["nodes_v"]["Q15_COLLECTOR"],
        q21_base_v=second_loudness_base_v,
        wiper_v=upper_supply_v - 0.1,
        balance_left_ohm=second_balance_left_ohm,
        is_a={n: is_a[n] for n in SECOND_DEVICES},
        beta_forward={n: beta_forward[n] for n in SECOND_DEVICES},
        beta_reverse={n: beta_reverse[n] for n in SECOND_DEVICES},
        temperature_k=temperature_k, minus_v=minus_v)
    parameters = dict(upper_supply_v=upper_supply_v,
                      first_parameters=first["network_parameters"],
                      second_parameters=second["network_parameters"])
    x = (list(first["nodes_v"].values())
         + list(second["nodes_v"].values()) + [upper_supply_v - 0.1])
    scales = [1e-5, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-5, 1e-3]
    scales += [1e-3] * 6
    for iteration in range(100):
        residual, devices = _evaluate(x, **parameters)
        error = max(abs(v / s) for v, s in zip(residual, scales))
        if max(abs(v) for v in residual) < 1e-12 and error < 1e-7:
            break
        jacobian = [[0.0] * 15 for _ in range(15)]
        for col in range(15):
            trial = x.copy()
            trial[col] += 1e-6
            high, _ = _evaluate(trial, **parameters)
            for row in range(15):
                jacobian[row][col] = (high[row] - residual[row]) / 1e-6 / scales[row]
        direction = _solve_linear(jacobian,
                                  [-v / s for v, s in zip(residual, scales)])
        for power in range(30):
            candidate = [v + 0.5 ** power * dv for v, dv in zip(x, direction)]
            try:
                candidate_residual, _ = _evaluate(candidate, **parameters)
            except ValueError:
                continue
            if max(abs(v / s) for v, s in zip(candidate_residual, scales)) < error:
                x = candidate
                break
        else:
            raise ValueError("coupled VCA Newton step did not decrease residual")
    else:
        raise ValueError("coupled VCA Newton iteration did not converge")
    residual, devices = _evaluate(x, **parameters)
    return {
        "nodes_v": dict(zip(NODES, x)), "devices": devices,
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_kcl_residual_a": max(abs(v) for v in residual),
        "first_to_second_base_currents_a": (
            devices["Q14"]["base_a"], devices["Q13"]["base_a"]),
        "iterations": iteration, "network_parameters": parameters,
        "forward_biased_base_collector_devices": tuple(
            n for n, device in devices.items() if device["v_bc_v"] > 0),
        "upper_supply_and_controls_imposed": True,
        "output_conversion_base_currents_imposed_zero": True,
    }


if __name__ == "__main__":
    import json

    out = conditional_cascaded_vca_dc(
        upper_supply_v=9.5, first_loudness_v=2,
        second_loudness_base_v=2, first_balance_left_ohm=12.5,
        second_balance_left_ohm=50,
        is_a={n: 1e-14 for n in DEVICE_NAMES},
        beta_forward={n: 100 for n in DEVICE_NAMES},
        beta_reverse={n: 5 for n in DEVICE_NAMES}, temperature_k=298.15)
    print(json.dumps({"nodes_v": out["nodes_v"],
                      "first_to_second_base_currents_a": out[
                          "first_to_second_base_currents_a"],
                      "max_kcl_residual_a": out["max_kcl_residual_a"]}, indent=2))
