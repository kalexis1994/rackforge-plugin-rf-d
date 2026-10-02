"""Predeclared original-residual equality and fixed-clock candidate continuations."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork,VERSION
from loudness_latch_bdf_static_precision_windows import OUTPUT as AUDIT,PATHS as OLD_PATHS,WINDOWS,candidate
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_memory_transfer import node_difference,memory_difference
from loudness_latch_bdf_survey import state_hash
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_continuation.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_continuation_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_INTEGRADOR_COMPENSADO_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,AUDIT,Path(__file__).resolve(),PROTOCOL,
    ROOT/"tools/loudness_latch_bdf_static_precision_integrator.py")))


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(WINDOWS.read_bytes()));audit=json.loads(gzip.decompress(AUDIT.read_bytes()))
    params=model_parameters(1,"finite_transit")
    original=BdfNetwork(200,params);variant=CompensatedBdfNetwork(200,params)
    windows=[]
    for base,static in zip(source["windows"],audit["windows"]):
        old=unpack(original,base["initial"]);checks=[]
        if len(base["reference"])!=16 or base["name"]!=static["name"]:raise ValueError("declared window mismatch")
        for index,(step,stamp) in enumerate(zip(base["reference"],static["rows"])):
            virtual,c,_=candidate(old,step,original);delta=np.array(step["diagnostics"]["increment_v"])
            a=original.network.increment_evaluator(10.,virtual,c["effective_dt_s"])
            b=variant.network.increment_evaluator(10.,virtual,c["effective_dt_s"])
            pairs=[]
            for node,shift in ((None,0.),(27,1e-6),(27,-1e-6),(66,1e-6),(66,-1e-6)):
                d=delta.copy()
                if node is not None:d[node]+=shift
                ar,_=a(d,False);br,_=b(d,False)
                pairs.append(dict(node=node,shift_v=shift,original_residual_a=ar.tolist(),
                    candidate_residual_a=br.tolist(),bits_equal=ar.tobytes()==br.tobytes()))
            _,j=b(delta)
            row=dict(index=index,previous_history_sha256=state_hash(old),pairs=pairs,
                jacobian_equal_to_compensated_audit=j.tobytes()==np.array(stamp["binary"][1]["solve"]["jacobian_s"]).tobytes())
            if index==0:
                _,aj=a(delta,use_fd=True);_,bj=b(delta,use_fd=True)
                row["full_residual_fd_bits_equal"]=aj.tobytes()==bj.tobytes()
            checks.append(row);old=unpack(original,step["history"])
        eligible=all(all(p["bits_equal"] for p in r["pairs"]) and r["jacobian_equal_to_compensated_audit"]
            and r.get("full_residual_fd_bits_equal",True) for r in checks)
        old=unpack(variant,base["initial"]);rows=[];stop=None;attempts=0
        if eligible:
            for index,step in enumerate(base["reference"]):
                h=step["diagnostics"]["actual_dt_s"];snapshot=state_hash(old);attempts+=1
                try:
                    new,d=variant.advance(old,10.,h)
                    if state_hash(old)!=snapshot:raise ValueError("candidate mutated its incoming histories")
                    pub=publication_check(variant,old,new,h,d)
                    reference=unpack(variant,step["history"])
                    nodes=node_difference(new.current,reference.current);memory=memory_difference(new.current,reference.current)
                    row=dict(index=index,history=pack(new),diagnostics=d,publication=pub,
                        previous_history_sha256=snapshot,node_difference_v=nodes.tolist(),memory_difference_v=memory.tolist(),
                        max_node_difference_v=float(np.max(abs(nodes))),max_memory_coordinate_difference_v=float(np.max(abs(memory))),
                        reference_iterations=step["diagnostics"]["iterations"],reference_time_equal=new.time_s==reference.time_s,
                        node_gate_passed=bool(np.max(abs(nodes))<1e-8),memory_gate_passed=bool(np.max(abs(memory))<1e-8),published=False)
                    row["publication_passed"]=bool(pub["round_trip_exact"] and pub["max_published_kcl_a"]<1e-11
                        and pub["max_branch_equation_error_v"]<1e-14)
                    rows.append(row)
                    if not row["publication_passed"]:
                        stop=dict(index=index,reason="publication-failed",incoming=pack(old),dt_s=h);break
                    old=new
                except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
                    stop=dict(index=index,reason="solve-or-check-failed",incoming=pack(old),dt_s=h,error=str(exc),
                        incoming_history_unchanged=state_hash(old)==snapshot);break
        else:stop=dict(reason="residual-or-jacobian-preflight-failed")
        window=dict(name=base["name"],initial=base["initial"],preflight=checks,preflight_passed=eligible,
            rows=rows,attempted_intervals=attempts,complete=len(rows)==16 and stop is None,stop=stop,final=pack(old))
        windows.append(window)
        print(json.dumps(dict(window=base["name"],preflight_passed=eligible,complete=window["complete"],
            intervals=len(rows),stop=stop,max_node_difference_v=max((r["max_node_difference_v"] for r in rows),default=None))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("candidate continuation inputs changed during execution")
    return dict(schema="rf-d/bdf-static-compensated-continuation/v1",source_sha256=before,environment=env,
        candidate_version=VERSION,windows=windows,planned_intervals=64,planned_residual_pairs=320,
        node_comparison_gate_v=1e-8,memory_coordinate_gate_v=1e-8,charge_coordinate_scale_c_per_v=1e-12,
        fixed_kcl_gate_a=1e-11,fixed_correction_gate_v=1e-8,branch_equation_gate_v=1e-14,
        history_reset_count=0,trajectory_retimed=False,adaptive_controller_applied=False,
        original_solver_modified=False,original_reset_fd_gate_closed=False,previous_reports_modified=False,
        physical_switching_admitted=False,temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        full_dc_trajectory_admitted=False,audio_admitted=False,deadline_admitted=False,diagnostic_only=True)


def save(report):
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k!="windows"}
    summary.update(storage=storage,windows=[dict(name=w["name"],preflight_passed=w["preflight_passed"],
        residual_pairs=sum(len(r["pairs"]) for r in w["preflight"]),attempted_intervals=w["attempted_intervals"],
        complete=w["complete"],stop=w["stop"],rows=[{k:v for k,v in r.items() if k not in (
            "history","publication","diagnostics","node_difference_v","memory_difference_v")}
            |dict(iterations=r["diagnostics"]["iterations"],max_kcl_a=r["diagnostics"]["max_kcl_a"],
                correction_v=r["diagnostics"]["correction_v"],max_published_kcl_a=r["publication"]["max_published_kcl_a"],
                max_branch_equation_error_v=r["publication"]["max_branch_equation_error_v"]) for r in w["rows"]]) for w in report["windows"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
