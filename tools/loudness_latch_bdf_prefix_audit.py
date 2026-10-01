"""Compare same-method refinement before switching; no claim of exact solution."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack as pack_history,unpack as unpack_history,publication_check
from loudness_latch_bdf_survey import trace as bdf_trace,state_hash
from loudness_latch_increment_survey import trace as be_trace
from loudness_latch_transition_observations import sampled_crossings

ROOT=Path(__file__).resolve().parents[1]
BE=ROOT/"evidence/loudness_latch_increment_survey.json.gz"
BDF=ROOT/"evidence/loudness_latch_bdf_survey.json.gz"
OUTPUT=ROOT/"evidence/loudness_latch_bdf_prefix_audit.json"
PREFIX_END_S=.0023
TIMES_S=(.0001,.001,.002,.0023)
PREFIX_GATE_V=1e-3


def prefix_comparison(a,b,index,end=PREFIX_END_S):
    ta,va=a;tb,vb=b
    start=max(ta[1],tb[1]);end=min(end,float(ta[-1]),float(tb[-1]))
    times=np.unique(np.concatenate((ta,tb,[end])));times=times[(times>=start)&(times<=end)]
    av=np.column_stack([np.interp(times,ta,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(times,tb,vb[:,k]) for k in range(94)])
    delta=np.abs(av-bv);location=np.unravel_index(np.argmax(delta),delta.shape)
    maximum=float(np.max(delta))
    return dict(start_s=float(start),end_s=end,points=len(times),maximum_node_difference_v=maximum,
        maximum_difference_node=int(location[1]),maximum_difference_time_s=float(times[location[0]]),
        maximum_timing_c2_difference_v=float(np.max(delta[:,index])),
        maximum_difference_gate_v=PREFIX_GATE_V,prefix_passed=end>=PREFIX_END_S and maximum<PREFIX_GATE_V,
        interpolation="linear on accepted intervals; initial source-jump bridges excluded")


def query_sample(network,case,time,index):
    """Unpublished solve to an interior time, preserving both incoming states."""
    old=unpack_history(network,case["initial"])
    for row in case["accepted"]:
        for step in row["steps"]:
            recorded=unpack_history(network,step["history"])
            if recorded.time_s<time:
                old=recorded;continue
            snapshot=state_hash(old)
            if recorded.time_s==time:
                candidate=recorded;diag=step["diagnostics"];method="stored-accepted-endpoint"
            else:
                candidate,diag=network.advance(old,10.,time-old.time_s)
                method="unpublished-partial-BDF2-from-two-accepted-states"
            check=publication_check(network,old,candidate,diag["actual_dt_s"],diag)
            ta,va=bdf_trace(case)
            interpolated=np.array([np.interp(time,ta,va[:,k]) for k in range(94)])
            actual=np.array(candidate.current.joint.node_v)
            if state_hash(old)!=snapshot:raise ValueError("query modified its incoming history")
            return dict(time_s=time,query_method=method,previous_history_sha256=snapshot,
                previous=pack_history(old),candidate=pack_history(candidate),diagnostics=diag,publication=check,
                limiting_node_index=index,interpolated_node_v=float(interpolated[index]),queried_node_v=float(actual[index]),
                max_interpolated_minus_queried_v=float(np.max(np.abs(interpolated-actual))),published=False)
    raise ValueError("query outside saved coverage")


def generate():
    paths=(Path(__file__).resolve(),ROOT/"tools/loudness_latch_bdf_survey.py",
           ROOT/"tools/loudness_latch_transition_observations.py",
           ROOT/"tools/loudness_latch_bdf_reference.py",ROOT/"tools/loudness_latch_bdf_probes.py",BE,BDF)
    before={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    data_be=json.loads(gzip.decompress(BE.read_bytes()));data_bdf=json.loads(gzip.decompress(BDF.read_bytes()))
    n=BdfNetwork(200,model_parameters(1,"finite_transit")).network
    names=("TIMING_C2","SET_BASE","RESET_COLLECTOR","ATTACK_OUT","KEY_RC","TRIGGER_COLLECTOR")
    indices=[66+n.joint.contour.index[n.joint.contour.alias[name]] for name in names]
    datasets=(("backward-euler",data_be,be_trace),("variable-bdf2",data_bdf,bdf_trace))
    groups=[]
    for name,data,trace in datasets:
        a,b=(trace(c) for c in data["cases"]);ta,va=a;tb,vb=b
        prefix=prefix_comparison(a,b,indices[0]);snapshots=[];events=[]
        for t in TIMES_S:
            if t>min(ta[-1],tb[-1]):continue
            snapshots.append(dict(time_s=t,nodes=[dict(node=name,node_index=i,
                a_v=float(np.interp(t,ta,va[:,i])),b_v=float(np.interp(t,tb,vb[:,i])),
                b_minus_a_v=float(np.interp(t,tb,vb[:,i])-np.interp(t,ta,va[:,i]))) for name,i in zip(names,indices)]))
        for node,threshold,direction in (("ATTACK_OUT",4.,"rising"),("RESET_COLLECTOR",.5,"falling")):
            i=indices[names.index(node)]
            ca=sampled_crossings(ta,va,i,threshold,direction);cb=sampled_crossings(tb,vb,i,threshold,direction)
            events.append(dict(node=node,threshold_v=threshold,direction=direction,policy_a=ca,policy_b=cb,
                b_minus_a_time_s=cb[0]["interpolated_time_s"]-ca[0]["interpolated_time_s"] if len(ca)==len(cb)==1 else None))
        groups.append(dict(method=name,prefix=prefix,snapshots=snapshots,events=events,
            complete_both=all(c["complete"] for c in data["cases"]),full_refinement=data["refinement"]))
    limiting=groups[1]["prefix"];time=limiting["maximum_difference_time_s"];index=limiting["maximum_difference_node"]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    queries=[query_sample(network,case,time,index) for case in data_bdf["cases"]]
    a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
    queried=dict(time_s=time,queries=queries,maximum_node_difference_v=float(np.max(np.abs(a-b))),
        limiting_node_index=index,queried_limiting_node_difference_v=float(abs(a[index]-b[index])),
        original_interpolated_maximum_v=limiting["maximum_node_difference_v"],
        original_prefix_gate_retained=True,published_shadow=False,diagnostic_only=True)
    peak=data_bdf["refinement"];peak_time=peak["maximum_difference_time_s"];peak_index=peak["maximum_difference_node"]
    peak_queries=[query_sample(network,case,peak_time,peak_index) for case in data_bdf["cases"]]
    a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in peak_queries]
    peak_queried=dict(time_s=peak_time,queries=peak_queries,maximum_node_difference_v=float(np.max(np.abs(a-b))),
        limiting_node_index=peak_index,queried_limiting_node_difference_v=float(abs(a[peak_index]-b[peak_index])),
        original_interpolated_maximum_v=peak["maximum_node_difference_v"],
        original_full_gate_retained=True,published_shadow=False,diagnostic_only=True)
    ratio=(groups[0]["prefix"]["maximum_timing_c2_difference_v"]/groups[1]["prefix"]["maximum_timing_c2_difference_v"]
           if groups[1]["prefix"]["maximum_timing_c2_difference_v"] else None)
    after={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    if before!=after:raise ValueError("prefix audit inputs changed during measurement")
    return dict(schema="rf-d/bdf-prefix-audit/v1",groups=groups,prefix_end_s=PREFIX_END_S,
        bdf_same_time_query=queried,
        bdf_transition_time_query=peak_queried,
        be_over_bdf_prefix_c2_refinement_difference=ratio,
        source_sha256=before,
        diagnostic_only=True,independent_exact_solution=False,temporal_refinement_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,trajectory_modified=False,
        limitation="method and mesh sensitivity, not error against an exact DAE solution; sampled interpolation and crossing times do not bound continuous behavior")


if __name__=="__main__":
    report=generate();OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(prefix=[g["prefix"] for g in report["groups"]],
        event_differences=[[e["b_minus_a_time_s"] for e in g["events"]] for g in report["groups"]],
        c2_ratio=report["be_over_bdf_prefix_c2_refinement_difference"],
        queried_maximum_v=report["bdf_same_time_query"]["maximum_node_difference_v"],
        queried_transition_maximum_v=report["bdf_transition_time_query"]["maximum_node_difference_v"],
        interpolation_query_differences_v=[q["max_interpolated_minus_queried_v"]
            for q in report["bdf_same_time_query"]["queries"]])))
