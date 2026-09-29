"""Conditional, diode-open DC reference for board-4 PNP output conversion.

The three base voltages are imposed. Currents are positive into PNP emitters
and out of their collectors/bases. This is an offline topology oracle, not a
2N4058 characterization or a predicted Model D output level.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _device, _solve_linear
from semiconductor_ideal import thermal_voltage_v
from output_diode_reference import diode_current_a


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "vca_output_conversion.json"
DEVICES = ("Q1", "Q12", "Q17")
NODES = ("Q1_EMITTER", "Q1_COLLECTOR", "Q12_EMITTER", "Q17_EMITTER",
         "Q12_COLLECTOR", "Q17_COLLECTOR")
EXPECTED = {"R8": 8.2, "R28": 8.2, "R9": 62, "R10": 120,
            "R11": 150, "R30": 680, "R29": 680, "R75": 1000,
            "R77": 1000}


def _parts() -> dict[str, float]:
    source = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    r = {row["ref"]: row["ohm"] for row in source["resistors"]}
    if (source["source"]["schematic"], r,
            {n: source["devices"][n] for n in DEVICES}) != (
            "Fig. 9-11, PDF p. 13", EXPECTED,
            {n: "PNP 2N4058" for n in DEVICES}):
        raise ValueError("output conversion differs from documentary graph")
    return r


def _pnp(vb: float, vc: float, ve: float, is_a: float,
         beta_f: float, beta_r: float, vt: float) -> dict:
    """Polarity transform of two-junction Ebers-Moll; currents are magnitudes.

    Signed currents can be negative if the transistor is biased in reverse.
    """
    q = _device(-vb, -vc, -ve, is_a, beta_f, beta_r, vt)
    return {**q, "v_eb_v": ve - vb, "v_cb_v": vc - vb}


def _evaluate(x: list[float], *, q1_base_v: float, q12_base_v: float,
              q17_base_v: float, plus_v: float, r: dict[str, float],
              vt: float, is_a: dict[str, float],
              beta_forward: dict[str, float],
              beta_reverse: dict[str, float],
              diode_model: dict[str, float] | None = None) -> tuple[list[float], dict]:
    q1 = _pnp(q1_base_v, x[1], x[0], is_a["Q1"],
              beta_forward["Q1"], beta_reverse["Q1"], vt)
    q12 = _pnp(q12_base_v, x[4], x[2], is_a["Q12"],
               beta_forward["Q12"], beta_reverse["Q12"], vt)
    q17 = _pnp(q17_base_v, x[5], x[3], is_a["Q17"],
               beta_forward["Q17"], beta_reverse["Q17"], vt)
    cr1 = cr2 = 0.0
    if diode_model is not None:
        cr1 = diode_current_a(x[5]-plus_v, model=diode_model, vt=vt)
        cr2 = diode_current_a(-x[5], model=diode_model, vt=vt)
    residual = [
        (plus_v - x[0]) / r["R9"] - q1["emitter_a"],
        q1["collector_a"] - (x[1] - x[2]) / r["R8"]
        - (x[1] - x[3]) / r["R28"],
        (x[1] - x[2]) / r["R8"] - q12["emitter_a"],
        (x[1] - x[3]) / r["R28"] - q17["emitter_a"],
        q12["collector_a"] - x[4] / r["R30"],
        q17["collector_a"] - x[5] / r["R29"] - cr1 + cr2,
    ]
    return residual, {"Q1": q1, "Q12": q12, "Q17": q17}


def conditional_output_conversion_dc(*, q1_base_v: float,
                                     q12_base_v: float, q17_base_v: float,
                                     is_a: dict[str, float],
                                     beta_forward: dict[str, float],
                                     beta_reverse: dict[str, float],
                                     temperature_k: float,
                                     plus_v: float = 10.0,
                                     diode_model: dict[str, float] | None = None) -> dict:
    """Six DC nodes; CR1/CR2 open or parameterized with Shockley law."""
    if not all(math.isfinite(v) for v in (q1_base_v, q12_base_v,
                                         q17_base_v, plus_v)):
        raise ValueError("finite output-conversion boundaries required")
    if any(set(values) != set(DEVICES) for values in
           (is_a, beta_forward, beta_reverse)):
        raise ValueError("provide parameters for Q1/Q12/Q17")
    if not all(math.isfinite(v) and v > 0 for v in is_a.values()):
        raise ValueError("positive finite Is required")
    if not all(math.isfinite(v) and v > 1 for v in beta_forward.values()):
        raise ValueError("finite forward beta > 1 required")
    if not all(math.isfinite(v) and v > 0 for v in beta_reverse.values()):
        raise ValueError("positive finite reverse beta required")
    r = _parts()
    if diode_model is not None and (diode_model["temperature_k"] != temperature_k
                                    or not math.isfinite(diode_model["is_a"])
                                    or diode_model["is_a"] <= 0):
        raise ValueError("diode model temperature and Is must match DC scenario")
    params = dict(q1_base_v=q1_base_v, q12_base_v=q12_base_v,
                  q17_base_v=q17_base_v, plus_v=plus_v, r=r,
                  vt=thermal_voltage_v(temperature_k), is_a=is_a,
                  beta_forward=beta_forward, beta_reverse=beta_reverse,
                  diode_model=diode_model)
    x = [q1_base_v + 0.6, q1_base_v + 0.35,
         q12_base_v + 0.6, q17_base_v + 0.6, 2.0, 2.0]
    scales = [1e-3] * 6
    for iteration in range(100):
        residual, devices = _evaluate(x, **params)
        error = max(abs(v / s) for v, s in zip(residual, scales))
        if max(abs(v) for v in residual) < 1e-12 and error < 1e-7:
            break
        jacobian = [[0.0] * 6 for _ in range(6)]
        for col in range(6):
            trial = x.copy()
            trial[col] += 1e-6
            high, _ = _evaluate(trial, **params)
            for row in range(6):
                jacobian[row][col] = (high[row] - residual[row]) / 1e-6 / scales[row]
        direction = _solve_linear(jacobian,
                                  [-v / s for v, s in zip(residual, scales)])
        for power in range(35):
            candidate = [v + 0.5 ** power * dv for v, dv in zip(x, direction)]
            try:
                next_residual, _ = _evaluate(candidate, **params)
            except ValueError:
                continue
            if max(abs(v / s) for v, s in zip(next_residual, scales)) < error:
                x = candidate
                break
        else:
            raise ValueError("output-conversion Newton step did not decrease residual")
    else:
        raise ValueError("output-conversion Newton iteration did not converge")
    residual, devices = _evaluate(x, **params)
    if diode_model is None and not 0 <= x[5] <= plus_v:
        raise ValueError("diode-open assumption fails at Q17 collector")
    cr1 = cr2 = 0.0
    if diode_model is not None:
        cr1 = diode_current_a(x[5]-plus_v, model=diode_model,
                              vt=params["vt"])
        cr2 = diode_current_a(-x[5], model=diode_model,
                              vt=params["vt"])
    return {
        "nodes_v": dict(zip(NODES, x)), "devices": devices,
        "kcl_residuals_a": dict(zip(NODES, residual)),
        "max_kcl_residual_a": max(abs(v) for v in residual),
        "base_source_currents_out_a": {n: devices[n]["base_a"] for n in DEVICES},
        "q17_collector_output_v": x[5], "iterations": iteration,
        "network_parameters": params,
        "diodes_assumed_open": diode_model is None,
        "c2_c4_open_at_dc": True,
        "diode_currents_a": {"CR1": cr1, "CR2": cr2},
    }


if __name__ == "__main__":
    example = conditional_output_conversion_dc(
        q1_base_v=8.3, q12_base_v=7.75, q17_base_v=7.75,
        is_a={n: 1e-14 for n in DEVICES},
        beta_forward={n: 100 for n in DEVICES},
        beta_reverse={n: 5 for n in DEVICES}, temperature_k=298.15)
    print(json.dumps({"nodes_v": example["nodes_v"],
                      "base_source_currents_out_a": example[
                          "base_source_currents_out_a"],
                      "max_kcl_residual_a": example["max_kcl_residual_a"]},
                     indent=2))
