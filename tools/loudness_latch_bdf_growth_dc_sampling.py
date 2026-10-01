"""All-node conserved observations for two fixed-tolerance growth contrasts."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_survey import trace
from loudness_latch_bdf_observation_domain import DomainPath
from loudness_latch_bdf_sampling import FIXED_TIMES_S,MIDPOINT_COUNT,metrics
from loudness_latch_bdf_common_sampling import fd_observation
from loudness_latch_bdf_doubling_sampling import node_peaks,PATHS as SAMPLING_PATHS
from loudness_latch_bdf_doubling_survey import OUTPUTS,store
from loudness_latch_bdf_growth_dc import OUTPUT as GROWTH,SUMMARY as SURVEY,PATHS as GROWTH_PATHS,NAME
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_growth_dc_sampling.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_growth_dc_sampling_summary.json"
PATHS=tuple(dict.fromkeys((*SAMPLING_PATHS,*GROWTH_PATHS,Path(__file__).resolve(),GROWTH,SURVEY)))


def observe(network,reference,case,original):
    paths=[DomainPath(network,c) for c in (reference,case)]
    names=(reference["name"],NAME)
    peaks=node_peaks(trace(reference),trace(case))
    start=max(float(p.times[1]) for p in paths);end=min(float(p.times[-1]) for p in paths)
    fixed=[t for t in FIXED_TIMES_S if start<=t<=end]
    mids=[p.midpoints(start,end) for p in paths]
    landmarks=dict(interpolated_peak=original["maximum_difference_time_s"])
    times=sorted(set(fixed+sum(mids,[])+[p["time_s"] for p in peaks]+list(landmarks.values())))
    rows=[]
    for number,time in enumerate(times):
        queries=[p.query(time) for p in paths];valid=all(q["query_valid"] for q in queries)
        row=dict(time_s=time,queries=queries,valid_both=valid,
            node_peak_indices=[p["node_index"] for p in peaks if p["time_s"]==time])
        if valid:
            a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
            delta=np.abs(a-b)
            row.update(maximum_node_difference_v=float(np.max(delta)),maximum_difference_node=int(np.argmax(delta)))
        rows.append(row)
        if (number+1)%100==0:
            print(json.dumps(dict(reference=names[0],observations=number+1,total=len(times))),flush=True)
    sampled=metrics(rows,end);fd=[]
    targets=dict(landmarks)
    if sampled.get("maximum_difference_time_s") is not None:
        targets["sampled_peak"]=sampled["maximum_difference_time_s"]
    for name,time in targets.items():
        row=next(r for r in rows if r["time_s"]==time)
        for policy,path,q in zip(names,paths,row["queries"]):
            if q["query_valid"]:
                fd.append(dict(fd_observation(network,path,q),landmark=name,policy=policy))
    return dict(reference=names[0],policies=names,start_s=start,end_s=end,
        node_peaks=peaks,fixed_grid_times_s=fixed,midpoint_times_s=mids,
        midpoint_count_per_policy=MIDPOINT_COUNT,landmarks=landmarks,rows=rows,fd_observations=fd,
        sampled_comparison=sampled,sampled_prefix_comparison=metrics(rows,.0023),
        original_interpolated_comparison=original,continuous_bound=False)


def generate():
    before=hashes(PATHS);env=environment()
    case=json.loads(gzip.decompress(GROWTH.read_bytes()))["case"]
    survey=json.loads(SURVEY.read_text(encoding="utf-8"))
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));contrasts=[]
    for path,original in zip(OUTPUTS,survey["comparisons"]):
        reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
        contrasts.append(observe(network,reference,case,original))
    if hashes(PATHS)!=before:raise ValueError("growth observation inputs changed during execution")
    return dict(schema="rf-d/bdf-growth-dc-sampling/v1",source_sha256=before,environment=env,
        contrasts=contrasts,diagnostic_only=True,trajectory_retimed=False,previous_reports_modified=False,
        temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        independent_spatial_oracle=False,physical_switching_admitted=False,audio_admitted=False,
        limitation="fixed-tolerance controller sensitivity; sampled all-node peaks, fixed grid and midpoints do not bound a continuous maximum; FD shares the circuit")


def save(report):
    storage=store(report,OUTPUT);contrasts=[]
    for c in report["contrasts"]:
        queries=[q for row in c["rows"] for q in row["queries"]]
        distinct={(d["policy"],d["time_s"]) for d in c["fd_observations"]}
        contrasts.append({k:v for k,v in c.items() if k not in ("rows","fd_observations")}|dict(
            observation_times=len(c["rows"]),queries=len(queries),invalid_queries=sum(not q["query_valid"] for q in queries),
            earlier_anchor_queries=sum(q.get("query_method")=="unpublished-two-BDF2-steps-from-earlier-accepted-anchor" for q in queries),
            fd_distinct_cases=len(distinct),
            fd_observations=[{k:v for k,v in d.items() if k!="steps"} for d in c["fd_observations"]]))
    summary={k:v for k,v in report.items() if k!="contrasts"}|dict(contrasts=contrasts,storage=storage)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    s=save(generate());print(json.dumps([dict(reference=c["reference"],queries=c["queries"],
        invalid=c["invalid_queries"],sampled=c["sampled_comparison"]) for c in s["contrasts"]]),flush=True)
