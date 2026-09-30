"""Independent FD windows at switches/late time, with declared native histories.

This checks short trajectories conditional on the same captured capacitor state,
not independent integration of the entire preceding two-second native trace.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from cutoff_j7_vectors import setup
from headphone_coupled_transient_reference import nonlinear_coupled_headphone_step

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "evidence/circuit66_stress_probe_inputs.json"
OUTPUT = ROOT / "evidence/circuit66_stress_probe_vectors.json"
GATES = dict(node_error_v=1e-6, j7_error_v=1e-6, capacitor_error_v=1e-6,
             tail_error_a=1e-9, oracle_kcl_a=1e-10)


def generate_vectors(inputs=None):
    capture = inputs if inputs is not None else json.loads(INPUT.read_text(encoding="utf-8-sig"))
    if not capture["passed"] or len(capture["probe_windows"]) != 48:
        raise ValueError("48 complete captured windows required")
    setups = {r61: setup(r61) for r61 in (200, 200000)}
    windows = []
    maximum = dict(node_error_v=0.0, j7_error_v=0.0, capacitor_error_v=0.0,
                   tail_error_a=0.0, oracle_kcl_a=0.0)
    for window in capture["probe_windows"]:
        ladder, recovery, output, hp, controls, _, _ = copy.deepcopy(setups[window["r61_ohm"]])
        initial = window["initial"]
        cv = initial["capacitor_v"]
        state = dict(node_v=tuple(initial["node_v"]), c10_capacitor_v=initial["c10_v"],
                     c18_v=cv[16], bus_v=window["previous_bus_v"],
                     amp_capacitor_v=dict(zip(("C19", "C15", "C21"), cv[13:16])))
        if len(window["rows"]) != 4:
            raise ValueError("incomplete captured window")
        rows = []
        for row in window["rows"]:
            b = row["boundary"]
            vp = output["network_parameters"]
            vp["first_parameters"]["core_parameters"]["loudness_v"] = b["loudness_v"]
            vp["second_parameters"]["q21_base_v"] = b["q21_base_v"]
            old = copy.deepcopy(state)
            state = nonlinear_coupled_headphone_step(
                ladder_dc=ladder, recovery_dc=recovery, cascaded_output_dc=output,
                previous_state=state, bus_v=b["bus_v"], dt_s=1/window["sample_rate_hz"],
                r14_pin7_to_pin6_ohm=b["r14_ohm"], r73_bottom_side_to_wiper_ohm=500,
                r20_wiper_to_ground_ohm=2500, hi_load_ohm=10000, lo_load_ohm=100000,
                r21_wiper_to_ground_ohm=b["r21_lower_ohm"],
                tip_load_ohm=b["tip_load_ohm"], ring_load_ohm=b["ring_load_ohm"],
                sw18_on=b["sw18_on"], jacobian_method="finite_difference", linear_solver="python",
                cutoff_inputs=dict(controls, panel=b["panel"], range_fraction=b["range_fraction"]), **hp)
            if b["r14_ohm"] is None and state["c10_capacitor_v"] != old["c10_capacitor_v"]:
                raise AssertionError("disconnected C10 consumed history")
            native = row["native"]
            errors = dict(
                node_error_v=max(abs(a-z) for a,z in zip(state["node_v"], native["node_v"])),
                j7_error_v=abs(state["j7_tip_v"]-native["node_v"][61]),
                capacitor_error_v=max(abs(state["c10_capacitor_v"]-native["c10_v"]),
                                      abs(state["c18_v"]-native["capacitor_v"][16]),
                                      *(abs(state["amp_capacitor_v"][name]-native["capacitor_v"][i])
                                        for i,name in zip(range(13,16), ("C19","C15","C21")))),
                tail_error_a=abs(state["tail_current_a"]-(native["node_v"][5]-native["node_v"][65])/680),
                oracle_kcl_a=state["max_charge_kcl_residual_a"])
            for key,value in errors.items():
                maximum[key] = max(maximum[key], value)
                if not value < GATES[key]:
                    raise AssertionError(f"rate={window['sample_rate_hz']} R61={window['r61_ohm']} "
                                         f"sample={row['sample']} {key}={value} >= {GATES[key]}")
            rows.append(dict(sample=row["sample"], boundary=b, node_v=list(state["node_v"]),
                             c10_v=state["c10_capacitor_v"], c18_v=state["c18_v"],
                             amp_capacitor_v=state["amp_capacitor_v"],
                             tail_current_a=state["tail_current_a"], j7_v=state["j7_tip_v"],
                             j4_hi_v=state["j4_hi_v"], j5_lo_v=state["j5_lo_v"],
                             max_kcl_a=state["max_charge_kcl_residual_a"],
                             native_comparison=errors))
        windows.append(dict(sample_rate_hz=window["sample_rate_hz"], r61_ohm=window["r61_ohm"],
                            first_sample=window["first_sample"], initial=initial, rows=rows))
    return dict(schema="rf-d/circuit66-stress-probe-vectors/v1",
                method="independent Python full FD 66-node Newton, four consecutive steps per captured history",
                history_origin="native long stress before each window; not full independent long integration",
                input_sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),
                gates=GATES, maxima=maximum, windows=windows, audio_fidelity_claim=False)


if __name__ == "__main__":
    result = generate_vectors()
    OUTPUT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(windows=len(result["windows"]), steps=sum(len(w["rows"]) for w in result["windows"]),
                          maxima=result["maxima"]), indent=2))
