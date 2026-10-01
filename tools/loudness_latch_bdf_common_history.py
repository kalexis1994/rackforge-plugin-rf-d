"""Conditional B3/C3 continuation from the exact same two accepted states."""
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_time import trial
from loudness_latch_bdf_survey import POLICIES,state_hash,trace as dc_trace
from loudness_latch_bdf_observation_domain import DomainPath,PATHS as DOMAIN_PATHS
from loudness_latch_bdf_refinement import PREVIOUS,OUTPUT as STRICT
from loudness_latch_increment_probes import hashes
from loudness_latch_time_reference import frozen_rate
from loudness_latch_transition_observations import sampled_crossings
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_common_history.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_common_history_summary.json"
ANCHOR_LIMIT_S=.0023
END_S=.003
GATE_V=1e-3
POLICY=POLICIES[1]
PATHS=tuple(dict.fromkeys((*DOMAIN_PATHS,Path(__file__).resolve())))


def reference_case(strict,index):
    source=strict["case"];initial=source["accepted"][index]["steps"][-1]["history"]
    rows=source["accepted"][index+1:]
    rejected=[r for r in source["rejected"] if r["time_s"]>=initial["time_s"]]
    return dict(initial=initial,policy=source["policy"],accepted=rows,rejected=rejected,
        accepted_trials=len(rows),published_intervals=sum(len(r["steps"]) for r in rows),
        final=source["final"],final_time_s=source["final_time_s"],complete=source["complete"],stop=source["stop"],
        attempts=len(rows)+len(rejected),history_reset_count=0,selected_alternative=None,
        inherited=True,source_accepted_anchor_index=index)


def continuation_trace(case):
    rows=[(case["initial"]["time_s"],case["initial"]["current"]["legacy"]["node_v"])]
    rows.extend((s["history"]["time_s"],s["history"]["current"]["legacy"]["node_v"])
                for r in case["accepted"] for s in r["steps"])
    return np.array([r[0] for r in rows]),np.array([r[1] for r in rows])


def compare(a,b,complete,start_s=None):
    ta,va=a;tb,vb=b
    start=max(float(ta[0]),float(tb[0]),float(ta[0]) if start_s is None else start_s)
    end=min(float(ta[-1]),float(tb[-1]))
    times=np.unique(np.concatenate((ta,tb,[start,end])));times=times[(times>=start)&(times<=end)]
    av=np.column_stack([np.interp(times,ta,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(times,tb,vb[:,k]) for k in range(94)])
    delta=np.abs(av-bv);i,k=np.unravel_index(np.argmax(delta),delta.shape)
    maximum=float(np.max(delta))
    return dict(start_s=start,end_s=end,points=len(times),maximum_node_difference_v=maximum,
        maximum_difference_time_s=float(times[i]),maximum_difference_node=int(k),
        final_node_difference_v=float(np.max(delta[-1])),maximum_difference_gate_v=GATE_V,
        passed=complete and maximum<GATE_V,interpolation="linear on original clock; initial common anchor included")


def run_continuation(network,seed,h,policy=POLICY):
    network.validate(seed)
    if seed.previous is None or seed.key_v!=10. or not seed.time_s<END_S:
        raise ValueError("two accepted KEY=10 histories before the requested end required")
    history=seed;initial=pack(seed);seed_hash=state_hash(seed)
    rate=frozen_rate(network.network,history.current,10.)
    accepted=[];rejected=[];stop=None
    for _ in range(policy.maximum_attempts):
        if history.time_s>=END_S:break
        h=min(h,END_S-history.time_s,2*history.previous_dt_s)
        old=history;snapshot=state_hash(old)
        try:
            result,diag,next_rate=trial(network,old,10.,h,policy,rate)
            if result is not None:
                previous=old;publications=[]
                for candidate,d in result:
                    check=publication_check(network,previous,candidate,d["actual_dt_s"],d)
                    publications.append(check);previous=candidate
                if any(not c["round_trip_exact"] or c["max_published_kcl_a"]>=1e-11
                       or c["max_branch_equation_error_v"]>=1e-14 for c in publications):
                    result=None;diag=dict(diag,reason="publication-rejected",publication=publications)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            result=None;diag=dict(reason="solve-rejected",error=str(exc))
        if state_hash(old)!=snapshot:raise ValueError("continuation modified its incoming double history")
        if result is None:
            rejected.append(dict(time_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,diagnostics=diag))
            h/=2
            if h<policy.minimum_step_s:
                stop=dict(reason="minimum-step-budget",time_s=old.time_s,next_dt_s=h);break
            continue
        accepted.append(dict(start_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,
            steps=[dict(history=pack(candidate),diagnostics=d,publication=p)
                   for (candidate,d),p in zip(result,publications)],diagnostics=diag))
        history=result[-1][0];rate=next_rate
        if len(accepted)%100==0:
            print(json.dumps(dict(policy="B3-from-C3-history",time_s=history.time_s,accepted=len(accepted),
                                  rejected=len(rejected),dt_s=h)),flush=True)
        if (max(diag["voltage_error_ratio"],diag["junction_voltage_error_ratio"])<.25
                and diag["junction_increment_v"]<policy.junction_increment_v/2
                and diag["positive_mode_step_product"]<policy.positive_mode_step_product/2):
            h=min(2*h,policy.maximum_step_s,2*history.previous_dt_s)
    if history.time_s<END_S and stop is None:stop=dict(reason="attempt-budget",time_s=history.time_s)
    if state_hash(seed)!=seed_hash:raise ValueError("continuation changed its accepted common seed")
    return dict(policy=asdict(policy),initial=initial,accepted=accepted,rejected=rejected,
        accepted_trials=len(accepted),published_intervals=sum(len(r["steps"]) for r in accepted),
        final=pack(history),final_time_s=history.time_s,complete=history.time_s>=END_S,stop=stop,
        attempts=len(accepted)+len(rejected),history_reset_count=0,selected_alternative=None,inherited=False)


def inherited_audit(network,case):
    old=unpack(network,case["initial"]);maximum=0.;count=0
    for row in case["accepted"]:
        if row["previous_history_sha256"]!=state_hash(old):raise ValueError("inherited C3 lineage mismatch")
        for s in row["steps"]:
            new=unpack(network,s["history"]);d=s["diagnostics"]
            check=publication_check(network,old,new,d["actual_dt_s"],d)
            if (check!=s["publication"] or not check["round_trip_exact"]
                    or check["max_published_kcl_a"]>=1e-11 or check["max_branch_equation_error_v"]>=1e-14
                    or new.previous!=old.current):raise ValueError("inherited C3 publication or memory mismatch")
            maximum=max(maximum,check["max_published_kcl_a"]);count+=1;old=new
    return dict(inherited_intervals=count,max_published_kcl_a=maximum,initial_history_sha256=state_hash(unpack(network,case["initial"])),
                final_history_sha256=state_hash(old),new_C3_intervals_generated=0)


class ContinuationPath(DomainPath):
    def __init__(self,network,case):
        self.network=network;self.case=case
        self.steps=[s for r in case["accepted"] for s in r["steps"]]
        self.times,self.volts=continuation_trace(case)


def generate():
    before=hashes(PATHS)
    strict=json.loads(gzip.decompress(STRICT.read_bytes()))
    original=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
    rows=strict["case"]["accepted"]
    index=max(i for i,r in enumerate(rows) if r["steps"][-1]["history"]["time_s"]<=ANCHOR_LIMIT_S)
    fine=reference_case(strict,index)
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));seed=unpack(network,fine["initial"])
    h=fine["accepted"][0]["dt_s"]
    audit=inherited_audit(network,fine)
    coarse=run_continuation(network,seed,h)
    bt,ct=continuation_trace(coarse),continuation_trace(fine)
    complete=coarse["complete"] and fine["complete"]
    conditional=compare(bt,ct,complete)
    original_window=compare(dc_trace(original["cases"][1]),ct,complete,start_s=seed.time_s)
    coarse_shift=compare(dc_trace(original["cases"][1]),bt,complete,start_s=seed.time_s)
    paths=[ContinuationPath(network,c) for c in (coarse,fine)]
    queries=[p.query(conditional["maximum_difference_time_s"]) for p in paths]
    valid=all(q["query_valid"] for q in queries)
    same_time=dict(time_s=conditional["maximum_difference_time_s"],queries=queries,valid_both=valid,diagnostic_only=True)
    if valid:
        a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
        delta=np.abs(a-b);same_time.update(maximum_node_difference_v=float(np.max(delta)),maximum_difference_node=int(np.argmax(delta)))
    events=[]
    for name,i,v,direction in (("ATTACK_OUT",67,4.,"rising"),("RESET_COLLECTOR",83,.5,"falling")):
        a=sampled_crossings(*bt,i,v,direction);b=sampled_crossings(*ct,i,v,direction)
        events.append(dict(node=name,node_index=i,threshold_v=v,direction=direction,B3_common=a,C3_common=b,
            c_minus_b_time_s=b[0]["interpolated_time_s"]-a[0]["interpolated_time_s"] if len(a)==len(b)==1 else None))
    if hashes(PATHS)!=before:raise ValueError("common history experiment inputs changed during execution")
    return dict(schema="rf-d/bdf-common-history/v1",source_sha256=before,environment=environment(),
        anchor_limit_s=ANCHOR_LIMIT_S,anchor_time_s=seed.time_s,anchor_C3_accepted_index=index,
        anchor=pack(seed),initial_proposal_s=h,common_history_sha256=state_hash(seed),case=coarse,
        inherited_C3_audit=audit,conditional_comparison=conditional,original_full_comparison=strict["refinement"],
        original_window_comparison=original_window,B3_original_vs_common_history=coarse_shift,
        same_time_conditional_peak=same_time,event_observations=events,
        conditional_refinement_passed=conditional["passed"],diagnostic_only=True,
        previous_reports_modified=False,trajectory_retimed=False,history_reset_count=0,
        temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="common C3 hypothesis fixes two physical/numerical histories and first proposal; inherited C3 suffix, no independent exact solution; differences and their maxima do not add linearly")


def save(report):
    canonical=json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    encoded=gzip.compress(canonical,compresslevel=9,mtime=0)
    if json.dumps(json.loads(gzip.decompress(encoded)),sort_keys=True,separators=(",",":"),allow_nan=False).encode()!=canonical:
        raise ValueError("lossless common history storage failed")
    OUTPUT.write_bytes(encoded)
    c=report["case"];steps=[s for r in c["accepted"] for s in r["steps"]]
    summary={k:v for k,v in report.items() if k not in ("case","anchor","same_time_conditional_peak")}
    summary.update(path=str(OUTPUT.relative_to(ROOT)).replace("\\","/"),
        compressed_sha256=hashlib.sha256(encoded).hexdigest(),canonical_json_sha256=hashlib.sha256(canonical).hexdigest(),
        case=dict(policy=c["policy"],complete=c["complete"],final_time_s=c["final_time_s"],stop=c["stop"],
            accepted_trials=c["accepted_trials"],published_intervals=c["published_intervals"],rejected_trials=len(c["rejected"]),
            rejection_reasons=dict(Counter(r["diagnostics"]["reason"] for r in c["rejected"])),
            max_published_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in steps),default=None)),
        same_time_conditional_peak={k:v for k,v in report["same_time_conditional_peak"].items() if k!="queries"})
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    s=save(generate());print(json.dumps({k:s[k] for k in ("case","conditional_comparison","original_window_comparison","same_time_conditional_peak","event_observations")} ),flush=True)
