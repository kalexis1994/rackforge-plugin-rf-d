"""Independent 71-node follower/R59/Q18-to-J7 DC/transient FD oracle.

C2 of board2 and Q15 reset base are imposed. No contour/latch phase policy.
The existing eighteen audio/control capacitor histories are integrated here.
"""
import copy
import json
import math
from pathlib import Path

from circuit66_dc_vectors import dc_evaluator
from circuit66_r21_vectors import charges
from circuit66_vca_dc_vectors import boundary_values
from circuit66_vca_release_probes import transient_evaluator
from cutoff_j7_vectors import setup
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from loudness_contour_reference import Semiconductors
from loudness_follower_vectors import evaluate as follower_evaluate, solve as follower_solve

try:
    import numpy as np
except ImportError:
    np = None

OUTPUT = Path(__file__).resolve().parents[1]/"evidence/circuit71_loudness_vectors.json"
GATES = dict(node_v=1e-6, capacitor_v=1e-6, current_a=1e-9, jack_v=1e-6,
             kcl_a=1e-11, correction_v=1e-8)


def evaluator(values, c2, reset, *, old=None, bus=0.0, lower=2000):
    # Freeze legacy volume at ZERO, then add its missing R59 terminal explicitly.
    zero = boundary_values(values, 0.0, 2.0)
    if old is None:
        audio = dc_evaluator(zero, values[4], lower)
    else:
        audio = transient_evaluator(zero, old,
            dict(bus_v=bus, loudness_v=0.0, q21_base_v=2.0, r21_lower_ohm=lower))
    boundary = dict(c2_v=c2, reset_base_v=reset, supply_v=9.3,
                    load_conductance_s=1/68000, load_reference_v=0.0)
    p = Semiconductors()

    def evaluate(x):
        r, _ = audio(x[:66])
        # Audio oracle uses incoming-current sign on row32. Follower rows use
        # outgoing-current sign. FD treats those row signs independently.
        r[32] += x[69]/68000
        follower, _ = follower_evaluate(x[66:], dict(boundary, load_reference_v=x[32]), p)
        return r+follower
    return evaluate


def solve(seed, evaluate, *, kcl_gate=1e-11, correction_gate=1e-8):
    x = list(seed)
    for iteration in range(48):
        r = evaluate(x)
        j = [[0.0]*71 for _ in x]
        for col in range(71):
            shifted = x.copy()
            shifted[col] += 1e-6
            rr = evaluate(shifted)
            for row in range(71):
                j[row][col] = (rr[row]-r[row])/1e-6
        direction = (np.linalg.solve(np.asarray(j), -np.asarray(r)).tolist()
                     if np is not None else _solve_linear(j, [-v for v in r]))
        kcl = max(abs(v) for v in r)
        correction = max(abs(v) for v in direction)
        if kcl < kcl_gate and correction < correction_gate:
            return x, dict(iterations=iteration, kcl_a=kcl, correction_v=correction)
        for power in range(32):
            trial = [v+2**-power*d for v, d in zip(x, direction)]
            try:
                rr = evaluate(trial)
                # At the rounding floor, accept a full correction that keeps
                # the current gate; the next iteration still verifies voltage.
                if max(abs(v) for v in rr) < kcl or kcl < kcl_gate and max(abs(v) for v in rr) < kcl_gate:
                    x = trial
                    break
            except (ValueError, OverflowError):
                continue
        else:
            raise ValueError("71-node FD line-search exhausted")
    raise ValueError("71-node FD iteration budget exhausted")


def memory(x, bus, old=None):
    cv = charges(x[:66], bus)
    c10 = x[22]-x[7]
    if old is not None:
        g = 10e-6*48000
        current = g/(1+g*25500)*(x[22]-x[7]-old["c10_v"])
        c10 -= 25500*current
    return dict(node_v=x[:66], capacitor_v=cv, c10_v=c10)


def metrics(x, c2, reset):
    p = Semiconductors()
    _, currents = follower_evaluate(x[66:], dict(c2_v=c2, reset_base_v=reset, supply_v=9.3,
        load_conductance_s=1/68000, load_reference_v=x[32]), p)
    low = 1/(1/1000+1/100000)
    wiper = 1/(1/2500+1/10000+1/(33000+low))
    hi = x[47]*wiper/(3500+wiper)
    return dict(timing_current_a=currents[0], reset_current_a=currents[1],
                r59_current_a=(x[69]-x[32])/68000,
                tail_current_a=(x[5]-x[65])/680, j7_v=x[61],
                j4_hi_v=hi, j5_lo_v=hi*low/(33000+low))


def generate():
    cases = []
    for r61 in (200, 200000):
        values = setup(r61)
        seed66 = list(values[5]["node_v"])
        for reset in (.01, .7):
            initial_c2 = 3.2
            follower, _, _ = follower_solve(dict(c2_v=initial_c2, reset_base_v=reset,
                supply_v=9.3, load_conductance_s=1/68000, load_reference_v=seed66[32]))
            x, diag = solve(seed66+follower, evaluator(values, initial_c2, reset))
            initial = dict(node_v=x, memory=memory(x, 0), diagnostics=diag,
                           metrics=metrics(x, initial_c2, reset))
            dc_rows = []
            for target in (.8469345758149237, 0.0, 6.0, 9.3, 3.2):
                anchor = initial_c2
                for stage in range(1,65):
                    c2 = target if stage == 64 else anchor+(target-anchor)*stage/64
                    x, diag = solve(x, evaluator(values, c2, reset))
                dc_rows.append(dict(c2_v=target, node_v=x, diagnostics=diag,
                                    metrics=metrics(x, target, reset)))
                initial_c2 = target
            # Start transient from the independently solved final DC root.
            old = memory(x, 0)
            transient_initial = copy.deepcopy(old)
            transient_initial["follower_v"] = x[66:]
            rows = []
            c2_previous = 3.2
            for sample in range(64):
                c2 = (3.2 if sample < 8 else 6.0 if sample < 24 else
                      .8469345758149237 if sample < 40 else 0.0 if sample < 48 else 3.2)
                bus = .02*math.sin(2*math.pi*100*sample/48000)
                evaluate = evaluator(values, c2, reset, old=old, bus=bus)
                direct_error = None
                try:
                    x, diag = solve(x, evaluate)
                except ValueError as exc:
                    direct_error = str(exc)
                    for stage in range(65):
                        source = c2 if stage == 64 else c2_previous+(c2-c2_previous)*stage/64
                        x, diag = solve(x, evaluator(values, source, reset, old=old, bus=bus))
                new = memory(x, bus, old)
                rows.append(dict(sample=sample, c2_v=c2, reset_base_v=reset, bus_v=bus,
                    node_v=x, capacitor_v=new["capacitor_v"], c10_v=new["c10_v"],
                    metrics=metrics(x, c2, reset), diagnostics=diag, direct_error=direct_error))
                old, c2_previous = new, c2
            cases.append(dict(r61_ohm=r61, reset_base_v=reset, initial=initial, dc_rows=dc_rows,
                              transient_initial=transient_initial, rows=rows))
    return dict(schema="rf-d/circuit71-loudness-vectors/v1", gates=GATES,
        method="full 71-node FD Newton; own DC and 18 capacitor histories; imposed board2 C2/reset",
        linear_solver="numpy" if np is not None else "python", cases=cases,
        audio_admitted=False, physical_contour_switching_admitted=False)


if __name__ == "__main__":
    report = generate()
    OUTPUT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(cases=len(report["cases"]), steps=256,
        direct_failures=sum(r["direct_error"] is not None for c in report["cases"] for r in c["rows"]))))
