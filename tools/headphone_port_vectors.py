"""Reproducible 62-node vectors and an independent port comparison gate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from headphone_coupled_transient_reference import (
    initial_coupled_headphone_state, nonlinear_coupled_headphone_step)
from headphone_amp_active_dc_reference import NODES as AMP_NODES
from headphone_transient_stress_reference import _scenario, reference_dc
from output_diode_reference import diode_model_from_reference
from filter_ladder_ebers_moll_dc_reference import NODE_NAMES as LADDER_NODES
from filter_recovery_active_dc_reference import NODES as RECOVERY_NODES
from vca_cascaded_output_dc_reference import NODES as VCA_OUTPUT_NODES


EVIDENCE = (Path(__file__).resolve().parents[1] / "evidence"
            / "headphone_port_vectors.json")
FIELDS = ("j7_tip_v", "r21_wiper_v", "c2_right_v", "j4_hi_v", "j5_lo_v")
NODE_ORDER = (tuple(f"B4_{name}" for name in LADDER_NODES+RECOVERY_NODES)
              + ("B4_C6_LEFT",)
              + tuple(f"B4_{name}" for name in VCA_OUTPUT_NODES)
              + ("B4_C2_RIGHT", "B4_PIN22", "PANEL_R21_WIPER")
              + tuple(f"B3_{name}" for name in AMP_NODES)
              + ("J7_TIP_RING",))
TOLERANCES = {
    "j7_tip_v": {"absolute_v": 1e-6, "relative": 1e-4},
    "other_output": {"absolute_v": 1e-5, "relative": 1e-4},
    "checkpoint_node": {"absolute_v": 1e-4, "relative": 1e-4},
    "max_kcl_residual_a": 1e-10,
}


def _schedule(case: str, step: int) -> tuple[float, bool, int | None]:
    if case == "ramp_switch_load":
        bus = (0.5*min(step/7, 1) if step < 16 else
               -0.5 if step < 24 else 0.0)
        switch = step < 12 or step >= 24
        load = 32 if step < 16 or step >= 24 else None
    elif case == "bipolar_slow":
        bus = (1.0 if step < 8 else -1.0 if step < 16
               else 1.0 if step < 24 else 0.0)
        switch = step < 8 or step >= 24
        load = None if step < 16 else 32
    elif case == "board3_cool_sine":
        bus = 0.5*math.sin(2*math.pi*100*(step+1)/9600)
        switch, load = True, 32
    else:
        raise ValueError("unknown vector case")
    return bus, switch, load


def generate_vectors() -> dict:
    if len(NODE_ORDER) != 62 or len(set(NODE_ORDER)) != 62:
        raise ValueError("headphone port node order must contain 62 unique names")
    assumption = _scenario()
    board4 = reference_dc(assumption)
    panel = dict(
        r14_pin7_to_pin6_ohm=assumption["r14_pin7_to_pin6_ohm"],
        r73_bottom_side_to_wiper_ohm=assumption["r73_bottom_side_to_wiper_ohm"],
        r20_wiper_to_ground_ohm=assumption["r20_wiper_to_ground_ohm"],
        r21_wiper_to_ground_ohm=assumption["r21_wiper_to_ground_ohm"],
        hi_load_ohm=assumption["hi_load_ohm"],
        lo_load_ohm=assumption["lo_load_ohm"])
    cases = []
    for name, dt_s, board3_temp in (
            ("ramp_switch_load", 1/48000, assumption["temperature_k"]),
            ("bipolar_slow", 1/4800, assumption["temperature_k"]),
            ("board3_cool_sine", 1/9600, 285.0)):
        base = board4.copy()
        base["temperature_k"] = board3_temp
        base["diode_model"] = diode_model_from_reference(
            ideality=assumption["diode_ideality"],
            forward_voltage_at_100ma_v=(
                assumption["diode_forward_voltage_at_100ma_v"]),
            temperature_k=board3_temp)
        state = initial_coupled_headphone_state(**base)
        initial = {
            "node_v": list(state["node_v"]),
            "c10_capacitor_v": state["c10_capacitor_v"],
            "amp_capacitor_v": dict(state["amp_capacitor_v"]),
            "bus_v": state["bus_v"]}
        steps = []
        for step in range(32):
            bus, switch, load = _schedule(name, step)
            state = nonlinear_coupled_headphone_step(
                **base, **panel, previous_state=state,
                bus_v=bus, dt_s=dt_s, sw18_on=switch,
                tip_load_ohm=load, ring_load_ohm=load,
                newton_max_iterations=16,
                line_search_max_halvings=16)
            expected = {field: state[field] for field in FIELDS}
            expected["max_kcl_residual_a"] = state["max_charge_kcl_residual_a"]
            if step in (0, 7, 15, 23, 31):
                expected["node_v"] = list(state["node_v"])
                expected["c10_capacitor_v"] = state["c10_capacitor_v"]
                expected["amp_capacitor_v"] = dict(state["amp_capacitor_v"])
            steps.append({"bus_v": bus, "sw18_on": switch,
                          "tip_ring_ohm": load, "expected": expected})
        cases.append({"id": name, "dt_s": dt_s,
                      "board4_temperature_k": assumption["temperature_k"],
                      "board3_temperature_k": board3_temp,
                      "initial_state": initial, "steps": steps})
    return {
        "schema": "rf-d/headphone-port-vectors/v1",
        "sources": ["SVC-9 Fig. 9-8 PDF p. 10",
                    "SVC-9 Fig. 9-11 PDF p. 13",
                    "SVC-9 Fig. 9-17 PDF p. 19"],
        "assumed_parameters": assumption,
        "integration": "implicit_euler_zoh_bus_at_step_start",
        "reference_solver": {"jacobian_method": "hybrid",
                             "linear_solver": "python",
                             "newton_max_iterations": 16,
                             "line_search_max_halvings": 16},
        "tolerances": TOLERANCES,
        "node_order": list(NODE_ORDER),
        "units": {"voltage": "V", "time": "s", "current": "A",
                  "temperature": "K", "resistance": "ohm"},
        "cases": cases,
        "interpretation": "Numerical port gate for conditioned circuit, not measured Model D audio."}


def compare_candidate(reference: dict, candidate: dict) -> dict:
    """Check a future native trace against predeclared numerical tolerances."""
    if (reference.get("schema") != "rf-d/headphone-port-vectors/v1"
            or candidate.get("schema") != "rf-d/headphone-port-candidate/v1"):
        raise ValueError("incompatible headphone vector schema")
    expected_cases = reference["cases"]
    actual_cases = candidate.get("cases")
    if (not isinstance(actual_cases, list)
            or [row["id"] for row in actual_cases]
            != [row["id"] for row in expected_cases]):
        raise ValueError("candidate case identities or order differ")
    worst_error = {field: 0.0 for field in FIELDS}
    node_error = 0.0
    count = 0
    for expected_case, actual_case in zip(expected_cases, actual_cases):
        actual_steps = actual_case.get("steps")
        if not isinstance(actual_steps, list) or len(actual_steps) != len(expected_case["steps"]):
            raise ValueError("candidate step count differs")
        for index, (expected_step, actual) in enumerate(zip(
                expected_case["steps"], actual_steps)):
            expected = expected_step["expected"]
            context = f"{expected_case['id']} sample {index}"
            for field in FIELDS:
                value = actual[field]
                if type(value) not in (int, float) or not math.isfinite(value):
                    raise ValueError(f"nonfinite {field} at {context}")
                error = abs(value-expected[field])
                tolerance = (TOLERANCES["j7_tip_v"] if field == "j7_tip_v"
                             else TOLERANCES["other_output"])
                if error > tolerance["absolute_v"]+tolerance["relative"]*abs(expected[field]):
                    raise ValueError(f"{field} exceeds port tolerance at {context}")
                worst_error[field] = max(worst_error[field], error)
            kcl = actual["max_kcl_residual_a"]
            if (type(kcl) not in (int, float) or not math.isfinite(kcl)
                    or kcl < 0 or kcl >= TOLERANCES["max_kcl_residual_a"]):
                raise ValueError(f"KCL exceeds port limit at {context}")
            if "node_v" in expected:
                nodes = actual.get("node_v")
                if not isinstance(nodes, list) or len(nodes) != 62:
                    raise ValueError(f"missing 62-node checkpoint at {context}")
                for expected_v, actual_v in zip(expected["node_v"], nodes):
                    if type(actual_v) not in (int, float) or not math.isfinite(actual_v):
                        raise ValueError(f"nonfinite checkpoint at {context}")
                    error = abs(actual_v-expected_v)
                    tolerance = TOLERANCES["checkpoint_node"]
                    if error > (tolerance["absolute_v"]
                                + tolerance["relative"]*abs(expected_v)):
                        raise ValueError(f"node checkpoint exceeds port tolerance at {context}")
                    node_error = max(node_error, error)
                for key in ("c10_capacitor_v",):
                    actual_v = actual.get(key)
                    if type(actual_v) not in (int, float) or not math.isfinite(actual_v):
                        raise ValueError(f"missing finite capacitor state at {context}")
                    tolerance = TOLERANCES["checkpoint_node"]
                    if abs(actual_v-expected[key]) > (
                            tolerance["absolute_v"]
                            + tolerance["relative"]*abs(expected[key])):
                        raise ValueError(f"capacitor state exceeds port tolerance at {context}")
                actual_caps = actual.get("amp_capacitor_v")
                if not isinstance(actual_caps, dict) or set(actual_caps) != {"C19", "C15", "C21"}:
                    raise ValueError(f"missing amplifier capacitor state at {context}")
                for key in ("C19", "C15", "C21"):
                    actual_v = actual_caps[key]
                    expected_v = expected["amp_capacitor_v"][key]
                    if type(actual_v) not in (int, float) or not math.isfinite(actual_v):
                        raise ValueError(f"nonfinite amplifier capacitor state at {context}")
                    tolerance = TOLERANCES["checkpoint_node"]
                    if abs(actual_v-expected_v) > (
                            tolerance["absolute_v"]
                            + tolerance["relative"]*abs(expected_v)):
                        raise ValueError(f"amplifier capacitor state exceeds port tolerance at {context}")
            count += 1
    return {"cases": len(expected_cases), "steps": count,
            "max_output_error_v": worst_error,
            "max_checkpoint_node_error_v": node_error,
            "passed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    if args.candidate is None:
        print(json.dumps(generate_vectors(), indent=2))
    else:
        reference = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        print(json.dumps(compare_candidate(reference, candidate), indent=2))
