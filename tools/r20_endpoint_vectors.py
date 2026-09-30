"""Exact panel shorts and independent full-FD 66-node transient oracle."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from cutoff_j7_vectors import setup
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from headphone_coupled_transient_reference import nonlinear_coupled_headphone_step

OUTPUT = Path(__file__).resolve().parents[1] / "evidence/r20_endpoint_vectors.json"


def explicit_panel(c2, lower, sw18, hi_load, lo_load):
    """Solve PIN21/HI/LO KCL with exact node identification at the shorts.

    Independent of panel_load_reduction: no equivalent impedance formulas.
    R75 stays in the nodal graph. Grounded and disconnected nodes are fixed
    by topology, never a conductance of infinity or an epsilon resistance.
    """
    if lower not in (0, 5000):
        raise ValueError("exact endpoint required")
    if not sw18:
        pin21 = c2 * 5000 / 6000 if lower == 0 else 0.0
        return dict(pin21_v=pin21, hi_v=0.0, lo_v=0.0, r75_a=(c2-pin21)/1000)
    if lower == 0:
        # HI/LO are grounded, PIN21 connected through the entire pot.
        pin21 = _solve_linear([[1/1000 + 1/5000]], [c2/1000])[0]
        return dict(pin21_v=pin21, hi_v=0.0, lo_v=0.0, r75_a=(c2-pin21)/1000)
    # PIN21=HI. The remaining lower segment and both jack loads remain.
    g = [[1/1000 + 1/5000 + 1/hi_load + 1/33000, -1/33000],
         [-1/33000, 1/33000 + 1/1000 + 1/lo_load]]
    hi, lo = _solve_linear(g, [c2/1000, 0.0])
    return dict(pin21_v=hi, hi_v=hi, lo_v=lo, r75_a=(c2-hi)/1000)


def generate_vectors():
    cases = []
    max_panel_error = 0.0
    for r61 in (200, 200000):
        values = setup(r61)
        ladder, recovery, output, hp, controls, initial, _ = values
        initial["node_v"] = list(initial["node_v"])
        for lower in (0, 5000):
            for sw18 in (False, True):
                state = copy.deepcopy(initial)
                rows = []
                for index in range(16):
                    segment = lower if 4 <= index < 12 else 2500
                    switch = sw18 if 4 <= index < 12 else True
                    bus = 0.02*math.sin(2*math.pi*100*(index+1)/48000)
                    state = nonlinear_coupled_headphone_step(
                        ladder_dc=ladder, recovery_dc=recovery, cascaded_output_dc=output,
                        previous_state=state, bus_v=bus, dt_s=1/48000,
                        r14_pin7_to_pin6_ohm=25000, r73_bottom_side_to_wiper_ohm=500,
                        r20_wiper_to_ground_ohm=segment, hi_load_ohm=10000, lo_load_ohm=100000,
                        r21_wiper_to_ground_ohm=2000, tip_load_ohm=32, ring_load_ohm=32,
                        sw18_on=switch, jacobian_method="finite_difference",
                        linear_solver="python", cutoff_inputs=controls, **hp)
                    if state["max_charge_kcl_residual_a"] >= 1e-10:
                        raise AssertionError("oracle KCL gate")
                    if 4 <= index < 12:
                        explicit = explicit_panel(state["node_v"][47], segment, switch, 10000, 100000)
                        err = max(abs(explicit["hi_v"]-state["j4_hi_v"]),
                                  abs(explicit["lo_v"]-state["j5_lo_v"]))
                        max_panel_error = max(max_panel_error, err)
                        if err >= 1e-12:
                            raise AssertionError("explicit panel gate")
                    rows.append(dict(index=index, r20_lower_ohm=segment, sw18_on=switch,
                                     bus_v=bus, node_v=list(state["node_v"]),
                                     c10_v=state["c10_capacitor_v"], c18_v=state["c18_v"],
                                     amp_capacitor_v=state["amp_capacitor_v"],
                                     j7_v=state["j7_tip_v"], j4_hi_v=state["j4_hi_v"],
                                     j5_lo_v=state["j5_lo_v"], tail_current_a=state["tail_current_a"],
                                     max_kcl_a=state["max_charge_kcl_residual_a"]))
                cases.append(dict(r61_ohm=r61, target_lower_ohm=lower, target_sw18_on=sw18,
                                  controls=controls, initial=initial, rows=rows))
    return dict(schema="rf-d/r20-endpoint-vectors/v1", dt_s=1/48000,
                method="full FD 66-node Newton; exact panel node identification cross-check",
                sources=["SVC-9 Fig. 9-17 PDF p. 19", "SVC-9 Fig. 9-8 PDF p. 10",
                         "SVC-9 Fig. 9-11 PDF p. 13"],
                gates=dict(node_error_v=1e-6, jack_error_v=1e-6, capacitor_error_v=1e-6,
                           tail_error_a=1e-9, oracle_kcl_a=1e-10, panel_error_v=1e-12),
                max_explicit_panel_error_v=max_panel_error, cases=cases, audio_fidelity_claim=False)


if __name__ == "__main__":
    result = generate_vectors()
    OUTPUT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(cases=len(result["cases"]), steps=128,
                         max_panel_error_v=result["max_explicit_panel_error_v"])))
