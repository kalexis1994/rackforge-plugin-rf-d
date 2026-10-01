"""A third complete BDF2 path with thresholds fixed before measurement."""
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
from loudness_latch_bdf_survey import run_case, trace, comparison, PATHS as SURVEY_PATHS
from loudness_latch_increment_time import Policy
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/"evidence/loudness_latch_bdf_survey.json.gz"
OUTPUT=ROOT/"evidence/loudness_latch_bdf_refinement.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_refinement_summary.json"
POLICY=Policy(6.25e-6,6.25e-6,6.25e-6,6.25e-6,.0125,.025,1e-4,1e-12,6000)
PATHS=tuple(dict.fromkeys((*SURVEY_PATHS,Path(__file__).resolve(),PREVIOUS)))


def generate():
    before=hashes(PATHS)
    previous=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
    case=run_case(POLICY,"C3")
    complete=case["complete"] and previous["cases"][1]["complete"]
    refinement=comparison(trace(previous["cases"][1]),trace(case),complete)
    if hashes(PATHS)!=before:raise ValueError("strict refinement inputs changed during execution")
    return dict(schema="rf-d/bdf-third-path/v1",source_sha256=before,environment=environment(),
        policy_name="C3",policy=asdict(POLICY),case=case,end_s=.003,
        previous_policy_name="B3",previous_case_index=1,
        previous_report=str(PREVIOUS.relative_to(ROOT)).replace("\\","/"),
        refinement=refinement,temporal_refinement_admitted=refinement["passed"],
        previous_reports_modified=False,independent_spatial_oracle=False,
        temporal_error_bound_admitted=False,physical_charge_identified=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="same spatial solver and synthetic transistor charges; local BE-BDF estimator is not a global or continuous error bound")


def save(report):
    canonical=json.dumps(report,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    encoded=gzip.compress(canonical,compresslevel=9,mtime=0)
    restored=json.loads(gzip.decompress(encoded))
    if json.dumps(restored,sort_keys=True,separators=(",",":"),allow_nan=False).encode()!=canonical:
        raise ValueError("lossless refinement storage failed")
    OUTPUT.write_bytes(encoded)
    case=report["case"];steps=[s for row in case["accepted"] for s in row["steps"]]
    summary=dict(schema="rf-d/bdf-third-path-summary/v1",path=str(OUTPUT.relative_to(ROOT)).replace("\\","/"),
        compressed_sha256=hashlib.sha256(encoded).hexdigest(),canonical_json_sha256=hashlib.sha256(canonical).hexdigest(),
        source_sha256=report["source_sha256"],environment=report["environment"],policy_name=report["policy_name"],
        policy=report["policy"],complete=case["complete"],stop=case["stop"],final_time_s=case["final_time_s"],
        accepted_trials=case["accepted_trials"],published_intervals=case["published_intervals"],
        rejected_trials=len(case["rejected"]),attempts=case["attempts"],
        rejection_reasons=dict(Counter(r["diagnostics"]["reason"] for r in case["rejected"])),
        minimum_interval_s=min((s["diagnostics"]["actual_dt_s"] for s in steps),default=None),
        max_published_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in steps),default=None),
        refinement=report["refinement"],temporal_refinement_admitted=report["temporal_refinement_admitted"],
        previous_reports_modified=False,independent_spatial_oracle=False,
        temporal_error_bound_admitted=False,physical_switching_admitted=False,audio_admitted=False)
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    print(json.dumps(save(generate())),flush=True)
