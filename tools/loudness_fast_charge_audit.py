"""Diagnostic charge sweep exposes omitted fast latch modes; no physical fit."""
import hashlib
import json
from pathlib import Path
import numpy as np
from loudness_chain94_reference import JointNetwork
from loudness_descriptor_stability import joint_static,reduced_modes,diagnostic_latch_caps,pole_matching_error
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_fast_charge_audit.json"

def generate():
    fold=json.loads((ROOT/"evidence/loudness_chain94_root_survey.json").read_text())
    cases=[]
    for case in fold["cases"]:
        network=JointNetwork(case["r61_ohm"])
        for root in case["roots"]:
            x=root["state"]["node_v"]
            g,caps=joint_static(network,x,10.0)
            gf,_=joint_static(network,x,10.0,use_fd=True)
            for cbe in (1e-12,10e-12,100e-12):
                for cbc in (2e-12,5e-12,10e-12):
                    augmented=caps+diagnostic_latch_caps(network.contour,66,cbe,cbc)
                    a=reduced_modes(g,augmented,.001)
                    f=reduced_modes(gf,augmented,.001)
                    match=pole_matching_error(a["poles"],f["poles"])
                    growing=[p for p in a["poles"] if p["real_per_s"]>1e-6]
                    cases.append(dict(r61_ohm=case["r61_ohm"],q25_collector_v=root["state"]["contour"]["node_v"]["RESET_COLLECTOR"],
                        diagnostic_cbe_f=cbe,diagnostic_cbc_f=cbc,analytic=a,independent_fd=f,
                        max_relative_pole_matching_error=match,
                        growing_modes_damped_by_1ms_backward_euler=sum(p["implicit_euler_amplification_abs"]<1 for p in growing),
                        selected=None))
    paths=[ROOT/"tools/loudness_fast_charge_audit.py",ROOT/"tools/loudness_descriptor_stability.py",
           ROOT/"evidence/loudness_chain94_root_survey.json"]
    return dict(schema="rf-d/loudness-fast-charge-audit/v1",cases=cases,
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        environment=environment(),diagnostic_only=True,physical_charge_identified=False,physical_switching_admitted=False,audio_admitted=False,selected=None,
        capacitor_scope="four constant diagnostic BE/BC capacitors on Q25/Q15 only; no nonlinear depletion/diffusion/storage law",
        diagnostic_cbe_origin="numerical sensitivity sweep 1/10/100pF, not a component specification",
        diagnostic_cbc_origin="2/5/10pF diagnostic scales; DS-3392-C specifies 2..10pF only at VCB=10V,f=1MHz,25C; not these operating points",
        gates=dict(coordinate_error=1e-12,eigen_residual=1e-9,pole_matching_relative=5e-3))

if __name__=="__main__":
    report=generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    for label,lo,hi in (("lower",0,.1),("middle",.1,2),("upper",2,10)):
        cases=[c for c in report["cases"] if lo<c["q25_collector_v"]<hi]
        print(json.dumps(dict(root=label,cases=len(cases),
            growing_counts=sorted(set(c["analytic"]["growing_modes"] for c in cases)),
            max_real_range=[min(c["analytic"]["max_real_per_s"] for c in cases),max(c["analytic"]["max_real_per_s"] for c in cases)],
            max_matching=max(c["max_relative_pole_matching_error"] for c in cases),
            max_residual=max(c["analytic"]["max_eigen_residual"] for c in cases))))
