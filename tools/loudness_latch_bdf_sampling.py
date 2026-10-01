"""Unpublished same-time observations; sampled diagnostics, never error bounds."""
from bisect import bisect_left
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check,PATHS as PROBE_PATHS
from loudness_latch_bdf_survey import trace,state_hash
from loudness_latch_bdf_prefix_audit import prefix_comparison
from loudness_latch_bdf_refinement import PREVIOUS,OUTPUT as STRICT,PATHS as REFINEMENT_PATHS
from loudness_latch_increment_probes import hashes
from loudness_latch_transition_observations import sampled_crossings
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_sampling.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_sampling_summary.json"
GATE_V=1e-3
MIDPOINT_COUNT=32
FIXED_TIMES_S=tuple(sorted(set([k*25e-6 for k in range(1,121)]
                              +[.0024+k*.5e-6 for k in range(201)])))
PATHS=tuple(dict.fromkeys((*PROBE_PATHS,*REFINEMENT_PATHS,Path(__file__).resolve(),
    ROOT/"tools/loudness_latch_bdf_survey.py",ROOT/"tools/loudness_latch_bdf_prefix_audit.py",
    ROOT/"tools/loudness_latch_bdf_refinement.py",ROOT/"tools/loudness_latch_transition_observations.py",
    PREVIOUS,STRICT)))


class SavedPath:
    def __init__(self,network,case):
        self.network=network;self.case=case
        self.steps=[s for row in case["accepted"] for s in row["steps"]]
        self.times,self.volts=trace(case)

    def previous(self,position):
        return unpack(self.network,self.case["initial"] if position==0 else self.steps[position-1]["history"])

    def query(self,time):
        time=float(time)
        if not np.isfinite(time) or not self.times[1]<=time<=self.times[-1]:
            raise ValueError("observation must exclude the initial source-jump bridge and stay within saved coverage")
        position=bisect_left(self.times,time)-1
        old=self.previous(position);snapshot=state_hash(old)
        step=self.steps[position];endpoint=step["history"]["time_s"]
        try:
            if endpoint==time:
                candidate=unpack(self.network,step["history"])
                diag=step["diagnostics"];method="stored-accepted-endpoint"
            else:
                candidate,diag=self.network.advance(old,10.,time-old.time_s)
                method="unpublished-partial-BDF2-from-two-accepted-states"
            check=publication_check(self.network,old,candidate,diag["actual_dt_s"],diag)
            interpolated=np.array([np.interp(time,self.times,self.volts[:,k]) for k in range(94)])
            actual=np.array(candidate.current.joint.node_v)
            valid=bool(check["max_published_kcl_a"]<1e-11 and check["max_branch_equation_error_v"]<1e-14
                   and check["round_trip_exact"] and candidate.time_s==time)
            result=dict(time_s=time,position=position,previous_history_sha256=snapshot,query_method=method,
                candidate=pack(candidate),diagnostics=diag,publication=check,query_valid=valid,
                interpolation_difference_v=list(map(float,interpolated-actual)),
                max_interpolation_difference_v=float(np.max(np.abs(interpolated-actual))),published=False)
        except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
            result=dict(time_s=time,position=position,previous_history_sha256=snapshot,query_valid=False,
                        error=str(exc),published=False)
        if state_hash(old)!=snapshot:raise ValueError("same-time observation changed its incoming history")
        return result

    def midpoints(self,start,end):
        positions=[k for k in range(1,len(self.steps))
                   if start<=(self.times[k]+self.times[k+1])/2<=end]
        if not positions:return []
        selected={positions[int(k)] for k in np.linspace(0,len(positions)-1,MIDPOINT_COUNT,dtype=int)}
        return [float((self.times[k]+self.times[k+1])/2) for k in sorted(selected)]


def metrics(rows,end):
    selected=[r for r in rows if r["time_s"]<=end]
    valid=[r for r in selected if r["valid_both"]]
    if not valid:return dict(points=len(selected),valid_points=0,passed=False,maximum_difference_gate_v=GATE_V)
    peak=max(valid,key=lambda r:r["maximum_node_difference_v"])
    return dict(points=len(selected),valid_points=len(valid),maximum_node_difference_v=peak["maximum_node_difference_v"],
        maximum_difference_time_s=peak["time_s"],maximum_difference_node=peak["maximum_difference_node"],
        maximum_difference_gate_v=GATE_V,passed=len(valid)==len(selected) and peak["maximum_node_difference_v"]<GATE_V,
        continuous_bound=False)


def generate():
    before=hashes(PATHS)
    original=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
    strict=json.loads(gzip.decompress(STRICT.read_bytes()))
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    cases=[original["cases"][1],strict["case"]];paths=[SavedPath(network,c) for c in cases]
    start=max(p.times[1] for p in paths);end=min(p.times[-1] for p in paths)
    prefix=prefix_comparison(trace(cases[0]),trace(cases[1]),92)
    landmarks=dict(prefix_peak=prefix["maximum_difference_time_s"],
                   full_peak=strict["refinement"]["maximum_difference_time_s"])
    fixed=[t for t in FIXED_TIMES_S if start<=t<=end]
    mids=[p.midpoints(start,end) for p in paths]
    times=sorted(set(fixed+sum(mids,[])+list(landmarks.values())))
    rows=[]
    for number,time in enumerate(times):
        queries=[p.query(time) for p in paths];valid=all(q["query_valid"] for q in queries)
        tags=(["fixed-grid"] if time in fixed else [])
        tags.extend(name for name,t in landmarks.items() if t==time)
        tags.extend("midpoint-"+name for name,ts in zip(("B3","C3"),mids) if time in ts)
        row=dict(time_s=float(time),tags=tags,queries=queries,valid_both=valid)
        if valid:
            a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
            delta=np.abs(a-b);row.update(maximum_node_difference_v=float(np.max(delta)),maximum_difference_node=int(np.argmax(delta)))
        rows.append(row)
        if (number+1)%50==0:print(json.dumps(dict(observations=number+1,total=len(times),time_s=time)),flush=True)
    fd=[]
    for name,time in landmarks.items():
        row=next(r for r in rows if r["time_s"]==time)
        for policy,p,q in zip(("B3","C3"),paths,row["queries"]):
            if not q["query_valid"]:continue
            old=p.previous(q["position"]);snapshot=state_hash(old)
            candidate,diag=network.advance(old,10.,time-old.time_s,use_fd=True)
            stored=unpack(network,q["candidate"])
            difference=float(np.max(np.abs(np.array(candidate.current.joint.node_v)-stored.current.joint.node_v)))
            check=publication_check(network,old,candidate,diag["actual_dt_s"],diag)
            if state_hash(old)!=snapshot:raise ValueError("FD observation modified incoming histories")
            fd.append(dict(landmark=name,policy=policy,time_s=time,previous_history_sha256=snapshot,
                           candidate=pack(candidate),diagnostics=diag,publication=check,
                           max_node_difference_v=difference,voltage_gate_v=1e-8,
                           passed=difference<1e-8 and check["max_published_kcl_a"]<1e-11,published=False))
    events=[]
    for node,index,threshold,direction in (("ATTACK_OUT",67,4.,"rising"),("RESET_COLLECTOR",83,.5,"falling")):
        crossed=[sampled_crossings(p.times,p.volts,index,threshold,direction) for p in paths]
        events.append(dict(node=node,node_index=index,threshold_v=threshold,direction=direction,
            policy_B3=crossed[0],policy_C3=crossed[1],
            c_minus_b_time_s=crossed[1][0]["interpolated_time_s"]-crossed[0][0]["interpolated_time_s"]
            if len(crossed[0])==len(crossed[1])==1 else None))
    if hashes(PATHS)!=before:raise ValueError("sampling audit inputs changed during execution")
    interpolation=[]
    for i,name in enumerate(("B3","C3")):
        available=[r for r in rows if r["queries"][i]["query_valid"]]
        peak=max(available,key=lambda r:r["queries"][i]["max_interpolation_difference_v"])
        interpolation.append(dict(policy=name,maximum_difference_v=peak["queries"][i]["max_interpolation_difference_v"],
                                  time_s=peak["time_s"],queried_points=len(available)))
    return dict(schema="rf-d/bdf-sampled-observations/v1",source_sha256=before,environment=environment(),
        start_s=float(start),end_s=float(end),fixed_grid_times_s=fixed,midpoint_times_s=mids,
        midpoint_count_per_policy=MIDPOINT_COUNT,landmarks=landmarks,rows=rows,fd_landmarks=fd,
        original_full_comparison=strict["refinement"],original_prefix_comparison=prefix,
        sampled_full_comparison=metrics(rows,end),sampled_prefix_comparison=metrics(rows,.0023),
        interpolation_observations=interpolation,event_observations=events,
        diagnostic_only=True,previous_reports_modified=False,trajectory_modified=False,
        temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="finite sampling and provisional partial steps; no local BE-BDF acceptance test on observations, no bound between queries or exact independent DAE solution")


def save(report):
    canonical=json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    encoded=gzip.compress(canonical,compresslevel=9,mtime=0)
    if json.dumps(json.loads(gzip.decompress(encoded)),sort_keys=True,separators=(",",":"),allow_nan=False).encode()!=canonical:
        raise ValueError("lossless sampled observation storage failed")
    OUTPUT.write_bytes(encoded)
    summary={k:v for k,v in report.items() if k not in ("rows","fd_landmarks","fixed_grid_times_s","midpoint_times_s")}
    summary.update(path=str(OUTPUT.relative_to(ROOT)).replace("\\","/"),
        compressed_sha256=hashlib.sha256(encoded).hexdigest(),canonical_json_sha256=hashlib.sha256(canonical).hexdigest(),
        observation_times=len(report["rows"]),queries=2*len(report["rows"]),
        invalid_queries=sum(not q["query_valid"] for r in report["rows"] for q in r["queries"]),
        fd_landmarks=[{k:v for k,v in r.items() if k not in ("candidate","diagnostics")} for r in report["fd_landmarks"]])
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":print(json.dumps(save(generate())),flush=True)
