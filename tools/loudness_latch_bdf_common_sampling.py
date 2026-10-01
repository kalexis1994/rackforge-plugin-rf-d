"""Observe every node's interpolated peak and the retained temporal grid."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from loudness_latch_bdf_common_history import (OUTPUT as COMMON,PATHS as COMMON_PATHS,STRICT,
    reference_case,continuation_trace,ContinuationPath)
from loudness_latch_bdf_observation_domain import OUTPUT as GRID
from loudness_latch_bdf_sampling import metrics
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_increment_probes import hashes
from bjt_charge_ngspice_probes import model_parameters
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_common_sampling.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_common_sampling_summary.json"
PATHS=tuple(dict.fromkeys((*COMMON_PATHS,Path(__file__).resolve(),COMMON,GRID)))


def node_peaks(a,b):
    ta,va=a;tb,vb=b
    start=max(float(ta[0]),float(tb[0]));end=min(float(ta[-1]),float(tb[-1]))
    times=np.unique(np.concatenate((ta,tb)));times=times[(times>=start)&(times<=end)]
    av=np.column_stack([np.interp(times,ta,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(times,tb,vb[:,k]) for k in range(94)])
    delta=np.abs(av-bv);indices=np.argmax(delta,axis=0)
    return [dict(node_index=k,time_s=float(times[int(indices[k])]),
                 interpolated_difference_v=float(delta[int(indices[k]),k])) for k in range(94)]


def fd_observation(network,path,query):
    old=path.previous(query["position"]);snapshot=state_hash(old)
    steps=query["path_steps"] or [dict(diagnostics=query["diagnostics"],candidate=query["candidate"])]
    checks=[]
    for s in steps:
        h=s["diagnostics"]["actual_dt_s"];before=state_hash(old)
        candidate,diag=network.advance(old,10.,h,use_fd=True)
        check=publication_check(network,old,candidate,h,diag)
        if state_hash(old)!=before:raise ValueError("FD observation modified its provisional incoming history")
        checks.append(dict(candidate=pack(candidate),diagnostics=diag,publication=check,previous_history_sha256=before,published=False))
        old=candidate
    actual=unpack(network,query["candidate"])
    maximum=float(np.max(np.abs(np.array(actual.current.joint.node_v)-old.current.joint.node_v)))
    return dict(time_s=query["time_s"],previous_history_sha256=snapshot,steps=checks,
        max_node_difference_v=maximum,voltage_gate_v=1e-8,
        passed=maximum<1e-8 and old.time_s==query["time_s"]
        and all(c["publication"]["max_published_kcl_a"]<1e-11 for c in checks),published=False)


def generate():
    before=hashes(PATHS)
    common=json.loads(gzip.decompress(COMMON.read_bytes()))
    strict=json.loads(gzip.decompress(STRICT.read_bytes()))
    grid=json.loads(gzip.decompress(GRID.read_bytes()))
    cases=[common["case"],reference_case(strict,common["anchor_C3_accepted_index"])]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    paths=[ContinuationPath(network,c) for c in cases]
    peaks=node_peaks(*(continuation_trace(c) for c in cases))
    start=max(float(p.times[1]) for p in paths);end=min(float(p.times[-1]) for p in paths)
    retained=[row["time_s"] for row in grid["rows"] if start<=row["time_s"]<=end]
    landmarks=dict(interpolated_common_peak=common["conditional_comparison"]["maximum_difference_time_s"],
                   original_DC_peak=common["original_full_comparison"]["maximum_difference_time_s"])
    times=sorted(set(retained+[p["time_s"] for p in peaks if start<=p["time_s"]<=end]+list(landmarks.values())))
    rows=[]
    for number,time in enumerate(times):
        queries=[p.query(time) for p in paths];valid=all(q["query_valid"] for q in queries)
        row=dict(time_s=time,queries=queries,valid_both=valid,
            retained_grid=time in retained,node_peak_indices=[p["node_index"] for p in peaks if p["time_s"]==time],
            landmarks=[name for name,t in landmarks.items() if t==time])
        if valid:
            a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
            delta=np.abs(a-b);row.update(maximum_node_difference_v=float(np.max(delta)),maximum_difference_node=int(np.argmax(delta)))
        rows.append(row)
        if (number+1)%100==0:print(json.dumps(dict(common_observations=number+1,total=len(times))),flush=True)
    sampled=metrics(rows,end)
    fd=[]
    for name,time in ("interpolated_common_peak",landmarks["interpolated_common_peak"]),("sampled_common_peak",sampled["maximum_difference_time_s"]):
        row=next(r for r in rows if r["time_s"]==time)
        for policy,path,q in zip(("B3-common","C3-inherited"),paths,row["queries"]):
            if q["query_valid"]:fd.append(dict(fd_observation(network,path,q),landmark=name,policy=policy))
    if hashes(PATHS)!=before:raise ValueError("common observation inputs changed during execution")
    return dict(schema="rf-d/bdf-common-sampled/v1",source_sha256=before,environment=environment(),
        node_peaks=peaks,retained_grid_times_s=retained,start_s=start,end_s=end,landmarks=landmarks,
        rows=rows,fd_observations=fd,sampled_comparison=sampled,
        original_interpolated_common_comparison=common["conditional_comparison"],
        original_DC_comparison=common["original_full_comparison"],
        diagnostic_only=True,trajectory_retimed=False,previous_reports_modified=False,
        temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="finite query set includes every node's linear-interpolation maximum; does not locate the exact continuous maximum or remove prefix dependence of the original DC paths")


def save(report):
    canonical=json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    encoded=gzip.compress(canonical,compresslevel=9,mtime=0)
    if json.dumps(json.loads(gzip.decompress(encoded)),sort_keys=True,separators=(",",":"),allow_nan=False).encode()!=canonical:
        raise ValueError("lossless common sampled storage failed")
    OUTPUT.write_bytes(encoded)
    summary={k:v for k,v in report.items() if k not in ("rows","fd_observations")}
    summary.update(path=str(OUTPUT.relative_to(ROOT)).replace("\\","/"),
        compressed_sha256=hashlib.sha256(encoded).hexdigest(),canonical_json_sha256=hashlib.sha256(canonical).hexdigest(),
        observation_times=len(report["rows"]),queries=2*len(report["rows"]),
        invalid_queries=sum(not q["query_valid"] for r in report["rows"] for q in r["queries"]),
        fd_observations=[{k:v for k,v in d.items() if k!="steps"} for d in report["fd_observations"]])
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    s=save(generate());print(json.dumps({k:s[k] for k in ("observation_times","queries","invalid_queries","sampled_comparison","fd_observations")}),flush=True)
