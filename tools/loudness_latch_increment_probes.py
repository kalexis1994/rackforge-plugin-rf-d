"""Fixed-history coordinate repair with Decimal publication checks."""
from decimal import Decimal,localcontext
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_increment_reference import IncrementNetwork,IncrementState
from loudness_latch_time_probes import pack as legacy_pack,unpack as legacy_unpack,SOURCE_PATHS as LEGACY_PATHS
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_increment_probes.json"
SOURCE_PATHS=tuple(dict.fromkeys((*LEGACY_PATHS,*(ROOT/p for p in (
    "tools/loudness_latch_increment_reference.py","tools/loudness_latch_increment_time.py",
    "tools/loudness_latch_increment_probes.py","tools/circuit66_vca_release_probes.py",
    "tools/loudness_contour_reference.py","evidence/loudness_latch_rejection_audit.json")))))


def hashes(paths=SOURCE_PATHS):
    return {str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def pack(state):
    return dict(schema="rf-d/compensated-state/v1",legacy=legacy_pack(state),
                node_low_v=state.node_low_v,capacitor_pairs_v=state.capacitor_pairs_v)


def unpack(network,record,key):
    if record["schema"]!="rf-d/compensated-state/v1":raise ValueError("versioned complete state required")
    legacy=legacy_unpack(network,record["legacy"],key)
    state=IncrementState(legacy.joint,legacy.latch,tuple(record["node_low_v"]),
                         tuple(tuple(p) for p in record["capacitor_pairs_v"]),network.signature)
    network.validate(state)
    return state


def state_hash(state):
    return hashlib.sha256(json.dumps(pack(state),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def publication_check(network,old,new,key,h,diag):
    """Check stored charge increments using 80-digit arithmetic on binary inputs.

    Static and nonlinear laws are the unchanged binary64 evaluator. The
    independent arithmetic check here covers linear publication, not physics.
    """
    delta=np.array(diag["increment_v"])
    currents=network.linear(delta,old,h)
    r,_=network.joint.evaluator(key)(new.joint.node_v,False)
    r+=network.latch.evaluate(new.joint.node_v,old.latch,h)["increment_a"]
    checks=[]
    with localcontext() as ctx:
        ctx.prec=80
        D=lambda x:Decimal.from_float(float(x))
        S=lambda p:sum(map(D,p),Decimal(0))
        for k,((left,right,fixed,c,resistance),a,b,current) in enumerate(zip(
                network.branches,old.capacitor_pairs_v,new.capacitor_pairs_v,currents)):
            published_current=(S(b)-S(a))*D(c)/D(h)
            branch=S((new.joint.node_v[left],new.node_low_v[left]))
            branch-=D(fixed) if right is None else S((new.joint.node_v[right],new.node_low_v[right]))
            voltage_error=branch-S(b)-D(resistance)*published_current
            current_error=published_current-D(current)
            checks.append(dict(branch_index=k,capacitance_f=c,series_resistance_ohm=resistance,
                current_a=float(published_current),publication_current_difference_a=float(current_error),
                branch_equation_error_v=float(voltage_error)))
            r[left]+=float(published_current)
            if right is not None:r[right]-=float(published_current)
    # Also reevaluate after serializing and reconstructing the entire state.
    restored=unpack(network,pack(new),key)
    restored_delta=np.array([math.fsum((a,b,-c,-d)) for a,b,c,d in
        zip(restored.joint.node_v,restored.node_low_v,old.joint.node_v,old.node_low_v)])
    rr,_=network.increment_evaluator(key,old,h)(restored_delta,False)
    return dict(branches=checks,max_published_kcl_a=float(np.max(np.abs(r))),
        max_serialized_replay_kcl_a=float(np.max(np.abs(rr))),round_trip_exact=restored==new,
        max_current_difference_a=max(abs(c["publication_current_difference_a"]) for c in checks),
        max_branch_equation_error_v=max(abs(c["branch_equation_error_v"]) for c in checks))


def generate():
    before=hashes()
    source=json.loads((ROOT/"evidence/loudness_latch_rejection_audit.json").read_text())["replay"]
    network=IncrementNetwork(200,model_parameters(1,"finite_transit"))
    old=network.convert(legacy_unpack(network,source["half_state"],10.0))
    snapshot=state_hash(old);h=source["macro_dt_s"]/2
    replays=[]
    for use_fd in (False,True):
        new,diag=network.step(old,10.0,h,use_fd=use_fd)
        delta=np.array(diag["increment_v"])
        ev=network.increment_evaluator(10.0,old,h)
        _,j=ev(delta);_,fd=ev(delta,use_fd=True)
        replays.append(dict(use_fd=use_fd,old=pack(old),new=pack(new),dt_s=h,diagnostics=diag,
            publication=publication_check(network,old,new,10.0,h,diag),
            jacobian_max_scaled_difference=float(np.max(np.abs(j-fd)/(1+np.abs(j)))),
            timing_node_low_v=new.node_low_v[92],timing_capacitor_pair_v=new.capacitor_pairs_v[18]))
    continuation=[];state=unpack(network,replays[0]["new"],10.0)
    for k in range(32):
        previous=state;state,diag=network.step(previous,10.0,h)
        continuation.append(dict(index=k,old=pack(previous),new=pack(state),dt_s=h,diagnostics=diag,
                                 publication=publication_check(network,previous,state,10.0,h,diag)))
    dc,dcdiag=network.initial_state()
    new,diag=network.step(dc,10.0,5e-5)
    legacy,legacydiag=super(IncrementNetwork,network).step(legacy_unpack(network,legacy_pack(dc),0.0),10.0,5e-5)
    ordinary=dict(old=pack(dc),new=pack(new),dt_s=5e-5,diagnostics=diag,
        legacy_diagnostics=legacydiag,max_legacy_node_difference_v=float(np.max(np.abs(
            np.array(new.joint.node_v)-legacy.joint.node_v))),publication=publication_check(network,dc,new,10.0,5e-5,diag))
    if state_hash(old)!=snapshot or hashes()!=before:raise ValueError("input state or sources changed")
    return dict(schema="rf-d/latch-increment-probes/v1",source_sha256=before,environment=environment(),
        repaired_interval=replays,continuation=continuation,ordinary_interval=ordinary,
        fixed_kcl_gate_a=1e-11,fixed_correction_gate_v=1e-8,history_reset_count=0,
        original_rejection_retained=True,static_laws_use_rounded_nodes=True,
        physical_switching_admitted=False,temporal_refinement_admitted=False,audio_admitted=False,selected=None)


if __name__=="__main__":
    report=generate();OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(replay_kcl=[r["diagnostics"]["max_kcl_a"] for r in report["repaired_interval"]],
        publication_kcl=max(r["publication"]["max_published_kcl_a"] for r in report["continuation"]),
        ordinary_node_difference_v=report["ordinary_interval"]["max_legacy_node_difference_v"])))
