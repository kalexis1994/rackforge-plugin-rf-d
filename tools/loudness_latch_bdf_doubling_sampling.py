"""Conserved observations of predeclared v4 DC paths, never retimed."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_survey import trace
from loudness_latch_bdf_observation_domain import DomainPath,PATHS as DOMAIN_PATHS
from loudness_latch_bdf_sampling import FIXED_TIMES_S,MIDPOINT_COUNT,metrics
from loudness_latch_bdf_common_sampling import fd_observation
from loudness_latch_bdf_doubling_survey import OUTPUTS,SUMMARY as SURVEY,NAMES,PATHS as SURVEY_PATHS,store
from loudness_latch_increment_probes import hashes
from loudness_latch_transition_observations import sampled_crossings
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_doubling_sampling.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_doubling_sampling_summary.json"
PATHS=tuple(dict.fromkeys((*DOMAIN_PATHS,*SURVEY_PATHS,Path(__file__).resolve(),*OUTPUTS,SURVEY,
    ROOT/"tools/loudness_latch_bdf_common_sampling.py")))


def node_peaks(a,b):
    ta,va=a;tb,vb=b
    start=max(float(ta[1]),float(tb[1]));end=min(float(ta[-1]),float(tb[-1]))
    times=np.unique(np.concatenate((ta,tb)));times=times[(times>=start)&(times<=end)]
    av=np.column_stack([np.interp(times,ta,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(times,tb,vb[:,k]) for k in range(94)])
    delta=np.abs(av-bv);indices=np.argmax(delta,axis=0)
    return [dict(node_index=k,time_s=float(times[int(indices[k])]),
                 interpolated_difference_v=float(delta[int(indices[k]),k])) for k in range(94)]


def generate():
    before=hashes(PATHS);survey=json.loads(SURVEY.read_text())
    cases=[json.loads(gzip.decompress(p.read_bytes()))["case"] for p in OUTPUTS]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    paths=[DomainPath(network,c) for c in cases]
    peaks=node_peaks(*(trace(c) for c in cases))
    start=max(float(p.times[1]) for p in paths);end=min(float(p.times[-1]) for p in paths)
    fixed=[t for t in FIXED_TIMES_S if start<=t<=end]
    mids=[p.midpoints(start,end) for p in paths]
    landmarks=dict(interpolated_v4_peak=survey["refinement"]["maximum_difference_time_s"])
    times=sorted(set(fixed+sum(mids,[])+[p["time_s"] for p in peaks]+list(landmarks.values())))
    rows=[]
    for number,time in enumerate(times):
        queries=[p.query(time) for p in paths];valid=all(q["query_valid"] for q in queries)
        tags=(["fixed-grid"] if time in fixed else [])
        tags.extend(name for name,t in landmarks.items() if t==time)
        tags.extend("midpoint-"+name for name,ts in zip(NAMES,mids) if time in ts)
        row=dict(time_s=time,tags=tags,node_peak_indices=[p["node_index"] for p in peaks if p["time_s"]==time],
                 queries=queries,valid_both=valid)
        if valid:
            a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
            delta=np.abs(a-b);row.update(maximum_node_difference_v=float(np.max(delta)),maximum_difference_node=int(np.argmax(delta)))
        rows.append(row)
        if (number+1)%100==0:print(json.dumps(dict(observations=number+1,total=len(times))),flush=True)
    sampled=metrics(rows,end);fd=[]
    targets=dict(landmarks,sampled_v4_peak=sampled["maximum_difference_time_s"])
    for name,time in targets.items():
        row=next(r for r in rows if r["time_s"]==time)
        for policy,path,q in zip(NAMES,paths,row["queries"]):
            if q["query_valid"]:fd.append(dict(fd_observation(network,path,q),landmark=name,policy=policy))
    events=[]
    for name,index,threshold,direction in (("ATTACK_OUT",67,4.,"rising"),("RESET_COLLECTOR",83,.5,"falling")):
        crossed=[sampled_crossings(p.times,p.volts,index,threshold,direction) for p in paths]
        events.append(dict(node=name,node_index=index,threshold_v=threshold,direction=direction,
            policy_D4=crossed[0],policy_E4=crossed[1],
            e_minus_d_time_s=crossed[1][0]["interpolated_time_s"]-crossed[0][0]["interpolated_time_s"]
            if len(crossed[0])==len(crossed[1])==1 else None))
    interpolation=[]
    for i,name in enumerate(NAMES):
        available=[r for r in rows if r["queries"][i]["query_valid"]]
        peak=max(available,key=lambda r:r["queries"][i]["max_interpolation_difference_v"])
        interpolation.append(dict(policy=name,maximum_difference_v=peak["queries"][i]["max_interpolation_difference_v"],
                                  time_s=peak["time_s"],queried_points=len(available)))
    if hashes(PATHS)!=before:raise ValueError("v4 observation inputs changed during execution")
    return dict(schema="rf-d/bdf-doubling-sampling/v1",source_sha256=before,environment=environment(),
        start_s=start,end_s=end,node_peaks=peaks,fixed_grid_times_s=fixed,midpoint_times_s=mids,
        midpoint_count_per_policy=MIDPOINT_COUNT,landmarks=landmarks,rows=rows,fd_observations=fd,
        sampled_comparison=sampled,sampled_prefix_comparison=metrics(rows,.0023),events=events,
        interpolation_comparisons=interpolation,original_interpolated_comparison=survey["refinement"],
        diagnostic_only=True,trajectory_retimed=False,previous_reports_modified=False,
        temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="all-node interpolated peaks and predeclared grid are sampled; partial solves preserve charge but provide no continuous maximum bound or independent spatial oracle")


def save(report):
    storage=store(report,OUTPUT)
    queries=[q for row in report["rows"] for q in row["queries"]]
    summary={k:v for k,v in report.items() if k not in ("rows","fd_observations")}
    summary.update(storage=storage,observation_times=len(report["rows"]),queries=len(queries),
        invalid_queries=sum(not q["query_valid"] for q in queries),
        earlier_anchor_queries=sum(q["query_method"]=="unpublished-two-BDF2-steps-from-earlier-accepted-anchor" for q in queries),
        fd_observations=[{k:v for k,v in d.items() if k!="steps"} for d in report["fd_observations"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    s=save(generate());print(json.dumps({k:s[k] for k in ("observation_times","queries","invalid_queries","sampled_comparison","fd_observations")}),flush=True)
