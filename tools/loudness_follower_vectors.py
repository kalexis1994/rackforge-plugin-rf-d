"""Independent five-node FD oracle of board-2 loudness follower/load port.

This is algebraic, with C2 voltage and Q15 base imposed. It does not select
contour phases, solve the latch, or close the board-4 Q18 base load.
"""
from dataclasses import asdict
import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _device, _solve_linear
from loudness_contour_reference import Semiconductors
from semiconductor_ideal import thermal_voltage_v

NODES = ["FOLLOWER_BASE", "FOLLOWER_MID", "FOLLOWER_SUPPLY", "LOUDNESS_OUT", "RESET_FEEDBACK"]
OUTPUT = Path(__file__).resolve().parents[1]/"evidence/loudness_follower_vectors.json"


def evaluate(x, boundary, p):
    base, mid, supply, out, feedback = x
    vt = thermal_voltage_v(p.temperature_k)
    q3 = _device(base, supply, mid, p.is_a, p.beta_forward, p.beta_reverse, vt)
    q2 = _device(mid, supply, out, p.is_a, p.beta_forward, p.beta_reverse, vt)
    exponent = (feedback-boundary["reset_base_v"])/(p.diode_ideality*vt)
    if exponent > 45:
        raise ValueError("diode exponential domain")
    diode = p.germanium_is_a*math.expm1(exponent)
    timing = (boundary["c2_v"]-base)/10000
    load = boundary["load_conductance_s"]*(out-boundary["load_reference_v"])
    residual = [-timing+q3["base_a"], -q3["emitter_a"]+q2["base_a"],
                (supply-boundary["supply_v"])/560+q3["collector_a"]+q2["collector_a"],
                -q2["emitter_a"]+(out-feedback)/6800+load,
                (feedback-out)/6800+(feedback+10)/16900+diode]
    return residual, [timing, -diode, -load]


def solve(boundary, p=Semiconductors(), seed=None):
    base = min(boundary["c2_v"]-.02, boundary["supply_v"]+.2)
    mid, out = base-.55, base-1.2
    feedback = min((out/6800-10/16900)/(1/6800+1/16900), boundary["reset_base_v"]+.4)
    x = list(seed) if seed is not None else [base, mid, boundary["supply_v"]-.25, out, feedback]
    for iteration in range(40):
        r, _ = evaluate(x, boundary, p)
        j = [[0.0]*5 for _ in x]
        for col in range(5):
            a, b = x.copy(), x.copy()
            a[col] -= 1e-6
            b[col] += 1e-6
            ra, _ = evaluate(a, boundary, p)
            rb, _ = evaluate(b, boundary, p)
            for row in range(5):
                j[row][col] = (rb[row]-ra[row])/2e-6
        direction = _solve_linear(j, [-v for v in r])
        kcl = max(abs(v) for v in r)
        correction = max(abs(v) for v in direction)
        # Port derivatives can move weak nodes far less than 10nV. Solve the
        # FD reference more tightly so early stopping cannot flatten a tangent.
        if kcl < 1e-13 and correction < 1e-12:
            _, currents = evaluate(x, boundary, p)
            return x, currents, dict(iterations=iteration, kcl_a=kcl, correction_v=correction)
        for power in range(24):
            trial = [v+2**-power*d for v, d in zip(x, direction)]
            try:
                rr, _ = evaluate(trial, boundary, p)
                if max(abs(v) for v in rr) < kcl:
                    x = trial
                    break
            except ValueError:
                continue
        else:
            raise ValueError("follower FD line search exhausted")
    raise ValueError("follower FD Newton budget exhausted")


def generate():
    cases = []
    for bf in (50.0, 100.0, 200.0):
        p = Semiconductors(beta_forward=bf)
        for c2 in (0.0, .8469345758149237, 3.0, 6.0, 9.3):
            for reset in (.01, .7):
                for g, ref in ((0.0, 0.0), (1/68000, .7)):
                    boundary = dict(c2_v=c2, reset_base_v=reset, supply_v=9.3,
                                    load_conductance_s=g, load_reference_v=ref)
                    x, currents, diag = solve(boundary, p)
                    gradients = [[0.0]*3 for _ in range(3)]
                    out_gradient = []
                    for col, key in enumerate(("c2_v", "reset_base_v", "load_reference_v")):
                        a, b = boundary.copy(), boundary.copy()
                        a[key] -= 1e-5
                        b[key] += 1e-5
                        xa, ia, _ = solve(a, p, seed=x)
                        xb, ib, _ = solve(b, p, seed=x)
                        for row in range(3):
                            gradients[row][col] = (ib[row]-ia[row])/2e-5
                        out_gradient.append((xb[3]-xa[3])/2e-5)
                    cases.append(dict(parameters=asdict(p), boundary=boundary, node_v=x,
                                      port_current_a=currents, port_jacobian_s=gradients,
                                      output_gradient_v_per_v=out_gradient, diagnostics=diag))
    return dict(schema=1, node_order=NODES,
                ports=["C2", "RESET_BASE", "LOAD_REFERENCE"],
                reference_kind="independent central FD roots and port gradients; imposed boundaries",
                jacobian_fd_step_v=1e-6, port_gradient_fd_step_v=1e-5,
                oracle_kcl_gate_a=1e-13, oracle_correction_gate_v=1e-12,
                node_gate_v=1e-6, current_gate_a=1e-10, tangent_gate_s=1e-9,
                output_tangent_gate=1e-6, cases=cases, audio_admitted=False)


if __name__ == "__main__":
    result = generate()
    OUTPUT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(cases=len(result["cases"]),
                         max_kcl_a=max(c["diagnostics"]["kcl_a"] for c in result["cases"]))))
