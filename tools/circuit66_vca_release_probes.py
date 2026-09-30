"""Voltage-conditioned independent KCL probes at imposed VCA source release.

Each probe uses one incoming native capacitor history; this does not integrate
the entire native ramp independently. Failed comparisons remain in the report.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from circuit66_dc_vectors import dc_evaluator, fd_direction, solve_dc as solve_kcl
from cutoff_j7_vectors import setup

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT/"evidence/circuit66_vca_release_survey.json"
OUTPUT = ROOT/"evidence/circuit66_vca_release_probe_vectors.json"
GATES = dict(node_error_v=1e-6, jack_error_v=1e-6, capacitor_error_v=1e-6,
             tail_error_a=1e-9, kcl_a=1e-11, correction_v=1e-8)

# SVC-9 Figs. 9-11 (p.13), 9-8 (p.10), 9-17 (p.19). Node order as the
# documentary 66-node oracle; the two C15 designators belong to different boards.
CAPS = [(8,12,68e-9),(9,13,68e-9),(10,14,68e-9),(11,15,68e-9),
        (4,None,220e-6),(6,"BUS",10e-6),(16,11,0.22e-6),(17,15,0.22e-6),
        (23,None,100e-6),(24,25,0.33e-6),(26,None,220e-6),(40,"PLUS",220e-6),
        (46,47,10e-6),(49,50,2.5e-6),(57,58,220e-12),(60,61,400e-6),(62,None,100e-12)]


def transient_evaluator(values, initial, boundary):
    values = copy.deepcopy(values)
    vp = values[2]["network_parameters"]
    vp["first_parameters"]["core_parameters"]["loudness_v"] = boundary["loudness_v"]
    vp["second_parameters"]["q21_base_v"] = boundary["q21_base_v"]
    dc = dc_evaluator(values, values[4])
    dt = 1/48000

    def evaluate(x):
        r, _ = dc(x)
        for i,(left,right,c) in enumerate(CAPS):
            vright = (x[right] if isinstance(right,int) else
                      boundary["bus_v"] if right == "BUS" else
                      10.0 if right == "PLUS" else 0.0)
            current = c/dt*(x[left]-vright-initial["capacitor_v"][i])
            r[left] += (-1 if left < 48 else 1)*current
            if isinstance(right,int):
                r[right] -= (-1 if right < 48 else 1)*current
        gc = 10e-6/dt
        current = gc/(1+gc*25500)*(x[22]-x[7]-initial["c10_v"])
        r[22] -= current
        r[7] += current
        return r, {}

    return evaluate


def generate_vectors():
    capture = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    if capture["schema"] != "rf-d/circuit66-vca-release-survey/v1" or len(capture["cases"]) != 28:
        raise ValueError("complete 28-case release survey required")
    setups = {r:setup(r) for r in (200,200000)}
    probes = []
    failures = 0
    maxima = dict(node_error_v=0.0, jack_error_v=0.0, capacitor_error_v=0.0,
                  tail_error_a=0.0, native_kcl_a=0.0, native_correction_v=0.0,
                  oracle_kcl_a=0.0, oracle_correction_v=0.0)
    for case in capture["cases"]:
        for probe in case["probes"]:
            evaluate = transient_evaluator(setups[case["r61_ohm"]],probe["initial"],probe["boundary"])
            native = probe["native"]["node_v"]
            nr, _ = evaluate(native)
            native_correction = max(abs(v) for v in fd_direction(native,nr,evaluate))
            # Start from the captured candidate, then refine with independent
            # FD until both KCL and voltage criteria are admitted. Every solve
            # retains the same incoming capacitor history throughout.
            x, kcl, correction = solve_kcl(native,evaluate)
            cv = []
            for left,right,_ in CAPS:
                rv = (x[right] if isinstance(right,int) else
                      probe["boundary"]["bus_v"] if right == "BUS" else
                      10.0 if right == "PLUS" else 0.0)
                cv.append(x[left]-rv)
            i10 = 10e-6*48000/(1+10e-6*48000*25500)*(x[22]-x[7]-probe["initial"]["c10_v"])
            c10 = x[22]-x[7]-25500*i10
            low = 1/(1/1000+1/100000)
            wiper = 1/(1/2500+1/10000+1/(33000+low))
            hi = x[47]*(2500+wiper)/(3500+wiper)*wiper/(2500+wiper)
            lo = hi*low/(33000+low)
            errors = dict(node_error_v=max(abs(a-b) for a,b in zip(x,native)),
                          jack_error_v=max(abs(x[61]-native[61]),abs(hi-probe["native"]["j4_hi_v"]),
                                           abs(lo-probe["native"]["j5_lo_v"])),
                          capacitor_error_v=max(abs(c10-probe["native"]["c10_v"]),
                                                *(abs(a-b) for a,b in zip(cv,probe["native"]["capacitor_v"]))),
                          tail_error_a=abs((x[5]-x[65]-native[5]+native[65])/680))
            passed = all(v<GATES[k] for k,v in errors.items())
            failures += not passed
            metrics = dict(errors,native_kcl_a=max(abs(v) for v in nr),native_correction_v=native_correction,
                           oracle_kcl_a=kcl,oracle_correction_v=correction)
            for k,v in metrics.items(): maxima[k] = max(maxima[k],v)
            probes.append(dict(r61_ohm=case["r61_ohm"],both_controls=case["both_controls"],
                               ramp_samples=case["ramp_samples"],sample=probe["sample"],
                               initial=probe["initial"],boundary=probe["boundary"],
                               node_v=x,capacitor_v=cv,c10_v=c10,
                               worst_node=max(range(66),key=lambda i:abs(x[i]-native[i])),
                               native_comparison=metrics,passed=passed))
    return dict(schema="rf-d/circuit66-vca-release-probes/v1",passed=failures==0,
                failed_probes=failures,input_sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),
                method="independent full FD KCL; 10 pA plus 10 nV correction; shared incoming native histories",
                gates=GATES,maxima=maxima,probes=probes,audio_fidelity_claim=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=INPUT)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args = parser.parse_args()
    INPUT, OUTPUT = args.input, args.output
    report = generate_vectors()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(passed=report["passed"],probes=len(report["probes"]),
                         failed_probes=report["failed_probes"],maxima=report["maxima"]),indent=2))
    if not report["passed"]:
        raise SystemExit(1)
