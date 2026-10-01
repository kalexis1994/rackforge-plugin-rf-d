"""Own-path adaptive v2 survey; retains every rejection and compensated state."""
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_increment_reference import IncrementNetwork
from loudness_latch_increment_time import Policy,trial
from loudness_latch_increment_probes import pack,hashes,state_hash,publication_check,SOURCE_PATHS
from loudness_latch_time_reference import frozen_rate
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_increment_survey.json"
END_S=.003
POLICIES=(Policy(1e-4,1e-4,1e-4,1e-4,.05,.1,1e-4,1e-12,2000),
          Policy(2.5e-5,2.5e-5,2.5e-5,2.5e-5,.025,.05,1e-4,1e-12,2000))
REFINEMENT_GATE_V=1e-3 # Declared before measurement; all 94 node potentials.
PATHS=(*SOURCE_PATHS,Path(__file__).resolve())


def run_case(policy,index):
    network=IncrementNetwork(200,model_parameters(1,"finite_transit"))
    state,dc=network.initial_state();initial=pack(state)
    rate=frozen_rate(network,state,0.)
    time=0.;h=policy.maximum_step_s;accepted=[];rejected=[];stop=None
    for attempt in range(policy.maximum_attempts):
        if time>=END_S:break
        h=min(h,END_S-time);old=state
        try:
            result,diag,next_rate=trial(network,old,10.,h,policy,rate)
            if result is not None:
                half,fine=result
                publications=(publication_check(network,old,half,10.,h/2,diag["half"]),
                              publication_check(network,half,fine,10.,h/2,diag["fine"]))
                if any(not p["round_trip_exact"] or p["max_published_kcl_a"]>=1e-11
                       or p["max_serialized_replay_kcl_a"]>=1e-11 for p in publications):
                    result=None;diag=dict(diag,reason="publication-rejected",publication=publications)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            result=None;diag=dict(reason="solve-rejected",error=str(exc))
        if result is None:
            rejected.append(dict(time_s=time,dt_s=h,previous_state_sha256=state_hash(old),diagnostics=diag))
            h/=2
            if h<policy.minimum_step_s:
                stop=dict(reason="minimum-step-budget",time_s=time,next_dt_s=h);break
            continue
        half,fine=result
        accepted.append(dict(start_s=time,dt_s=h,half=pack(half),fine=pack(fine),diagnostics=diag,
                             publication=publications))
        state=fine;time+=h;rate=next_rate
        if len(accepted)%100==0:
            print(json.dumps(dict(policy=index,time_s=time,accepted=len(accepted),rejected=len(rejected),dt_s=h)),flush=True)
        if (max(diag["voltage_error_ratio"],diag["junction_voltage_error_ratio"])<.25
                and diag["junction_increment_v"]<policy.junction_increment_v/2
                and diag["positive_mode_step_product"]<policy.positive_mode_step_product/2):
            h=min(2*h,policy.maximum_step_s)
    if time<END_S and stop is None:stop=dict(reason="attempt-budget",time_s=time)
    case=dict(policy=asdict(policy),r61_ohm=200,profile="finite_transit",initial=initial,dc_diagnostics=dc,
        accepted=accepted,rejected=rejected,final_time_s=time,final=pack(state),complete=time>=END_S,stop=stop,
        accepted_macro_steps=len(accepted),accepted_backward_euler_steps=2*len(accepted),
        attempts=len(accepted)+len(rejected),history_reset_count=0,selected_alternative=None)
    print(json.dumps(dict(policy=index,complete=case["complete"],accepted=len(accepted),rejected=len(rejected),stop=stop)),flush=True)
    return case


def trace(case):
    rows=[(0.,case["initial"]["legacy"]["node_v"])]
    for row in case["accepted"]:
        rows.extend(((row["start_s"]+row["dt_s"]/2,row["half"]["legacy"]["node_v"]),
                     (row["start_s"]+row["dt_s"],row["fine"]["legacy"]["node_v"])))
    return np.array([r[0] for r in rows]),np.array([r[1] for r in rows])


def compare(cases):
    ta,va=trace(cases[0]);tb,vb=trace(cases[1])
    if min(len(ta),len(tb))<2:
        return dict(passed=False,reason="empty-trajectory",maximum_difference_gate_v=REFINEMENT_GATE_V)
    start=max(ta[1],tb[1]);end=min(ta[-1],tb[-1])
    times=np.unique(np.concatenate((ta,tb)));times=times[(times>=start)&(times<=end)]
    a=np.column_stack([np.interp(times,ta,va[:,k]) for k in range(94)])
    b=np.column_stack([np.interp(times,tb,vb[:,k]) for k in range(94)])
    delta=np.abs(a-b);loc=np.unravel_index(np.argmax(delta),delta.shape)
    maximum=float(np.max(delta))
    return dict(comparison_start_s=float(start),common_end_s=float(end),comparison_points=len(times),
        maximum_node_difference_v=maximum,max_difference_time_s=float(times[loc[0]]),max_difference_node=int(loc[1]),
        final_node_difference_v=float(np.max(np.abs(va[-1]-vb[-1]))) if all(c["complete"] for c in cases) else None,
        maximum_difference_gate_v=REFINEMENT_GATE_V,passed=all(c["complete"] for c in cases) and maximum<REFINEMENT_GATE_V,
        interpolation="linear on accepted half intervals; initial source-jump bridges excluded; rounded node potentials")


def generate():
    before=hashes(PATHS);cases=[run_case(p,k) for k,p in enumerate(POLICIES)]
    refinement=compare(cases)
    if hashes(PATHS)!=before:raise ValueError("survey sources changed during execution")
    return dict(schema="rf-d/latch-increment-survey/v2",source_sha256=before,environment=environment(),
        end_s=END_S,key_before_v=0.,key_after_v=10.,cases=cases,refinement=refinement,
        coordinate_version="increment-pair/v1",error_metric_version="node-and-junction-voltage/v2",
        original_v1_modified=False,independent_trajectory_oracle=False,
        temporal_refinement_admitted=refinement["passed"],temporal_error_bound_admitted=False,
        physical_charge_identified=False,physical_switching_admitted=False,audio_admitted=False,selected=None,
        limitation="own-path step doubling and frozen endpoint modes; static laws and nonlinear charges use rounded nodes; omitted semiconductor charges remain")


if __name__=="__main__":
    report=generate();OUTPUT.write_text(json.dumps(report,indent=1)+"\n",encoding="utf-8")
    print(json.dumps(report["refinement"]),flush=True)
