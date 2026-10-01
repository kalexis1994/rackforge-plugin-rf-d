"""Independent quadrature and differential checks of synthetic charge laws."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np
from junction_charge_reference import Depletion, LowInjectionDiffusion, Junction, ChargeHistory, companion
from loudness_lab_metadata import environment

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/"evidence/junction_charge_probes.json"
GATES = dict(charge_abs_c=1e-20,charge_relative=2e-8,derivative_abs_f=1e-19,derivative_relative=1e-6)


def integral_capacitance(model, start, stop):
    # Independent Gauss-Legendre quadrature of C, split at its analytic knee.
    points, weights = np.polynomial.legendre.leggauss(64)
    lo, hi = sorted((start, stop))
    knee = model.depletion.forward_fraction*model.depletion.potential_v
    edges = [lo]+([knee] if lo < knee < hi else [])+[hi]
    total = 0.0
    for a, b in zip(edges,edges[1:]):
        mid, half = (a+b)/2,(b-a)/2
        total += half*sum(float(w)*model.evaluate(mid+half*float(x))[1] for x,w in zip(points,weights))
    return total if stop >= start else -total


def generate():
    rows = []
    for grading in (0.0,.33,.5,.999999999,1.0):
        for fraction in (0.0,.4,.8):
            for transit in (0.0,3e-9):
                # All values are mathematical test inputs, not fitted 2N3392 data.
                model = Junction(Depletion(7e-12,.75,grading,fraction),LowInjectionDiffusion(transit,1e-14,.026))
                knee = fraction*.75
                for v in (-10.0,-1.0,-1e-12,0.0,1e-12,knee-1e-8,knee,knee+1e-8,.68,.82):
                    q,c = model.evaluate(v)
                    integral = integral_capacitance(model,0.0,v)
                    h = 1e-6
                    q_plus = model.evaluate(v+h)[0]
                    q_minus = model.evaluate(v-h)[0]
                    derivative = (q_plus-q_minus)/(2*h)
                    charge_error,derivative_error = abs(q-integral),abs(c-derivative)
                    rows.append(dict(synthetic_model=asdict(model),voltage_v=v,charge_c=q,capacitance_f=c,
                        quadrature_charge_c=integral,central_derivative_f=derivative,charge_error_c=charge_error,
                        derivative_error_f=derivative_error,
                        charge_gate=charge_error<=GATES["charge_abs_c"]+GATES["charge_relative"]*abs(q),
                        derivative_gate=derivative_error<=GATES["derivative_abs_f"]+GATES["derivative_relative"]*abs(c)))
    model = Junction(Depletion(7e-12,.75,.5,.4),LowInjectionDiffusion(3e-9,1e-14,.026))
    v0,v1,dt = .2,.68,1e-6
    q0,c0 = model.evaluate(v0)
    q1,c1 = model.evaluate(v1)
    result = companion(model,v1,0,ChargeHistory(q0),dt)
    correct = result.current_a[0]
    wrong = c1*(v1-v0)/dt
    paths = [ROOT/"tools/junction_charge_reference.py",ROOT/"tools/junction_charge_probes.py"]
    return dict(schema="rf-d/junction-charge-probes/v1",cases=rows,gates=GATES,environment=environment(),
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        synthetic_parameters_only=True,physical_charge_identified=False,physical_switching_admitted=False,audio_admitted=False,
        nonlinear_increment=dict(start_v=v0,end_v=v1,dt_s=dt,charge_difference_current_a=correct,
            endpoint_capacitance_times_voltage_current_a=wrong,relative_difference=abs(wrong-correct)/abs(correct)))


if __name__ == "__main__":
    report = generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    rows = report["cases"]
    print(json.dumps(dict(cases=len(rows),rejected=sum(not r["charge_gate"] or not r["derivative_gate"] for r in rows),
        max_charge_error_c=max(r["charge_error_c"] for r in rows),max_derivative_error_f=max(r["derivative_error_f"] for r in rows),
        nonlinear_increment_relative_difference=report["nonlinear_increment"]["relative_difference"])))
    if not all(r["charge_gate"] and r["derivative_gate"] for r in rows):
        raise SystemExit(1)
