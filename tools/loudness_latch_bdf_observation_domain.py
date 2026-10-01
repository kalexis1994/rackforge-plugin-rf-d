"""Observe the exact requested clock time with provisional steps >= 1 ps."""
from bisect import bisect_left
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from loudness_latch_bdf_sampling import SavedPath,metrics,PATHS as SAMPLING_PATHS,OUTPUT as ORIGINAL
from loudness_latch_bdf_refinement import PREVIOUS,OUTPUT as STRICT
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_increment_probes import hashes
from bjt_charge_ngspice_probes import model_parameters
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_observation_domain.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_observation_domain_summary.json"
MINIMUM_STEP_S=1e-12
PATHS=tuple(dict.fromkeys((*SAMPLING_PATHS,Path(__file__).resolve(),ORIGINAL)))


class DomainPath(SavedPath):
    def query(self,time,stored=None):
        time=float(time)
        if not np.isfinite(time) or not self.times[1]<=time<=self.times[-1]:
            raise ValueError("observation outside saved common coverage")
        nearest=bisect_left(self.times,time)-1
        incoming=self.previous(nearest);gap=time-incoming.time_s
        endpoint=self.steps[nearest]["history"]["time_s"]
        if endpoint==time or gap>=MINIMUM_STEP_S:
            q=dict(super().query(time) if stored is None else stored)
            if q["time_s"]!=time or q["position"]!=nearest:
                raise ValueError("stored observation does not describe this requested time and anchor")
            if q.get("diagnostics",{}).get("actual_dt_s",MINIMUM_STEP_S)<MINIMUM_STEP_S:
                raise ValueError("accepted endpoint or ordinary observation outside declared domain")
            return dict(q,observation_version="minimum-step-domain/v2",source_query_reused=stored is not None,
                        nearest_position=nearest,requested_remainder_s=gap,path_steps=[])
        # A sub-domain remainder is never solved or rounded to an endpoint.
        # Look back one accepted state, then atomically observe two half steps.
        if nearest<1:raise ValueError("earlier accepted anchor unavailable")
        position=nearest-1;old=self.previous(position)
        if old.previous is None:raise ValueError("two accepted histories required at the earlier observation anchor")
        snapshot=state_hash(old);span=time-old.time_s;h=span/2
        result=dict(time_s=time,position=position,nearest_position=nearest,requested_remainder_s=gap,
            previous_history_sha256=snapshot,query_method="unpublished-two-BDF2-steps-from-earlier-accepted-anchor",
            observation_version="minimum-step-domain/v2",source_query_reused=False,path_steps=[],published=False)
        previous=old
        try:
            for part in range(2):
                dt=h if part==0 else time-previous.time_s
                if dt<MINIMUM_STEP_S:raise ValueError("partial observation interval below declared minimum")
                before=state_hash(previous)
                candidate,diag=self.network.advance(previous,10.,dt)
                check=publication_check(self.network,previous,candidate,dt,diag)
                result["path_steps"].append(dict(candidate=pack(candidate),diagnostics=diag,publication=check,
                                                  previous_history_sha256=before,published=False))
                if state_hash(previous)!=before:raise ValueError("partial step modified its incoming history")
                if (check["max_published_kcl_a"]>=1e-11 or check["max_branch_equation_error_v"]>=1e-14
                        or not check["round_trip_exact"]):
                    raise ValueError("provisional observation publication check failed")
                previous=candidate
            if previous.time_s!=time:raise ValueError("observation did not reach the exact requested binary clock time")
            interpolated=np.array([np.interp(time,self.times,self.volts[:,k]) for k in range(94)])
            actual=np.array(previous.current.joint.node_v)
            result.update(candidate=pack(previous),diagnostics=diag,publication=check,query_valid=True,
                          interpolation_difference_v=list(map(float,interpolated-actual)),
                          max_interpolation_difference_v=float(np.max(np.abs(interpolated-actual))))
        except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
            result.update(query_valid=False,error=str(exc))
        if state_hash(old)!=snapshot:raise ValueError("observation changed the earlier accepted histories")
        return result


def generate():
    before=hashes(PATHS)
    original=json.loads(gzip.decompress(ORIGINAL.read_bytes()))
    previous=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
    strict=json.loads(gzip.decompress(STRICT.read_bytes()))
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    cases=[previous["cases"][1],strict["case"]]
    if any(c["policy"]["minimum_step_s"]!=MINIMUM_STEP_S for c in cases):
        raise ValueError("observation domain must match both declared trajectory minima")
    paths=[DomainPath(network,c) for c in cases];rows=[]
    for source in original["rows"]:
        time=source["time_s"];queries=[p.query(time,q) for p,q in zip(paths,source["queries"])]
        valid=all(q["query_valid"] for q in queries)
        row=dict(time_s=time,tags=source["tags"],queries=queries,valid_both=valid)
        if valid:
            a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
            delta=np.abs(a-b);row.update(maximum_node_difference_v=float(np.max(delta)),maximum_difference_node=int(np.argmax(delta)))
        rows.append(row)
    if hashes(PATHS)!=before:raise ValueError("observation domain inputs changed during execution")
    return dict(schema="rf-d/bdf-observation-domain/v2",source_sha256=before,environment=environment(),
        minimum_observation_step_s=MINIMUM_STEP_S,rows=rows,
        original_full_comparison=original["original_full_comparison"],
        original_prefix_comparison=original["original_prefix_comparison"],
        original_sampling_comparison=original["sampled_full_comparison"],
        sampled_full_comparison=metrics(rows,original["end_s"]),sampled_prefix_comparison=metrics(rows,.0023),
        landmarks=original["landmarks"],requested_times_modified=False,
        previous_reports_modified=False,trajectory_modified=False,diagnostic_only=True,
        temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="two unpublished half observations from an earlier accepted anchor replace only sub-domain remainders; no BE-BDF local acceptance or continuous/global error bound")


def save(report):
    canonical=json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    encoded=gzip.compress(canonical,compresslevel=9,mtime=0)
    if json.dumps(json.loads(gzip.decompress(encoded)),sort_keys=True,separators=(",",":"),allow_nan=False).encode()!=canonical:
        raise ValueError("lossless observation domain storage failed")
    OUTPUT.write_bytes(encoded)
    queries=[q for row in report["rows"] for q in row["queries"]]
    summary={k:v for k,v in report.items() if k!="rows"}
    summary.update(path=str(OUTPUT.relative_to(ROOT)).replace("\\","/"),
        compressed_sha256=hashlib.sha256(encoded).hexdigest(),canonical_json_sha256=hashlib.sha256(canonical).hexdigest(),
        observation_times=len(report["rows"]),queries=len(queries),invalid_queries=sum(not q["query_valid"] for q in queries),
        reused_queries=sum(q["source_query_reused"] for q in queries),
        earlier_anchor_queries=sum(not q["source_query_reused"] for q in queries),
        provisional_intervals=sum(len(q["path_steps"]) for q in queries),
        failure_reasons=dict(Counter(q.get("error","check-failed") for q in queries if not q["query_valid"])),
        min_provisional_interval_s=min((s["diagnostics"]["actual_dt_s"] for q in queries for s in q["path_steps"]),default=None),
        max_provisional_kcl_a=max((s["publication"]["max_published_kcl_a"] for q in queries for s in q["path_steps"]),default=None))
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":print(json.dumps(save(generate())),flush=True)
