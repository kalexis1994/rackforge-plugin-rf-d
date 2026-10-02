"""Explicit E4G8 driver with only the Newton network construction replaced."""
import ast
from dataclasses import asdict
import gzip
import inspect
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork,VERSION
import loudness_latch_bdf_growth_dc as original_driver
from loudness_latch_bdf_growth_dc import NAME,POLICY,GROWTH_ERROR_THRESHOLD,OUTPUT as SOURCE
from loudness_latch_bdf_static_precision_fixed_clock import OUTPUT as FIXED,PATHS as OLD_PATHS
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash,trace,comparison,END_S,GATE_V
from loudness_latch_bdf_time import trial as startup_trial
from loudness_latch_bdf_doubling import trial
from loudness_latch_bdf_doubling_survey import OUTPUTS,store,canonical,case_summary
from loudness_latch_bdf_memory_transfer import node_difference,memory_difference
from loudness_latch_increment_probes import hashes
from loudness_latch_time_reference import frozen_rate
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_adaptive.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_adaptive_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_CONTROLADOR_COMPENSADO_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,FIXED,SOURCE,*OUTPUTS,Path(__file__).resolve(),PROTOCOL)))


def run_case():
    started=perf_counter()
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))
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


def driver_audit():
    reference=ast.parse(inspect.getsource(original_driver.run_case))
    candidate=ast.parse(inspect.getsource(run_case));count=0
    for node in ast.walk(candidate):
        if isinstance(node,ast.Name) and node.id=="CompensatedBdfNetwork":
            node.id="BdfNetwork";count+=1
    equal=ast.dump(reference,include_attributes=False)==ast.dump(candidate,include_attributes=False)
    if count!=1 or not equal:raise ValueError("controller driver changed beyond its single network constructor")
    return dict(normalized_ast_equal=equal,network_constructor_substitutions=count,
        reference_driver_source_utf8=inspect.getsource(original_driver.run_case),
        candidate_driver_source_utf8=inspect.getsource(run_case))


def published(case):return [s for a in case["accepted"] for s in a["steps"]]


def clock(steps):return [[s["history"]["time_s"],s["diagnostics"]["actual_dt_s"],
    s["history"]["key_v"],s["diagnostics"]["method"]] for s in steps]


def decisions(case):
    return dict(accepted=[[a["start_s"],a["dt_s"],len(a["steps"])] for a in case["accepted"]],
        rejected=[[a["time_s"],a["dt_s"],a["diagnostics"]["reason"]] for a in case["rejected"]])


def generate():
    before=hashes(PATHS);env=environment();audit=driver_audit();case=run_case()
    source=json.loads(gzip.decompress(SOURCE.read_bytes()))["case"]
    steps=published(case);base=published(source)
    new_clock=clock(steps);old_clock=clock(base);same_clock=new_clock==old_clock
    controller_decisions_equal=decisions(case)==decisions(source)
    initial_equal=canonical(case["initial"])==canonical(source["initial"])
    if case["policy"]!=source["policy"] or case["growth_error_threshold"]!=source["growth_error_threshold"]:
        raise ValueError("declared controller policy differs from source")
    contrast=dict(initial_equal=initial_equal,published_clocks_equal=same_clock,
        controller_decisions_equal=controller_decisions_equal,candidate_decisions=decisions(case),
        reference_decisions=decisions(source),candidate_clock=new_clock,reference_clock=old_clock,
        rows=[],fixed_clock_states_identical=None,coordinate_gate_v=1e-8,charge_coordinate_scale_c_per_v=1e-12)
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"))
    if same_clock:
        for index,(s,b) in enumerate(zip(steps,base)):
            new=unpack(network,s["history"]);old=unpack(network,b["history"])
            nodes=node_difference(new.current,old.current);memory=memory_difference(new.current,old.current)
            contrast["rows"].append(dict(index=index,time_s=new.time_s,node_difference_v=nodes.tolist(),
                memory_difference_v=memory.tolist(),max_node_difference_v=float(np.max(abs(nodes))),
                max_memory_coordinate_difference_v=float(np.max(abs(memory))),
                node_gate_passed=bool(np.max(abs(nodes))<1e-8),memory_gate_passed=bool(np.max(abs(memory))<1e-8)))
    del source,base
    fixed=json.loads(gzip.decompress(FIXED.read_bytes()))
    fixed_steps=[dict(history=r["history"],diagnostics=r["diagnostics"]) for r in fixed["rows"]]
    if new_clock==clock(fixed_steps):
        contrast["fixed_clock_states_identical"]=all(canonical(s["history"])==canonical(f["history"])
            for s,f in zip(steps,fixed_steps))
    del fixed,fixed_steps
    temporal=[]
    for name,path in zip(("D4","E4"),OUTPUTS):
        reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
        temporal.append(dict(reference=name,diagnostic_only=True,
            **comparison(trace(reference),trace(case),reference["complete"] and case["complete"])))
        del reference
    if hashes(PATHS)!=before:raise ValueError("adaptive candidate inputs changed during execution")
    equivalent=bool(case["complete"] and initial_equal and same_clock and controller_decisions_equal
        and all(r["node_gate_passed"] and r["memory_gate_passed"] for r in contrast["rows"]))
    return dict(schema="rf-d/bdf-compensated-adaptive/v1",source_sha256=before,environment=env,
        candidate_version=VERSION,driver_audit=audit,case=case,contrast=contrast,temporal_comparisons=temporal,
        controller_equivalence_passed=equivalent,adaptive_controller_applied=True,
        modal_guard_uses_original_shared_derivative=True,original_controller_policy_modified=False,
        original_solver_modified=False,previous_reports_modified=False,trajectory_retimed=False,
        temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        independent_full_spatial_oracle=False,physical_switching_admitted=False,
        audio_admitted=False,deadline_admitted=False,diagnostic_only=True)


def save(report):
    storage=store(report,OUTPUT);case=report["case"];contrast=report["contrast"]
    summary={k:v for k,v in report.items() if k not in ("driver_audit","case","contrast")}
    summary.update(storage=storage,driver_audit={k:v for k,v in report["driver_audit"].items() if not k.endswith("source_utf8")},
        case=case_summary(case)|dict(attempts=case["attempts"],growth_error_threshold=case["growth_error_threshold"],
            offline_integration_wall_s=case["offline_integration_wall_s"]),
        contrast={k:v for k,v in contrast.items() if k not in ("candidate_decisions","reference_decisions","candidate_clock","reference_clock","rows")}
        |dict(compared_intervals=len(contrast["rows"]),
            max_node_difference_v=max((r["max_node_difference_v"] for r in contrast["rows"]),default=None),
            max_memory_coordinate_difference_v=max((r["max_memory_coordinate_difference_v"] for r in contrast["rows"]),default=None),
            node_comparison_failures=sum(not r["node_gate_passed"] for r in contrast["rows"]),
            memory_comparison_failures=sum(not r["memory_gate_passed"] for r in contrast["rows"])))
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":
    result=save(generate());print(json.dumps(dict(case=result["case"],contrast=result["contrast"],storage=result["storage"])),flush=True)
