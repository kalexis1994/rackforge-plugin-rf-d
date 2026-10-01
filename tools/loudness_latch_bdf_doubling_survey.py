"""Predeclared DC-to-3 ms BDF2 full/half survey; preserve failed paths."""
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,publication_check
from loudness_latch_bdf_survey import state_hash,trace,comparison,END_S,GATE_V
from loudness_latch_bdf_time import trial as startup_trial
from loudness_latch_bdf_doubling import trial
from loudness_latch_bdf_doubling_probes import PATHS as PROBE_PATHS,OUTPUT as PROBES
from loudness_latch_bdf_refinement import OUTPUT as STRICT
from loudness_latch_increment_time import Policy
from loudness_latch_increment_probes import hashes
from loudness_latch_time_reference import frozen_rate
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
NAMES=("D4","E4")
POLICIES=(Policy(4e-8,4e-8,4e-8,4e-8,.025,.05,1e-4,1e-12,6000),
          Policy(1e-8,1e-8,1e-8,1e-8,.0125,.025,1e-4,1e-12,12000))
OUTPUTS=tuple(ROOT/f"evidence/loudness_latch_bdf_doubling_{name.lower()}.json.gz" for name in NAMES)
SUMMARY=ROOT/"evidence/loudness_latch_bdf_doubling_survey_summary.json"
PATHS=tuple(dict.fromkeys((*PROBE_PATHS,Path(__file__).resolve(),PROBES,STRICT)))


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def store(value,path):
    raw=canonical(value);encoded=gzip.compress(raw,compresslevel=9,mtime=0)
    if canonical(json.loads(gzip.decompress(encoded)))!=raw:
        raise ValueError("lossless canonical storage failed")
    path.write_bytes(encoded)
    return dict(path=path.relative_to(ROOT).as_posix(),bytes=len(encoded),
                compressed_sha256=hashlib.sha256(encoded).hexdigest(),
                canonical_json_sha256=hashlib.sha256(raw).hexdigest())


def run_case(policy,name):
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    history,dc=network.initial_history();initial=pack(history)
    rate=frozen_rate(network.network,history.current,0.)
    h=policy.maximum_step_s;accepted=[];rejected=[];stop=None
    for attempt in range(policy.maximum_attempts):
        if history.time_s>=END_S:break
        h=min(h,END_S-history.time_s)
        if history.previous is not None:h=min(h,2*history.previous_dt_s)
        old=history;snapshot=state_hash(old)
        if h<2*policy.minimum_step_s:
            stop=dict(reason="two-half-interval-domain",time_s=old.time_s,next_dt_s=h);break
        startup=old.previous is None
        try:
            result,diag,next_rate=(startup_trial if startup else trial)(network,old,10.,h,policy,rate)
            publications=[]
            if result is not None:
                previous=old
                for candidate,d in result:
                    check=publication_check(network,previous,candidate,d["actual_dt_s"],d)
                    publications.append(check);previous=candidate
                if any(not c["round_trip_exact"] or c["max_published_kcl_a"]>=1e-11
                       or c["max_branch_equation_error_v"]>=1e-14 for c in publications):
                    result=None;diag=dict(diag,reason="publication-rejected",publication=publications)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            result=None;diag=dict(reason="solve-rejected",error=str(exc))
        if state_hash(old)!=snapshot:raise ValueError("trial changed incoming accepted histories")
        diag=dict(diag,startup=bool(startup))
        if result is None:
            rejected.append(dict(time_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,diagnostics=diag))
            h/=2
            if h<2*policy.minimum_step_s:
                stop=dict(reason="two-half-interval-domain",time_s=old.time_s,next_dt_s=h);break
            continue
        steps=[dict(history=pack(candidate),diagnostics=d,publication=p)
               for (candidate,d),p in zip(result,publications)]
        accepted.append(dict(start_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,
                             steps=steps,diagnostics=diag))
        history=result[-1][0];rate=next_rate
        if len(accepted)%100==0:
            print(json.dumps(dict(policy=name,time_s=history.time_s,accepted=len(accepted),
                                  rejected=len(rejected),dt_s=h)),flush=True)
        if (max(diag["voltage_error_ratio"],diag["junction_voltage_error_ratio"])<.25
                and diag["junction_increment_v"]<policy.junction_increment_v/2
                and diag["positive_mode_step_product"]<policy.positive_mode_step_product/2):
            h=min(2*h,policy.maximum_step_s,2*history.previous_dt_s)
    if history.time_s<END_S and stop is None:stop=dict(reason="attempt-budget",time_s=history.time_s)
    case=dict(name=name,policy=asdict(policy),initial=initial,dc_diagnostics=dc,accepted=accepted,rejected=rejected,
        accepted_trials=len(accepted),published_intervals=sum(len(r["steps"]) for r in accepted),
        final=pack(history),final_time_s=history.time_s,complete=bool(history.time_s>=END_S),stop=stop,
        attempts=len(accepted)+len(rejected),history_reset_count=0,selected_alternative=None)
    print(json.dumps(dict(policy=name,complete=case["complete"],accepted=len(accepted),
                          rejected=len(rejected),stop=stop)),flush=True)
    return case


def case_summary(case):
    steps=[s for row in case["accepted"] for s in row["steps"]]
    shadows=[s for row in case["accepted"] for s in row["diagnostics"].get("shadow_half_steps",[])]
    return dict(name=case["name"],policy=case["policy"],complete=case["complete"],stop=case["stop"],
        final_time_s=case["final_time_s"],accepted_trials=case["accepted_trials"],
        published_intervals=case["published_intervals"],provisional_accepted_half_intervals=len(shadows),
        rejected_trials=len(case["rejected"]),
        rejection_reasons=dict(Counter(r["diagnostics"]["reason"] for r in case["rejected"])),
        startup_published_intervals=sum(len(r["steps"]) for r in case["accepted"] if r["diagnostics"]["startup"]),
        minimum_published_interval_s=min((s["diagnostics"]["actual_dt_s"] for s in steps),default=None),
        minimum_provisional_half_interval_s=min((s["diagnostics"]["actual_dt_s"] for s in shadows),default=None),
        max_published_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in steps),default=None),
        max_provisional_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in shadows),default=None))


def generate():
    before=hashes(PATHS);env=environment();cases=[];stored=[]
    for name,policy,path in zip(NAMES,POLICIES,OUTPUTS):
        case=run_case(policy,name)
        if hashes(PATHS)!=before:raise ValueError("survey inputs changed during execution")
        payload=dict(schema="rf-d/bdf-doubling-case/v1",source_sha256=before,environment=env,case=case,
                     previous_reports_modified=False,physical_switching_admitted=False,audio_admitted=False)
        stored.append(store(payload,path));cases.append(case)
    strict=json.loads(gzip.decompress(STRICT.read_bytes()))["case"]
    refinement=comparison(*(trace(c) for c in cases),all(c["complete"] for c in cases))
    cross=[comparison(trace(c),trace(strict),c["complete"] and strict["complete"]) for c in cases]
    if hashes(PATHS)!=before:raise ValueError("survey inputs changed during execution")
    summary=dict(schema="rf-d/bdf-doubling-survey-summary/v1",source_sha256=before,environment=env,
        end_s=END_S,r61_ohm=200,profile="finite_transit",key_before_v=0.,key_after_v=10.,
        cases=[dict(case_summary(c),storage=s) for c,s in zip(cases,stored)],
        refinement=refinement,C3_cross_comparisons=cross,maximum_difference_gate_v=GATE_V,
        startup="BE-full versus BE-half plus BDF2-half, only while previous history is absent",
        normal_estimator="full BDF2 versus two provisional BDF2 halves; publish full, raw difference",
        policies_predeclared=True,previous_reports_modified=False,trajectory_retimed=False,
        independent_spatial_oracle=False,temporal_refinement_admitted=refinement["passed"],
        temporal_error_bound_admitted=False,physical_charge_identified=False,physical_switching_admitted=False,
        audio_admitted=False,selected=None,
        limitation="shared spatial solver and synthetic charge; local estimates do not bound global error; linear observations require conserved same-time audit")
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    result=generate();print(json.dumps(dict(refinement=result["refinement"],cases=result["cases"])),flush=True)
