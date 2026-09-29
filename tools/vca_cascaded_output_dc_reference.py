"""Conditional 22-node DC from two VCA cores through PNP output conversion.

The output remains the pre-C2 Q17 collector. Q18/Q21 control voltages,
filter/VCA input, transistor parameters and rails are imposed boundaries.
"""

from __future__ import annotations

import json
import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from vca_cascaded_dc_reference import (
    DEVICE_NAMES as VCA_DEVICES, NODES as VCA_NODES,
    _evaluate as vca_kcl, conditional_cascaded_vca_dc,
)
from vca_output_conversion_dc_reference import (
    DEVICES as OUTPUT_DEVICES, NODES as OUTPUT_NODES,
    _evaluate as output_kcl, _parts as output_parts,
    conditional_output_conversion_dc,
)
from semiconductor_ideal import thermal_voltage_v


NODES = VCA_NODES + ("Q1_BASE",) + OUTPUT_NODES
DEVICE_NAMES = VCA_DEVICES + OUTPUT_DEVICES


def _evaluate(x: list[float], *, first_parameters: dict,
              second_parameters: dict, output_parameters: dict,
              plus_v: float) -> tuple[list[float], dict]:
    vca, first_six = vca_kcl(
        x[:15], upper_supply_v=x[15], first_parameters=first_parameters,
        second_parameters=second_parameters)
    output, last_three = output_kcl(
        x[16:], q1_base_v=x[15], q12_base_v=x[12],
        q17_base_v=x[13], plus_v=plus_v, **output_parameters)
    # PNP base current leaves Q12/Q17 and enters the NPN collector nodes.
    vca[12] += last_three["Q12"]["base_a"]
    vca[13] += last_three["Q17"]["base_a"]
    r = output_parameters["r"]
    q1_base_kcl = ((plus_v - x[15]) / r["R10"]
                   + last_three["Q1"]["base_a"]
                   - (x[15] - x[14]) / r["R11"])
    return vca + [q1_base_kcl] + output, first_six | last_three


def conditional_cascaded_output_dc(*, first_loudness_v: float,
                                   second_loudness_base_v: float,
                                   first_balance_left_ohm: float,
                                   second_balance_left_ohm: float,
                                   is_a: dict[str, float],
                                   beta_forward: dict[str, float],
                                   beta_reverse: dict[str, float],
                                   temperature_k: float,
                                   plus_v: float = 10.0,
                                   minus_v: float = -10.0) -> dict:
    """Solve both VCA wipers, R10/R11 and Q1/Q12/Q17 together."""
    if not all(math.isfinite(v) for v in (first_loudness_v,
                                         second_loudness_base_v,
                                         first_balance_left_ohm,
                                         second_balance_left_ohm,
                                         plus_v, minus_v)):
        raise ValueError("finite VCA/output boundaries required")
    if any(set(values) != set(DEVICE_NAMES) for values in
           (is_a, beta_forward, beta_reverse)):
        raise ValueError("provide parameters for all nine transistors")
    vca = conditional_cascaded_vca_dc(
        upper_supply_v=plus_v-1, first_loudness_v=first_loudness_v,
        second_loudness_base_v=second_loudness_base_v,
        first_balance_left_ohm=first_balance_left_ohm,
        second_balance_left_ohm=second_balance_left_ohm,
        is_a={n: is_a[n] for n in VCA_DEVICES},
        beta_forward={n: beta_forward[n] for n in VCA_DEVICES},
        beta_reverse={n: beta_reverse[n] for n in VCA_DEVICES},
        temperature_k=temperature_k, minus_v=minus_v)
    v = vca["nodes_v"]
    output = conditional_output_conversion_dc(
        q1_base_v=plus_v-1, q12_base_v=v["Q14_COLLECTOR"],
        q17_base_v=v["Q13_COLLECTOR"],
        is_a={n: is_a[n] for n in OUTPUT_DEVICES},
        beta_forward={n: beta_forward[n] for n in OUTPUT_DEVICES},
        beta_reverse={n: beta_reverse[n] for n in OUTPUT_DEVICES},
        temperature_k=temperature_k, plus_v=plus_v)
    output_parameters = dict(r=output_parts(),
                             vt=thermal_voltage_v(temperature_k),
                             is_a={n: is_a[n] for n in OUTPUT_DEVICES},
                             beta_forward={n: beta_forward[n]
                                           for n in OUTPUT_DEVICES},
                             beta_reverse={n: beta_reverse[n]
                                           for n in OUTPUT_DEVICES})
    params = dict(first_parameters=vca["network_parameters"]["first_parameters"],
                  second_parameters=vca["network_parameters"]["second_parameters"],
                  output_parameters=output_parameters, plus_v=plus_v)
    x = list(v.values()) + [plus_v-1] + list(output["nodes_v"].values())
    scales = [1e-3] * len(x)
    scales[0] = scales[7] = 1e-5
    for iteration in range(100):
        residual, devices = _evaluate(x, **params)
        error = max(abs(value / scale) for value, scale in zip(residual, scales))
        if max(abs(value) for value in residual) < 1e-12 and error < 1e-7:
            break
        jacobian = [[0.0] * len(x) for _ in x]
        for col in range(len(x)):
            trial = x.copy()
            trial[col] += 1e-6
            high, _ = _evaluate(trial, **params)
            for row in range(len(x)):
                jacobian[row][col] = ((high[row] - residual[row])
                                      / 1e-6 / scales[row])
        direction = _solve_linear(jacobian,
                                  [-value/scale for value, scale
                                   in zip(residual, scales)])
        for power in range(35):
            candidate = [value + 0.5**power * delta for value, delta
                         in zip(x, direction)]
            try:
                next_residual, _ = _evaluate(candidate, **params)
            except ValueError:
                continue
            if max(abs(value/scale) for value, scale
                   in zip(next_residual, scales)) < error:
                x = candidate
                break
        else:
            raise ValueError("cascaded-output Newton step did not decrease residual")
    else:
        raise ValueError("cascaded-output Newton iteration did not converge")
    residual, devices = _evaluate(x, **params)
    if not 0 <= x[21] <= plus_v:
        raise ValueError("diode-open assumption fails at Q17 collector")
    conductance = [[0.0] * len(x) for _ in x]
    for col in range(len(x)):
        high_x, low_x = x.copy(), x.copy()
        high_x[col] += 1e-6
        low_x[col] -= 1e-6
        high, _ = _evaluate(high_x, **params)
        low, _ = _evaluate(low_x, **params)
        for row in range(len(x)):
            conductance[row][col] = (high[row] - low[row]) / 2e-6
    return {
        "nodes_v": dict(zip(NODES, x)), "devices": devices,
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_kcl_residual_a": max(abs(value) for value in residual),
        "conductance_matrix_s": tuple(tuple(row) for row in conductance),
        "q17_collector_output_v": x[21],
        "interstage_base_currents_a": {
            "Q14": devices["Q14"]["base_a"],
            "Q13": devices["Q13"]["base_a"],
            "Q12": devices["Q12"]["base_a"],
            "Q17": devices["Q17"]["base_a"]},
        "iterations": iteration, "network_parameters": params,
        "diodes_assumed_open": True, "output_coupling_open_at_dc": True,
        "input_and_controls_imposed": True,
    }


if __name__ == "__main__":
    out = conditional_cascaded_output_dc(
        first_loudness_v=2, second_loudness_base_v=2,
        first_balance_left_ohm=12.5, second_balance_left_ohm=50,
        is_a={n: 1e-14 for n in DEVICE_NAMES},
        beta_forward={n: 100 for n in DEVICE_NAMES},
        beta_reverse={n: 5 for n in DEVICE_NAMES},
        temperature_k=298.15)
    print(json.dumps({"nodes_v": out["nodes_v"],
                      "max_kcl_residual_a": out["max_kcl_residual_a"]},
                     indent=2))
