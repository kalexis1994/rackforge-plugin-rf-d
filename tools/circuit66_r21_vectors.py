"""Independent full FD integration at exact R21 endpoints and restoration.

Python computes its own DC, charges and incoming histories for every step.
The native file is used only for comparison, never as a numerical seed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from circuit66_dc_vectors import dc_evaluator, solve_dc
from circuit66_vca_release_probes import CAPS, transient_evaluator
from cutoff_j7_vectors import setup

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "evidence/circuit66_r21_native.json"
OUTPUT = ROOT / "evidence/circuit66_r21_vectors.json"
GATES = dict(node_error_v=1e-6, capacitor_error_v=1e-6, jack_error_v=1e-6,
             tail_error_a=1e-9, short_error_a=1e-9, kcl_a=1e-11,
             constraint_v=1e-11, correction_v=1e-8)


def charges(x, bus):
    return [x[left]-(x[right] if isinstance(right,int) else
                    bus if right == "BUS" else 10 if right == "PLUS" else 0)
            for left,right,_ in CAPS]


def generate_vectors():
    native = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    assert native["schema"] == "rf-d/circuit66-r21-native/v1"
    assert len(native["cases"]) == 4
    setups = {r:setup(r) for r in (200,200000)}
    cases = []
    maxima = {k:0.0 for k in GATES}
    for case in native["cases"]:
        values = setups[case["r61_ohm"]]
        seed = list(values[5]["node_v"])
        initial,_,_ = solve_dc(seed,dc_evaluator(values,values[4]))
        cold,kcl,correction = solve_dc(seed,dc_evaluator(values,values[4],case["target_lower_ohm"]))
        cold_error = max(abs(a-b) for a,b in zip(cold,case["cold_node_v"]))
        assert cold_error < GATES["node_error_v"]
        old = dict(node_v=initial,capacitor_v=charges(initial,0),c10_v=initial[22]-initial[7])
        rows = []
        for row in case["rows"]:
            lower = row["r21_lower_ohm"]
            boundary = dict(bus_v=row["bus_v"],loudness_v=2,q21_base_v=2,r21_lower_ohm=lower)
            evaluate = transient_evaluator(values,old,boundary)
            x,kcl,correction = solve_dc(old["node_v"],evaluate)
            r,_ = evaluate(x)
            # Recover the eliminated branch current; audit both physical KCL
            # equations explicitly. This current is not a state or resistor.
            i19 = 2.5e-6*48000*(x[49]-x[50]-old["capacitor_v"][13])
            i77 = (x[47]-x[48])/1000
            if lower == 0:
                iupper = (x[48]-x[49])/5000
                short = iupper-i19
                branch_kcl = max(abs(iupper-i77),abs(-iupper+i19+short))
            elif lower == 5000:
                short = i77
                branch_kcl = max(abs(short-i77),abs(-short+x[49]/5000+i19))
            else:
                short,branch_kcl = None,0.0
            physical = max(branch_kcl,*(abs(v) for i,v in enumerate(r) if i != 49 or 0 < lower < 5000))
            constraint = abs(r[49]) if lower in (0,5000) else 0.0
            cv = charges(x,row["bus_v"])
            i10 = 10e-6*48000/(1+10e-6*48000*25500)*(x[22]-x[7]-old["c10_v"])
            c10 = x[22]-x[7]-25500*i10
            low = 1/(1/1000+1/100000)
            wiper = 1/(1/2500+1/10000+1/(33000+low))
            hi = x[47]*wiper/(3500+wiper)
            lo = hi*low/(33000+low)
            tail = (x[5]-x[65])/680
            metrics = dict(node_error_v=max(abs(a-b) for a,b in zip(x,row["node_v"])),
                           capacitor_error_v=max(abs(c10-row["c10_v"]),
                                                 *(abs(a-b) for a,b in zip(cv,row["capacitor_v"]))),
                           jack_error_v=max(abs(x[61]-row["j7_v"]),abs(hi-row["j4_hi_v"]),abs(lo-row["j5_lo_v"])),
                           tail_error_a=abs(tail-row["tail_current_a"]),
                           short_error_a=abs(short-row["short_current_a"]) if short is not None else 0.0,
                           kcl_a=physical,constraint_v=constraint,correction_v=correction)
            for key,value in metrics.items():
                maxima[key] = max(maxima[key],value)
            rows.append(dict(index=row["index"],bus_v=row["bus_v"],r21_lower_ohm=lower,
                             node_v=x,capacitor_v=cv,c10_v=c10,j7_v=x[61],j4_hi_v=hi,j5_lo_v=lo,
                             tail_current_a=tail,short_current_a=short,metrics=metrics,
                             passed=all(v<GATES[k] for k,v in metrics.items())))
            old = dict(node_v=x,capacitor_v=cv,c10_v=c10)
        cases.append(dict(r61_ohm=case["r61_ohm"],target_lower_ohm=case["target_lower_ohm"],
                          controls=values[4],initial_node_v=initial,cold_node_v=cold,
                          cold_error_v=cold_error,rows=rows))
    return dict(schema="rf-d/circuit66-r21-vectors/v1",passed=all(v<GATES[k] for k,v in maxima.items()),
                method="independent full 66-column FD; own DC and all incoming capacitor histories; exact terminal identification",
                input_sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),gates=GATES,maxima=maxima,
                cases=cases,audio_fidelity_claim=False)


if __name__ == "__main__":
    report = generate_vectors()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(passed=report["passed"],steps=sum(len(c["rows"]) for c in report["cases"]),maxima=report["maxima"]),indent=2))
    if not report["passed"]:
        raise SystemExit(1)
