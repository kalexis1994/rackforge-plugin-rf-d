"""Frozen E4G8 published clock, inherited residual and own candidate histories."""
import gzip
import json
import math
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork,VERSION
from loudness_latch_bdf_static_precision_continuation import OUTPUT as WINDOWS,PATHS as OLD_PATHS
from loudness_latch_bdf_growth_dc import OUTPUT as SOURCE
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_memory_transfer import node_difference,memory_difference
from loudness_latch_bdf_survey import state_hash
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store,canonical
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_fixed_clock.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_fixed_clock_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_RELOJ_COMPLETO_COMPENSADO_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,WINDOWS,SOURCE,Path(__file__).resolve(),PROTOCOL)))
STEP_COUNT=6486
SOURCE_SHA256="d912d493022638b37f23b2b6d5c1eff345b387e8eeed1e42e3a86c710168f0dd"


def schedule(network,case):
    old=unpack(network,case["initial"]);rows=[]
    if old.time_s!=0. or old.previous is not None:raise ValueError("archived DC startup required")
    for trial_index,trial in enumerate(case["accepted"]):
        if state_hash(old)!=trial["previous_history_sha256"] or old.time_s!=trial["start_s"]:
            raise ValueError("reference trial lineage mismatch")
        for step_index,step in enumerate(trial["steps"]):
            h=step["diagnostics"]["actual_dt_s"];new=unpack(network,step["history"])
            if not math.isfinite(h) or h<1e-12:raise ValueError("reference interval outside 1 ps domain")
            if (new.time_s!=old.time_s+h or new.previous!=old.current or new.previous_dt_s!=h
                    or new.previous_key_v!=old.key_v or new.key_v!=10.):
                raise ValueError("reference step clock or complete previous state mismatch")
            rows.append(dict(trial_index=trial_index,step_index=step_index,dt_s=h,
                time_s=new.time_s,reference_incoming_sha256=state_hash(old),step=step))
            old=new
    if len(rows)!=STEP_COUNT or old.time_s!=.003 or canonical(pack(old))!=canonical(case["final"]):
        raise ValueError("declared full reference coverage mismatch")
    return rows


def comparison_row(new,reference):
    nodes=node_difference(new.current,reference.current);memory=memory_difference(new.current,reference.current)
    return dict(node_difference_v=nodes.tolist(),memory_difference_v=memory.tolist(),
        max_node_difference_v=float(np.max(abs(nodes))),max_memory_coordinate_difference_v=float(np.max(abs(memory))),
        maximum_difference_node=int(np.argmax(abs(nodes))),maximum_difference_memory=int(np.argmax(abs(memory))),
        node_gate_passed=bool(np.max(abs(nodes))<1e-8),memory_gate_passed=bool(np.max(abs(memory))<1e-8),
        reference_time_equal=new.time_s==reference.time_s)


def generate():
    before=hashes(PATHS);env=environment()
    if before[SOURCE.relative_to(ROOT).as_posix()]!=SOURCE_SHA256:raise ValueError("frozen E4G8 source identity mismatch")
    case=json.loads(gzip.decompress(SOURCE.read_bytes()))["case"]
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"));clock=schedule(network,case)
    initial,dc=network.initial_history();initial_matches=canonical(pack(initial))==canonical(case["initial"])
    old=initial;rows=[];stop=None;attempts=0
    if initial_matches:
        for index,slot in enumerate(clock):
            h=slot["dt_s"];snapshot=state_hash(old);attempts+=1
            try:
                new,d=network.advance(old,10.,h)
                if state_hash(old)!=snapshot:raise ValueError("fixed-clock step mutated its incoming histories")
                pub=publication_check(network,old,new,h,d)
                reference=unpack(network,slot["step"]["history"])
                row=dict(index=index,trial_index=slot["trial_index"],step_index=slot["step_index"],
                    history=pack(new),diagnostics=d,publication=pub,previous_history_sha256=snapshot,
                    reference_incoming_sha256=slot["reference_incoming_sha256"],
                    reference_iterations=slot["step"]["diagnostics"]["iterations"],
                    **comparison_row(new,reference),published=False)
                row["publication_passed"]=bool(pub["round_trip_exact"] and pub["max_published_kcl_a"]<1e-11
                    and pub["max_branch_equation_error_v"]<1e-14)
                rows.append(row)
                if not row["publication_passed"] or not row["reference_time_equal"]:
                    stop=dict(index=index,reason="publication-or-clock-failed",incoming=pack(old),dt_s=h);break
                old=new
            except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
                stop=dict(index=index,reason="solve-or-check-failed",incoming=pack(old),dt_s=h,error=str(exc),
                    incoming_history_unchanged=state_hash(old)==snapshot);break
            if len(rows)%500==0:
                print(json.dumps(dict(intervals=len(rows),time_s=old.time_s,
                    node_comparison_failures=sum(not r["node_gate_passed"] for r in rows))),flush=True)
    else:stop=dict(reason="fresh-DC-does-not-match-archived-DC",fresh=pack(initial),reference=case["initial"])
    if hashes(PATHS)!=before:raise ValueError("fixed-clock inputs changed during execution")
    complete=len(rows)==STEP_COUNT and stop is None and old.time_s==.003
    print(json.dumps(dict(complete=complete,attempted=attempts,solved=len(rows),final_time_s=old.time_s,
        stop=None if stop is None else {k:v for k,v in stop.items() if k not in ("incoming","fresh","reference")})),flush=True)
    return dict(schema="rf-d/bdf-compensated-fixed-clock/v1",source_sha256=before,environment=env,
        candidate_version=VERSION,initial=pack(initial),reference_initial=case["initial"],dc_diagnostics=dc,
        fresh_dc_matches_reference=initial_matches,reference_lineage_verified=True,
        reference_clock=[{k:v for k,v in s.items() if k!="step"} for s in clock],rows=rows,
        planned_intervals=STEP_COUNT,attempted_intervals=attempts,solved_intervals=len(rows),
        valid_intervals=sum(r["publication_passed"] and r["reference_time_equal"] for r in rows),
        reference_rejected_trials_not_executed=len(case["rejected"]),
        final=pack(old),complete=complete,stop=stop,
        fixed_clock_equivalence_passed=bool(complete and all(r["node_gate_passed"] and r["memory_gate_passed"] for r in rows)),
        node_comparison_gate_v=1e-8,memory_coordinate_gate_v=1e-8,charge_coordinate_scale_c_per_v=1e-12,
        fixed_kcl_gate_a=1e-11,fixed_correction_gate_v=1e-8,branch_equation_gate_v=1e-14,
        history_reset_count=0,trajectory_retimed=False,adaptive_controller_applied=False,
        original_solver_modified=False,original_reset_fd_gate_closed=False,previous_reports_modified=False,
        independent_full_spatial_oracle=False,physical_switching_admitted=False,
        temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        audio_admitted=False,deadline_admitted=False,diagnostic_only=True)


def save(report):
    storage=store(report,OUTPUT)
    rows=report["rows"]
    summary={k:v for k,v in report.items() if k not in ("rows","reference_clock","initial","reference_initial","final")}
    summary.update(storage=storage,final_time_s=report["final"]["time_s"],
        max_node_difference_v=max((r["max_node_difference_v"] for r in rows),default=None),
        max_memory_coordinate_difference_v=max((r["max_memory_coordinate_difference_v"] for r in rows),default=None),
        node_comparison_failures=sum(not r["node_gate_passed"] for r in rows),
        memory_comparison_failures=sum(not r["memory_gate_passed"] for r in rows),
        first_node_failure=next((r["index"] for r in rows if not r["node_gate_passed"]),None),
        first_memory_failure=next((r["index"] for r in rows if not r["memory_gate_passed"]),None),
        candidate_iterations=sum(r["diagnostics"]["iterations"] for r in rows),
        reference_iterations_for_solved_clock=sum(r["reference_iterations"] for r in rows),
        max_published_kcl_a=max((r["publication"]["max_published_kcl_a"] for r in rows),default=None),
        max_branch_equation_error_v=max((r["publication"]["max_branch_equation_error_v"] for r in rows),default=None),
        maximum_node_row=max(({k:r[k] for k in ("index","trial_index","step_index","maximum_difference_node","max_node_difference_v")}
            |dict(time_s=r["history"]["time_s"]) for r in rows),key=lambda r:r["max_node_difference_v"],default=None))
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
