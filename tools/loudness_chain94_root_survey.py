"""Diagnostic seed coverage between the loaded fold roots; never select a branch."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np
from loudness_chain94_reference import JointNetwork,State
from loudness_contour_reference import State as ContourState
from loudness_descriptor_stability import joint_static,reduced_modes,diagnostic_latch_caps
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_chain94_root_survey.json"

def generate():
    fold=json.loads((ROOT/"evidence/loudness_chain94_fold.json").read_text())
    cases=[]
    for case in fold["cases"]:
        network=JointNetwork(case["r61_ohm"])
        p=case["prefix"][-1]["state"]
        old=State(tuple(p["node_v"]),tuple(p["audio_capacitor_v"]),p["c10_v"],ContourState(**p["contour"]))
        known=[np.array(r["state"]["node_v"]) for r in case["analytic"]["roots"]]
        roots=[];trials=[]
        for numerator in range(17):
            alpha=numerator/16
            for shift in (-.001,0.0,.001):
                seed=(1-alpha)*known[0]+alpha*known[1]
                for terminal in ("SET_BASE","RESET_BASE"):
                    seed[66+network.contour.index[network.contour.alias[terminal]]]+=shift
                try:
                    state,diag=network.solve(seed,10.0,old,.001)
                    index=next((i for i,r in enumerate(roots) if max(abs(a-b) for a,b in zip(state.node_v,r["state"].node_v))<1e-6),None)
                    if index is None:
                        index=len(roots)
                        fd,fd_diag=network.solve(seed,10.0,old,.001,use_fd=True)
                        error=max(abs(a-b) for a,b in zip(state.node_v,fd.node_v))
                        g,caps=joint_static(network,state.node_v,10.0)
                        slow=reduced_modes(g,caps,.001)
                        fast=reduced_modes(g,caps+diagnostic_latch_caps(network.contour,66,10e-12,5e-12),.001)
                        roots.append(dict(state=state,diagnostics=diag,full_fd_error_v=error,full_fd_diagnostics=fd_diag,
                            slow_modes=slow,diagnostic_fast_modes=fast))
                    trials.append(dict(alpha=alpha,base_shift_v=shift,root_index=index,diagnostics=diag))
                except (ValueError,np.linalg.LinAlgError) as exc:
                    trials.append(dict(alpha=alpha,base_shift_v=shift,error=str(exc),root_index=None))
        cases.append(dict(r61_ohm=case["r61_ohm"],trials=trials,roots=[dict(r,state=asdict(r["state"])) for r in roots],
            selected=None,enumeration_exhaustive=False))
        print(json.dumps(dict(r61=case["r61_ohm"],trials=len(trials),roots=len(roots),
            rejected=sum(t["root_index"] is None for t in trials))),flush=True)
    paths=[ROOT/"tools/loudness_chain94_root_survey.py",ROOT/"evidence/loudness_chain94_fold.json"]
    return dict(schema="rf-d/loudness-chain94-root-survey/v1",cases=cases,selected=None,
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        seed_scope="17 interpolations between the two known roots; three 0/+-1mV latch-base shifts; same 21 incoming histories",
        environment=environment(),physical_switching_admitted=False,audio_admitted=False,enumeration_exhaustive=False)

if __name__=="__main__":
    report=generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if not all(r["full_fd_error_v"]<1e-6 for c in report["cases"] for r in c["roots"]):raise SystemExit(1)
