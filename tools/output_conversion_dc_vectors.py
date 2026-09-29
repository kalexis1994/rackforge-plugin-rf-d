"""Frozen isolated Q1/Q12/Q17 board-4 DC operating points."""

from __future__ import annotations

import json

from output_diode_reference import diode_model_from_reference
from vca_output_conversion_dc_reference import (
    NODES, conditional_output_conversion_dc)


def generate_vectors() -> dict:
    cases = []
    for name, q1, q12, q17, temperature, diodes in (
            ("nominal_open", 8.3, 7.75, 7.75, 298.15, False),
            ("nominal_diode", 8.3, 7.75, 7.75, 298.15, True),
            ("cool_unbalanced", 8.35, 7.8, 7.65, 285.0, True)):
        model = (diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.7,
            temperature_k=temperature) if diodes else None)
        is_a = dict.fromkeys(("Q1", "Q12", "Q17"), 1e-14)
        bf = dict.fromkeys(("Q1", "Q12", "Q17"), 100.0)
        br = dict.fromkeys(("Q1", "Q12", "Q17"), 5.0)
        result = conditional_output_conversion_dc(
            q1_base_v=q1, q12_base_v=q12, q17_base_v=q17,
            is_a=is_a, beta_forward=bf, beta_reverse=br,
            temperature_k=temperature, diode_model=model)
        cases.append({
            "id": name,
            "boundary": {"q1_base_v": q1, "q12_base_v": q12,
                         "q17_base_v": q17, "plus_v": 10.0},
            "parameters": {"is_a": 1e-14, "beta_forward": 100.0,
                           "beta_reverse": 5.0,
                           "temperature_k": temperature,
                           "diode_model": (None if model is None else {
                               "is_a": model["is_a"],
                               "ideality": model["ideality"]})},
            "node_v": [result["nodes_v"][name] for name in NODES],
            "max_kcl_residual_a": result["max_kcl_residual_a"],
            "diode_currents_a": result["diode_currents_a"]})
    return {
        "schema": "rf-d/output-conversion-dc-vectors/v1",
        "sources": ["SVC-9 Fig. 9-11 PDF p. 13",
                    "SVC-9 Table 7-8 PDF pp. 30-31"],
        "node_order": list(NODES),
        "method": "isolated six-node Ebers-Moll DC, bases imposed, C2/C4 open",
        "units": {"voltage": "V", "current": "A", "temperature": "K"},
        "cases": cases,
        "interpretation": "Conditional laboratory parameters; no measured 2N4058 population."}


if __name__ == "__main__":
    print(json.dumps(generate_vectors(), indent=2))
