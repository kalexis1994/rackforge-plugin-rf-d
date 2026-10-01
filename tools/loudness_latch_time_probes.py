"""Own-path adaptive survey from joint DC; independent trajectory still pending."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np
from loudness_latch_charge_reference import ChargedNetwork,State
from loudness_chain94_reference import State as JointState
from loudness_contour_reference import State as ContourState
from bjt_charge_reference import History as DeviceHistory
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_charge_reference import History
from loudness_latch_time_reference import Policy,trial,frozen_rate
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_time_probes.json"
END_S=.003
POLICIES=(Policy(1e-4,1e-4,1e-18,1e-3,.05,.1,1e-4,1e-12,2000),
          Policy(2.5e-5,2.5e-5,2.5e-19,2.5e-4,.025,.05,1e-4,1e-12,2000))
SOURCE_PATHS=tuple(ROOT/p for p in (
    "tools/loudness_latch_time_reference.py","tools/loudness_latch_time_probes.py",
    "tools/loudness_latch_charge_reference.py","tools/loudness_chain94_reference.py",
    "tools/loudness_descriptor_stability.py","tools/bjt_charge_reference.py",
    "tools/bjt_charge_ngspice_probes.py","tools/junction_charge_reference.py",
    "evidence/loudness_contour_graph.json"))


def source_hashes():
    return {str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE_PATHS}


def pack(state):
    return dict(node_v=state.joint.node_v,audio_capacitor_v=state.joint.audio_capacitor_v,
                c10_v=state.joint.c10_v,contour_capacitor_v=state.joint.contour.capacitor_v,
                oriented_charge_c=[[d.be_c,d.bc_c] for d in state.latch.devices])


def unpack(network,record,key):
    contour=network.joint.contour
    values=dict(contour.rails,KEYBOARD_TRIGGER=key)
    values.update(zip(contour.nodes,record["node_v"][66:]))
    values.update({name:values[alias] for name,alias in contour.alias.items()})
    joint=JointState(tuple(record["node_v"]),tuple(record["audio_capacitor_v"]),record["c10_v"],
                     ContourState(values,dict(record["contour_capacitor_v"])))
    p=network.latch.device.parameters
    history=History(network.latch.layout,tuple(DeviceHistory(p,*q) for q in record["oriented_charge_c"]))
    return State(joint,history)


def state_hash(state):
    return hashlib.sha256(json.dumps(pack(state),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def run_case(policy,index):
    network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
    state,dc_diag=network.initial_state()
    initial=pack(state)
    rate=frozen_rate(network,state,0.0) # left limit before the source edge
    t=0.0;h=policy.maximum_step_s
    accepted=[];rejected=[];stop=None
    for attempt in range(policy.maximum_attempts):
        if t>=END_S:break
        h=min(h,END_S-t)
        old=state
        try:
            result,diag,next_rate=trial(network,old,10.0,h,policy,rate)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            result=None;diag=dict(reason="solve-rejected",error=str(exc))
        if result is None:
            rejected.append(dict(time_s=t,dt_s=h,previous_state_sha256=state_hash(old),diagnostics=diag))
            h/=2
            if h<policy.minimum_step_s:
                stop=dict(reason="minimum-step-budget",time_s=t,next_dt_s=h);break
            continue
        half,fine=result
        accepted.append(dict(start_s=t,dt_s=h,half=pack(half),fine=pack(fine),diagnostics=diag))
        state=fine;rate=next_rate;t+=h
        if len(accepted)%100==0:
            print(json.dumps(dict(policy=index,time_s=t,dt_s=h,accepted=len(accepted),rejected=len(rejected),
                                  q25_collector_v=state.joint.contour.node_v["RESET_COLLECTOR"])),flush=True)
        if (max(diag["voltage_error_ratio"],diag["charge_error_ratio"])<.25
                and diag["junction_increment_v"]<policy.junction_increment_v/2
                and diag["positive_mode_step_product"]<policy.positive_mode_step_product/2):
            h=min(2*h,policy.maximum_step_s)
    if t<END_S and stop is None:stop=dict(reason="attempt-budget",time_s=t)
    report=dict(policy=asdict(policy),r61_ohm=200,profile="finite_transit",initial=initial,dc_diagnostics=dc_diag,
                accepted=accepted,rejected=rejected,accepted_macro_steps=len(accepted),
                accepted_backward_euler_steps=2*len(accepted),attempts=len(accepted)+len(rejected),
                final_time_s=t,final=pack(state),stop=stop,history_reset_count=0,selected_alternative=None,
                complete=t>=END_S)
    print(json.dumps(dict(policy=index,complete=report["complete"],accepted=len(accepted),rejected=len(rejected),stop=stop)),flush=True)
    return report


def trace(case):
    rows=[(0.0,case["initial"]["node_v"])]
    for r in case["accepted"]:
        rows.extend(((r["start_s"]+r["dt_s"]/2,r["half"]["node_v"]),(r["start_s"]+r["dt_s"],r["fine"]["node_v"])))
    times=np.array([r[0] for r in rows]);values=np.array([r[1] for r in rows])
    return times,values


def generate():
    hashes=source_hashes()
    cases=[run_case(p,i) for i,p in enumerate(POLICIES)]
    ta,va=trace(cases[0]);tb,vb=trace(cases[1])
    common=np.unique(np.concatenate((ta,tb)))
    common=common[common<=min(ta[-1],tb[-1])]
    a=np.column_stack([np.interp(common,ta,va[:,k]) for k in range(94)])
    b=np.column_stack([np.interp(common,tb,vb[:,k]) for k in range(94)])
    # The algebraic source diode jumps at t=0; comparing its linear bridges
    # would manufacture a discrepancy unrelated to accepted time points.
    start=max(ta[1],tb[1]) if len(ta)>1 and len(tb)>1 else None
    valid=common>=start if start is not None else np.zeros(len(common),dtype=bool)
    error=np.abs(a[valid]-b[valid])
    location=np.unravel_index(np.argmax(error),error.shape) if error.size else None
    if source_hashes()!=hashes:
        raise ValueError("survey inputs changed during execution; regenerate from one source revision")
    return dict(schema="rf-d/loudness-latch-time/v1",cases=cases,end_s=END_S,key_before_v=0.0,key_after_v=10.0,
        environment=environment(),source_sha256=hashes,
        method="joint DC; unpublished one-step/two-half-step comparison; publish fine half intervals only; endpoint frozen growing-mode guard",
        refinement=dict(common_end_s=float(common[-1]),comparison_start_s=float(start),
            comparison_points=int(np.sum(valid)),max_node_difference_v=float(np.max(error)) if error.size else None,
            max_difference_time_s=float(common[valid][location[0]]) if location is not None else None,
            max_difference_node=int(location[1]) if location is not None else None,
            interpolation="linear on both complete adaptive accepted traces; initial source-jump bridges excluded"),
        independent_trajectory_oracle=False,temporal_error_bound_admitted=False,physical_charge_identified=False,
        physical_switching_admitted=False,audio_admitted=False,selected=None,
        limitation="step-doubling and endpoint frozen modes are conditional diagnostics, not an inter-sample error or physical stability proof; omitted device charges remain")


def quality(report):
    if len(report["cases"])!=2:return False
    for case,p in zip(report["cases"],POLICIES):
        if case["policy"]!=asdict(p) or not case["accepted"]:return False
        if case["dc_diagnostics"]["max_kcl_a"]>=1e-11 or case["dc_diagnostics"]["correction_v"]>=1e-8:return False
        for row in case["accepted"]:
            d=row["diagnostics"]
            if (max(d["voltage_error_ratio"],d["charge_error_ratio"])>1
                    or d["junction_increment_v"]>p.junction_increment_v
                    or d["positive_mode_step_product"]>p.positive_mode_step_product):return False
            if any(d[k]["max_kcl_a"]>=1e-11 or d[k]["correction_v"]>=1e-8 for k in ("full","half","fine")):return False
    return True


if __name__=="__main__":
    report=generate()
    report["accepted_step_quality_passed"]=quality(report)
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report["refinement"]))
    raise SystemExit(0 if quality(report) else 1)
