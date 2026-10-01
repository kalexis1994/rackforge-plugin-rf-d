"""Same-memory circuit windows isolate a predeclared growth heuristic."""
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack
from loudness_latch_bdf_doubling import trial
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import POLICIES,OUTPUTS,PATHS as SOURCE_PATHS,store,case_summary
from loudness_latch_bdf_common_history import ContinuationPath,continuation_trace,compare
from loudness_latch_time_reference import frozen_rate
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_growth_windows.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_growth_windows_summary.json"
WINDOWS=(("prefix",.0023,10e-6),("attack",.00242,.25e-6),
         ("reset",.00244205,20e-9),("tail",.0025,20e-6))
THRESHOLDS=(.25,.125)
MAXIMUM_ATTEMPTS=600
POLICY=POLICIES[1]
PATHS=tuple(dict.fromkeys((*SOURCE_PATHS,OUTPUTS[1],Path(__file__).resolve(),
                         ROOT/"tools/loudness_latch_bdf_common_history.py")))


def run_window(network,initial,first_h,end,threshold):
    old=unpack(network,initial);rate=frozen_rate(network.network,old.current,10.)
    h=first_h;accepted=[];rejected=[];stop=None
    for _ in range(MAXIMUM_ATTEMPTS):
        if old.time_s>=end:break
        h=min(h,end-old.time_s,POLICY.maximum_step_s,2*old.previous_dt_s)
        if h<2*POLICY.minimum_step_s:
            stop=dict(reason="two-half-interval-domain",time_s=old.time_s,next_dt_s=h);break
        snapshot=state_hash(old)
        try:
            result,d,next_rate=trial(network,old,10.,h,POLICY,rate)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            result=None;d=dict(reason="solve-rejected",error=str(exc))
        if state_hash(old)!=snapshot:raise ValueError("window trial modified incoming histories")
        d=dict(d,startup=False)
        if result is None:
            rejected.append(dict(time_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,diagnostics=d))
            h/=2
            continue
        candidate,diag=result[0]
        accepted.append(dict(start_s=old.time_s,dt_s=h,previous_history_sha256=snapshot,
            steps=[dict(history=pack(candidate),diagnostics=diag,publication=d["full_publication"])],diagnostics=d))
        old=candidate;rate=next_rate
        if (max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"])<threshold
                and d["junction_increment_v"]<POLICY.junction_increment_v/2
                and d["positive_mode_step_product"]<POLICY.positive_mode_step_product/2):
            h=min(2*h,POLICY.maximum_step_s,2*old.previous_dt_s)
    if old.time_s<end and stop is None:stop=dict(reason="window-attempt-budget",time_s=old.time_s)
    return dict(name=str(threshold),growth_error_threshold=threshold,policy=asdict(POLICY),initial=initial,
        first_proposal_s=first_h,end_s=end,maximum_window_attempts=MAXIMUM_ATTEMPTS,
        accepted=accepted,rejected=rejected,accepted_trials=len(accepted),published_intervals=len(accepted),
        attempts=len(accepted)+len(rejected),final=pack(old),final_time_s=old.time_s,
        complete=bool(old.time_s==end),stop=stop,history_reset_count=0,selected_alternative=None)


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(OUTPUTS[1].read_bytes()))["case"]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));windows=[]
    for name,limit,span in WINDOWS:
        index=max(k for k,row in enumerate(source["accepted"]) if row["steps"][-1]["history"]["time_s"]<=limit)
        initial=source["accepted"][index]["steps"][-1]["history"]
        first=source["accepted"][index+1]["dt_s"];end=initial["time_s"]+span
        cases=[run_window(network,initial,first,end,threshold) for threshold in THRESHOLDS]
        comparison=compare(*(continuation_trace(c) for c in cases),all(c["complete"] for c in cases))
        time=comparison["maximum_difference_time_s"]
        paths=[ContinuationPath(network,c) for c in cases]
        queries=[p.query(time) for p in paths] if time>=max(p.times[1] for p in paths) else []
        valid=bool(len(queries)==2 and all(q["query_valid"] for q in queries))
        peak=dict(time_s=time,queries=queries,valid_both=valid)
        if valid:
            a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in queries]
            peak.update(maximum_node_difference_v=float(np.max(np.abs(a-b))))
        row=dict(name=name,anchor_limit_s=limit,window_length_s=span,E4_accepted_anchor_index=index,
            initial=initial,first_proposal_s=first,end_s=end,cases=cases,
            conditional_comparison=comparison,same_time_interpolated_peak=peak)
        windows.append(row)
        print(json.dumps(dict(window=name,cases=[dict(threshold=c["growth_error_threshold"],complete=c["complete"],
            accepted=c["accepted_trials"],rejected=len(c["rejected"])) for c in cases],
            conditional_maximum_v=comparison["maximum_node_difference_v"])),flush=True)
    if hashes(PATHS)!=before:raise ValueError("growth-window inputs changed during execution")
    return dict(schema="rf-d/bdf-growth-windows/v1",source_sha256=before,environment=env,
        windows=windows,thresholds=THRESHOLDS,policy=asdict(POLICY),maximum_window_attempts=MAXIMUM_ATTEMPTS,
        diagnostic_only=True,previous_reports_modified=False,trajectory_retimed=False,
        temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="same E4 memory and proposal condition each finite window; thresholds are both heuristics; no global DC refinement or continuous maximum bound")


def save(report):
    storage=store(report,OUTPUT)
    windows=[]
    for w in report["windows"]:
        peak={k:v for k,v in w["same_time_interpolated_peak"].items() if k!="queries"}
        windows.append({k:v for k,v in w.items() if k not in ("initial","cases","same_time_interpolated_peak")}|
                       dict(cases=[dict(case_summary(c),growth_error_threshold=c["growth_error_threshold"]) for c in w["cases"]],
                            same_time_interpolated_peak=peak))
    summary={k:v for k,v in report.items() if k!="windows"}|dict(windows=windows,storage=storage)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":save(generate())
