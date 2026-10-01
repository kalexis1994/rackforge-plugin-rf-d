"""Predeclared E4G8 DC path: change only the growth error threshold."""
from dataclasses import asdict
import gzip
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,publication_check
from loudness_latch_bdf_survey import state_hash,trace,comparison,END_S,GATE_V
from loudness_latch_bdf_time import trial as startup_trial
from loudness_latch_bdf_doubling import trial
from loudness_latch_bdf_doubling_survey import POLICIES,OUTPUTS,PATHS as SURVEY_PATHS,store,case_summary
from loudness_latch_bdf_growth_windows import OUTPUT as WINDOWS
from loudness_latch_increment_probes import hashes
from loudness_latch_time_reference import frozen_rate
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
NAME="E4G8"
POLICY=POLICIES[1]
GROWTH_ERROR_THRESHOLD=.125
OUTPUT=ROOT/"evidence/loudness_latch_bdf_growth_dc.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_growth_dc_summary.json"
PATHS=tuple(dict.fromkeys((*SURVEY_PATHS,*OUTPUTS,WINDOWS,Path(__file__).resolve())))


def run_case():
    started=perf_counter()
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    history,dc=network.initial_history();initial=pack(history)
    rate=frozen_rate(network.network,history.current,0.)
    h=POLICY.maximum_step_s;accepted=[];rejected=[];stop=None
    for _ in range(POLICY.maximum_attempts):
        if history.time_s>=END_S:break
        h=min(h,END_S-history.time_s)
        if history.previous is not None:h=min(h,2*history.previous_dt_s)
        old=history;snapshot=state_hash(old)
        if h<2*POLICY.minimum_step_s:
            stop=dict(reason="two-half-interval-domain",time_s=old.time_s,next_dt_s=h);break
        startup=old.previous is None
        try:
            result,diag,next_rate=(startup_trial if startup else trial)(network,old,10.,h,POLICY,rate)
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
        if state_hash(old)!=snapshot:raise ValueError("DC growth trial changed incoming histories")
        diag=dict(diag,startup=bool(startup))
        if result is None:
            rejected.append(dict(time_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,diagnostics=diag))
            h/=2
            continue
        steps=[dict(history=pack(candidate),diagnostics=d,publication=p)
               for (candidate,d),p in zip(result,publications)]
        accepted.append(dict(start_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,
                             steps=steps,diagnostics=diag))
        history=result[-1][0];rate=next_rate
        if len(accepted)%100==0:
            print(json.dumps(dict(policy=NAME,time_s=history.time_s,accepted=len(accepted),
                                  rejected=len(rejected),dt_s=h,elapsed_s=perf_counter()-started)),flush=True)
        if (max(diag["voltage_error_ratio"],diag["junction_voltage_error_ratio"])<GROWTH_ERROR_THRESHOLD
                and diag["junction_increment_v"]<POLICY.junction_increment_v/2
                and diag["positive_mode_step_product"]<POLICY.positive_mode_step_product/2):
            h=min(2*h,POLICY.maximum_step_s,2*history.previous_dt_s)
    if history.time_s<END_S and stop is None:stop=dict(reason="attempt-budget",time_s=history.time_s)
    return dict(name=NAME,growth_error_threshold=GROWTH_ERROR_THRESHOLD,policy=asdict(POLICY),
        initial=initial,dc_diagnostics=dc,accepted=accepted,rejected=rejected,
        accepted_trials=len(accepted),published_intervals=sum(len(r["steps"]) for r in accepted),
        final=pack(history),final_time_s=history.time_s,complete=bool(history.time_s==END_S),stop=stop,
        attempts=len(accepted)+len(rejected),history_reset_count=0,selected_alternative=None,
        offline_integration_wall_s=perf_counter()-started)


def generate():
    before=hashes(PATHS);env=environment();case=run_case()
    if hashes(PATHS)!=before:raise ValueError("DC growth inputs changed during execution")
    payload=dict(schema="rf-d/bdf-growth-dc/v1",source_sha256=before,environment=env,case=case,
        previous_reports_modified=False,physical_switching_admitted=False,audio_admitted=False)
    storage=store(payload,OUTPUT)
    comparisons=[]
    for name,path in zip(("D4","E4"),OUTPUTS):
        reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
        comparisons.append(dict(reference=name,diagnostic_only=True,
            **comparison(trace(reference),trace(case),reference["complete"] and case["complete"])))
    if hashes(PATHS)!=before:raise ValueError("DC growth inputs changed during summary")
    summary=dict(schema="rf-d/bdf-growth-dc-summary/v1",source_sha256=before,environment=env,
        case=dict(case_summary(case),storage=storage,attempts=case["attempts"],
                  growth_error_threshold=GROWTH_ERROR_THRESHOLD,
                  offline_integration_wall_s=case["offline_integration_wall_s"]),
        comparisons=comparisons,end_s=END_S,maximum_difference_gate_v=GATE_V,
        policies_predeclared=True,changed_control="growth error threshold .25 to .125 only",
        startup="BE-full versus BE-half plus BDF2-half, only while previous history is absent",
        normal_estimator="full BDF2 versus two provisional BDF2 halves; publish full, raw difference",
        previous_reports_modified=False,trajectory_retimed=False,selected=None,
        diagnostic_only=True,temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        independent_spatial_oracle=False,physical_charge_identified=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="growth sensitivity at fixed E4 tolerances is not a refinement sequence; offline wall time is not an audio deadline; conserved same-time audit follows")
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    s=generate();print(json.dumps(dict(case=s["case"],comparisons=s["comparisons"])),flush=True)
