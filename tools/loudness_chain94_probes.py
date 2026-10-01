"""Loaded full-contour fold; no alternative branch is selected or integrated."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from loudness_chain94_reference import JointNetwork
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_chain94_fold.json"

def serialize(probe):
    return dict(selected=None,rejected=probe["rejected"],roots=[dict(state=asdict(r["state"]),
        diagnostics=r["diagnostics"],seed_policy=r["seed_policy"]) for r in probe["roots"]])

def generate():
    cases=[]
    for r61 in (200,200000):
        network=JointNetwork(r61)
        state,diag=network.initial_state()
        prefix=[dict(sample=-1,state=asdict(state),diagnostics=diag)]
        rejection=None
        for sample in range(20):
            key=10.0 if sample>=10 else 0.0
            try:next_state,diag=network.step(state,key,.001)
            except ValueError as exc:
                rejection=dict(sample=sample,keyboard_v=key,dt_s=.001,error=str(exc));break
            state=next_state
            prefix.append(dict(sample=sample,keyboard_v=key,state=asdict(state),diagnostics=diag))
        if rejection is None:raise ValueError("no loaded fold found in declared prefix")
        a=network.probe_step_roots(state,key,.001)
        f=network.probe_step_roots(state,key,.001,use_fd=True)
        worst=0.0
        if not a["roots"] or not f["roots"]:raise ValueError("loaded fold has no reproducible candidates")
        for root in a["roots"]:
            worst=max(worst,min(max(abs(u-v) for u,v in zip(root["state"].node_v,fd["state"].node_v)) for fd in f["roots"]))
        cases.append(dict(r61_ohm=r61,prefix=prefix,fold=rejection,analytic=serialize(a),full_fd=serialize(f),
            max_root_reproduction_error_v=worst,root_count=len(a["roots"]),
            numerical_reproduction_passed=worst<1e-6))
        print(json.dumps(dict(r61=r61,fold=rejection["sample"],roots=len(a["roots"]),error_v=worst)),flush=True)
    hashes={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [ROOT/"tools/loudness_chain94_reference.py",ROOT/"tools/loudness_chain94_probes.py",ROOT/"evidence/loudness_contour_graph.json"]}
    return dict(schema="rf-d/loudness-chain94-fold/v1",cases=cases,source_sha256=hashes,
        method="full loaded contour/audio; 94 nodes; 21 fixed capacitor histories; hybrid and full FD Jacobians",
        environment=environment(),physical_switching_admitted=False,audio_admitted=False,selected=None)

if __name__=="__main__":
    report=generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if not all(c["numerical_reproduction_passed"] for c in report["cases"]):raise SystemExit(1)
