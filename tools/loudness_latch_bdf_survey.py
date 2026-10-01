"""Own-path BE/BDF2 temporal comparison with direct publication verification."""
from dataclasses import asdict
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,publication_check,PATHS as PROBE_PATHS
from loudness_latch_bdf_time import trial
from loudness_latch_increment_time import Policy
from loudness_latch_increment_probes import hashes
from loudness_latch_time_reference import frozen_rate
from loudness_latch_increment_survey import trace as be_trace
from loudness_latch_transition_observations import sampled_crossings
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_survey.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_survey_summary.json"
BE=ROOT/"evidence/loudness_latch_increment_survey.json.gz"
END_S=.003
POLICIES=(Policy(1e-4,1e-4,1e-4,1e-4,.05,.1,1e-4,1e-12,3000),
          Policy(2.5e-5,2.5e-5,2.5e-5,2.5e-5,.025,.05,1e-4,1e-12,3000))
GATE_V=1e-3
PATHS=tuple(dict.fromkeys((*PROBE_PATHS,Path(__file__).resolve(),
    ROOT/"tools/loudness_latch_bdf_time.py",ROOT/"tools/loudness_latch_increment_survey.py",
    ROOT/"tools/loudness_latch_transition_observations.py",BE)))


def state_hash(history):
    return hashlib.sha256(json.dumps(pack(history),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def run_case(policy,index):
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));history,dc=network.initial_history()
    initial=pack(history);rate=frozen_rate(network.network,history.current,0.)
    h=policy.maximum_step_s;accepted=[];rejected=[];stop=None
    for attempt in range(policy.maximum_attempts):
        if history.time_s>=END_S:break
        h=min(h,END_S-history.time_s)
        if history.previous is not None:h=min(h,2*history.previous_dt_s)
        old=history
        try:
            result,diag,next_rate=trial(network,old,10.,h,policy,rate)
            if result is not None:
                publications=[];previous=old
                for candidate,d in result:
                    check=publication_check(network,previous,candidate,d["actual_dt_s"],d)
                    publications.append(check);previous=candidate
                if any(not c["round_trip_exact"] or c["max_published_kcl_a"]>=1e-11
                       or c["max_branch_equation_error_v"]>=1e-14 for c in publications):
                    result=None;diag=dict(diag,reason="publication-rejected",publication=publications)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            result=None;diag=dict(reason="solve-rejected",error=str(exc))
        if result is None:
            rejected.append(dict(time_s=old.time_s,dt_s=h,previous_history_sha256=state_hash(old),diagnostics=diag))
            h/=2
            if h<policy.minimum_step_s:
                stop=dict(reason="minimum-step-budget",time_s=old.time_s,next_dt_s=h);break
            continue
        steps=[dict(history=pack(candidate),diagnostics=d,publication=p)
               for (candidate,d),p in zip(result,publications)]
        accepted.append(dict(start_s=old.time_s,dt_s=h,previous_history_sha256=state_hash(old),
                             steps=steps,diagnostics=diag))
        history=result[-1][0];rate=next_rate
        if len(accepted)%100==0:
            print(json.dumps(dict(policy=index,time_s=history.time_s,accepted=len(accepted),rejected=len(rejected),dt_s=h)),flush=True)
        if (max(diag["voltage_error_ratio"],diag["junction_voltage_error_ratio"])<.25
                and diag["junction_increment_v"]<policy.junction_increment_v/2
                and diag["positive_mode_step_product"]<policy.positive_mode_step_product/2):
            h=min(2*h,policy.maximum_step_s,2*history.previous_dt_s)
    if history.time_s<END_S and stop is None:stop=dict(reason="attempt-budget",time_s=history.time_s)
    case=dict(policy=asdict(policy),initial=initial,dc_diagnostics=dc,accepted=accepted,rejected=rejected,
        accepted_trials=len(accepted),published_intervals=sum(len(r["steps"]) for r in accepted),
        final=pack(history),final_time_s=history.time_s,complete=history.time_s>=END_S,stop=stop,
        attempts=len(accepted)+len(rejected),history_reset_count=0,selected_alternative=None)
    print(json.dumps(dict(policy=index,complete=case["complete"],accepted=len(accepted),rejected=len(rejected),stop=stop)),flush=True)
    return case


def trace(case):
    rows=[(0.,case["initial"]["current"]["legacy"]["node_v"])]
    for row in case["accepted"]:
        rows.extend((s["history"]["time_s"],s["history"]["current"]["legacy"]["node_v"]) for s in row["steps"])
    return np.array([r[0] for r in rows]),np.array([r[1] for r in rows])


def comparison(a,b,complete):
    ta,va=a;tb,vb=b
    if min(len(ta),len(tb))<2:return dict(passed=False,reason="empty-trajectory",maximum_difference_gate_v=GATE_V)
    start=max(ta[1],tb[1]);end=min(ta[-1],tb[-1])
    times=np.unique(np.concatenate((ta,tb)));times=times[(times>=start)&(times<=end)]
    av=np.column_stack([np.interp(times,ta,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(times,tb,vb[:,k]) for k in range(94)])
    delta=np.abs(av-bv);location=np.unravel_index(np.argmax(delta),delta.shape);maximum=float(np.max(delta))
    return dict(comparison_start_s=float(start),common_end_s=float(end),comparison_points=len(times),
        maximum_node_difference_v=maximum,maximum_difference_time_s=float(times[location[0]]),
        maximum_difference_node=int(location[1]),maximum_difference_gate_v=GATE_V,
        final_node_difference_v=float(np.max(np.abs(va[-1]-vb[-1]))) if complete else None,
        passed=complete and maximum<GATE_V,interpolation="linear on accepted intervals; initial source-jump bridges excluded")


def observations(network,be,bdf):
    n=network.network;names=("TIMING_C2","SET_BASE","RESET_COLLECTOR","ATTACK_OUT")
    indices=[66+n.joint.contour.index[n.joint.contour.alias[name]] for name in names]
    timestamps=(.0001,.001,.002,.0023)
    prefixes=[];events=[]
    for policy,((ta,va),(tb,vb)) in enumerate(zip(be,bdf)):
        prefixes.extend(dict(policy=policy,time_s=t,node=name,be_v=float(np.interp(t,ta,va[:,i])),
            bdf_v=float(np.interp(t,tb,vb[:,i])),bdf_minus_be_v=float(np.interp(t,tb,vb[:,i])-np.interp(t,ta,va[:,i])))
            for t in timestamps if t<=min(ta[-1],tb[-1]) for name,i in zip(names,indices))
        for name,threshold,direction in (("ATTACK_OUT",4.,"rising"),("RESET_COLLECTOR",.5,"falling")):
            index=indices[names.index(name)]
            a=sampled_crossings(ta,va,index,threshold,direction);b=sampled_crossings(tb,vb,index,threshold,direction)
            events.append(dict(policy=policy,node=name,threshold_v=threshold,direction=direction,be=a,bdf=b,
                bdf_minus_be_time_s=b[0]["interpolated_time_s"]-a[0]["interpolated_time_s"] if len(a)==len(b)==1 else None))
    return dict(prefix_voltages=prefixes,event_crossings=events,diagnostic_only=True,trajectory_retimed=False)


def generate():
    before=hashes(PATHS);cases=[run_case(p,i) for i,p in enumerate(POLICIES)]
    be=json.loads(gzip.decompress(BE.read_bytes()))
    bt=[trace(c) for c in cases];et=[be_trace(c) for c in be["cases"]]
    refinement=comparison(*bt,all(c["complete"] for c in cases))
    cross=[comparison(a,b,bc["complete"] and ec["complete"]) for a,b,bc,ec in zip(bt,et,cases,be["cases"])]
    observed=observations(BdfNetwork(200,model_parameters(1,"finite_transit")),et,bt)
    if hashes(PATHS)!=before:raise ValueError("BDF survey inputs changed during execution")
    return dict(schema="rf-d/bdf-path-survey/v1",source_sha256=before,environment=environment(),
        end_s=END_S,r61_ohm=200,profile="finite_transit",key_before_v=0.,key_after_v=10.,cases=cases,
        refinement=refinement,BE_cross_comparisons=cross,observations=observed,previous_euler_reports_modified=False,
        independent_spatial_oracle=False,temporal_refinement_admitted=refinement["passed"],
        temporal_error_bound_admitted=False,physical_charge_identified=False,physical_switching_admitted=False,
        audio_admitted=False,selected=None,
        limitation="shared spatial solver; BE-BDF discrepancy is a local estimator, not a global error bound; frozen endpoint modes; omitted charges remain")


def save(report):
    canonical=json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    encoded=gzip.compress(canonical,compresslevel=9,mtime=0)
    restored=json.loads(gzip.decompress(encoded))
    if json.dumps(restored,sort_keys=True,separators=(",",":"),allow_nan=False).encode()!=canonical:
        raise ValueError("lossless survey storage failed")
    OUTPUT.write_bytes(encoded)
    cases=[]
    for c in report["cases"]:
        steps=[s for a in c["accepted"] for s in a["steps"]]
        cases.append(dict(policy=c["policy"],complete=c["complete"],stop=c["stop"],final_time_s=c["final_time_s"],
            accepted_trials=c["accepted_trials"],published_intervals=c["published_intervals"],
            rejected_trials=len(c["rejected"]),rejection_reasons=dict(Counter(r["diagnostics"]["reason"] for r in c["rejected"])),
            minimum_interval_s=min((s["diagnostics"]["actual_dt_s"] for s in steps),default=None),
            max_published_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in steps),default=None)))
    summary=dict(schema="rf-d/bdf-survey-summary/v1",path=str(OUTPUT.relative_to(ROOT)).replace("\\","/"),
        compressed_sha256=hashlib.sha256(encoded).hexdigest(),canonical_json_sha256=hashlib.sha256(canonical).hexdigest(),
        source_sha256=report["source_sha256"],environment=report["environment"],cases=cases,
        refinement=report["refinement"],BE_cross_comparisons=report["BE_cross_comparisons"],observations=report["observations"],
        physical_switching_admitted=False,audio_admitted=False,independent_spatial_oracle=False)
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    summary=save(generate());print(json.dumps(dict(refinement=summary["refinement"],cases=summary["cases"])),flush=True)
