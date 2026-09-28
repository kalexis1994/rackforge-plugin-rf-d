"""Nine-node first-VCA DC with its balance wiper supplied through R13.

SECOND_BAL_WIPER, at the far end of R13, remains an imposed boundary until
Q14/Q13/Q21 and the shared positive supply path are solved together.
"""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from vca1_active_core_dc_reference import (
    NODES as CORE_NODES, _evaluate as core_kcl, _parts,
    conditional_vca1_dc,
)


NODES = CORE_NODES + ("FIRST_BAL_WIPER",)


def _evaluate(x: list[float], *, second_wiper_v: float,
              core_parameters: dict) -> tuple[list[float], dict]:
    local, devices = core_kcl(x[:8], **(core_parameters | {"wiper_v": x[8]}))
    r = core_parameters["r"]
    w = x[8]
    # Incoming from the second balance wiper, outgoing through bias and
    # both collector load legs. The R14 endpoints were eliminated exactly.
    local.append(
        (second_wiper_v - w) / r["R13"]
        - (w - x[1]) / r["R22"]
        - (w - x[5]) / (r["R19"] + core_parameters["left_ohm"])
        - (w - x[6]) / (r["R23"] + r["R14_BOARD4"]
                        - core_parameters["left_ohm"]))
    return local, devices


def conditional_vca1_supplied_dc(*, second_wiper_v: float,
                                 loudness_v: float, balance_left_ohm: float,
                                 is_a: dict[str, float],
                                 beta_forward: dict[str, float],
                                 beta_reverse: dict[str, float],
                                 temperature_k: float,
                                 minus_v: float = -10.0) -> dict:
    """Solve first balance cursor rather than forcing its voltage."""
    if not math.isfinite(second_wiper_v):
        raise ValueError("finite second-balance-wiper boundary required")
    r = _parts()
    # Preconditioner and parameter validation from the same eight-node law.
    estimate = second_wiper_v * (r["R22"] + r["R36"]) / (
        r["R13"] + r["R22"] + r["R36"])
    core = conditional_vca1_dc(
        wiper_v=estimate, loudness_v=loudness_v,
        balance_left_ohm=balance_left_ohm, is_a=is_a,
        beta_forward=beta_forward, beta_reverse=beta_reverse,
        temperature_k=temperature_k, minus_v=minus_v)
    parameters = dict(second_wiper_v=second_wiper_v,
                      core_parameters=core["network_parameters"])
    x = list(core["nodes_v"].values()) + [estimate]
    scales = [1e-5, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-5, 1e-3]
    for iteration in range(80):
        residual, devices = _evaluate(x, **parameters)
        error = max(abs(v / s) for v, s in zip(residual, scales))
        if max(abs(v) for v in residual) < 1e-12 and error < 1e-7:
            break
        jacobian = [[0.0] * 9 for _ in range(9)]
        for col in range(9):
            trial = x.copy()
            trial[col] += 1e-6
            high, _ = _evaluate(trial, **parameters)
            for row in range(9):
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
            raise ValueError("supplied first-VCA Newton step did not decrease residual")
    else:
        raise ValueError("supplied first-VCA DC Newton step did not converge")
    residual, devices = _evaluate(x, **parameters)
    conductance = [[0.0] * 9 for _ in range(9)]
    for col in range(9):
        high_x, low_x = x.copy(), x.copy()
        high_x[col] += 1e-6
        low_x[col] -= 1e-6
        high, _ = _evaluate(high_x, **parameters)
        low, _ = _evaluate(low_x, **parameters)
        for row in range(9):
            conductance[row][col] = (high[row] - low[row]) / 2e-6
    return {
        "nodes_v": dict(zip(NODES, x)), "devices": devices,
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_kcl_residual_a": max(abs(v) for v in residual),
        "conductance_matrix_s": tuple(tuple(row) for row in conductance),
        "iterations": iteration, "network_parameters": parameters,
        "forward_biased_base_collector_devices": tuple(
            name for name, device in devices.items() if device["v_bc_v"] > 0),
        "second_wiper_voltage_imposed": True,
        "second_vca_base_currents_imposed_zero": True,
    }


if __name__ == "__main__":
    import json
    from vca1_active_core_dc_reference import DEVICES

    out = conditional_vca1_supplied_dc(
        second_wiper_v=9, loudness_v=2, balance_left_ohm=12.5,
        is_a={n: 1e-14 for n in DEVICES},
        beta_forward={n: 100 for n in DEVICES},
        beta_reverse={n: 5 for n in DEVICES}, temperature_k=298.15)
    print(json.dumps({"nodes_v": out["nodes_v"],
                      "max_kcl_residual_a": out["max_kcl_residual_a"]}, indent=2))
