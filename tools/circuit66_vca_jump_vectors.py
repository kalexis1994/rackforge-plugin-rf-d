"""Independent transient integration with abrupt zero/restore VCA sources.

Own DC and capacitor histories; native data supplies stimuli/comparisons only.
Every nonlinear solve retains one incoming history, not numerical substeps.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from circuit66_dc_vectors import dc_evaluator, solve_dc
from circuit66_r21_vectors import charges
from circuit66_vca_release_probes import transient_evaluator
from cutoff_j7_vectors import setup

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT/"evidence/circuit66_vca_jump_prototype.json"
OUTPUT = ROOT/"evidence/circuit66_vca_jump_vectors.json"
GATES = dict(node_error_v=1e-6,capacitor_error_v=1e-6,jack_error_v=1e-6,
             tail_error_a=1e-9,kcl_a=1e-11,correction_v=1e-8)


def generate_vectors():
    native = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    assert native["schema"] == "rf-d/circuit66-vca-jump-native/v1"
    assert len(native["cases"]) == 6
    setups = {r:setup(r) for r in (200,200000)}
    maxima = {k:0.0 for k in GATES}
    cases = []
    for case in native["cases"]:
        values = setups[case["r61_ohm"]]
        x,_,_ = solve_dc(list(values[5]["node_v"]),dc_evaluator(values,values[4]))
        initial = x.copy()
        old = dict(node_v=x,capacitor_v=charges(x,0),c10_v=x[22]-x[7])
        rows = []
        sources = (2.0,2.0)
        for row in case["rows"]:
            b = {key:row[key] for key in ("bus_v","loudness_v","q21_base_v")}
            evaluate = transient_evaluator(values,old,b)
            direct_error = None
            try:
                x,kcl,correction = solve_dc(old["node_v"],evaluate)
            except ValueError as e:
                direct_error = str(e)
                # A restore can put the incoming node seed outside the BJT
                # domain at the requested source. Use 64 (not native 32)
                # numerical source stages; every solve has unchanged incoming
                # capacitors and dt. No native nodes enter this path.
                x = old["node_v"].copy()
                for stage in range(65):
                    intermediate = b.copy()
                    if stage < 64:
                        intermediate["loudness_v"] = sources[0]+(b["loudness_v"]-sources[0])*stage/64
                        intermediate["q21_base_v"] = sources[1]+(b["q21_base_v"]-sources[1])*stage/64
                    x,kcl,correction = solve_dc(x,transient_evaluator(values,old,intermediate))
            cv = charges(x,b["bus_v"])
            i10 = 10e-6*48000/(1+10e-6*48000*25500)*(x[22]-x[7]-old["c10_v"])
            c10 = x[22]-x[7]-25500*i10
            low = 1/(1/1000+1/100000)
            wiper = 1/(1/2500+1/10000+1/(33000+low))
            hi = x[47]*wiper/(3500+wiper)
            lo = hi*low/(33000+low)
            tail = (x[5]-x[65])/680
            metrics = dict(node_error_v=max(abs(a-b) for a,b in zip(x,row["node_v"])),
                           capacitor_error_v=max(abs(c10-row["c10_v"]),*(abs(a-b) for a,b in zip(cv,row["capacitor_v"]))),
                           jack_error_v=max(abs(x[61]-row["j7_v"]),abs(hi-row["j4_hi_v"]),abs(lo-row["j5_lo_v"])),
                           tail_error_a=abs(tail-row["tail_current_a"]),kcl_a=kcl,correction_v=correction)
            for key,value in metrics.items(): maxima[key] = max(maxima[key],value)
            rows.append(dict(sample=row["sample"],boundary=b,node_v=x,capacitor_v=cv,c10_v=c10,
                             j7_v=x[61],j4_hi_v=hi,j5_lo_v=lo,tail_current_a=tail,metrics=metrics,
                             direct_error=direct_error,numerical_source_stages=64 if direct_error else 0,
                             passed=all(v<GATES[k] for k,v in metrics.items())))
            old = dict(node_v=x,capacitor_v=cv,c10_v=c10)
            sources = (b["loudness_v"],b["q21_base_v"])
        cases.append(dict(r61_ohm=case["r61_ohm"],mode=case["mode"],controls=values[4],initial_node_v=initial,rows=rows))
    return dict(schema="rf-d/circuit66-vca-jump-vectors/v1",passed=all(v<GATES[k] for k,v in maxima.items()),
                method="independent full FD integration; direct 40/32 or 64-stage source continuation; own DC and incoming histories",
                input_sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),gates=GATES,maxima=maxima,
                cases=cases,audio_fidelity_claim=False)


if __name__ == "__main__":
    report = generate_vectors()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(passed=report["passed"],steps=sum(len(c["rows"]) for c in report["cases"]),maxima=report["maxima"]),indent=2))
    if not report["passed"]: raise SystemExit(1)
