"""Frozen 64-candidate static derivative/map audit; no new nonlinear solve."""
from decimal import Decimal
import gzip
import json
import math
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from circuit66_decimal_static import evaluate as decimal_evaluate
from circuit66_static_binary import MODES, prepare, evaluate as binary_evaluate
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_memory_windows import OUTPUT as WINDOWS
from loudness_latch_bdf_memory_transfer import stamps
from loudness_latch_bdf_static_precision import dynamic, derivative_metrics, solved, floats
from loudness_latch_bdf_static_precision_binary import SOURCE as STATIC, PATHS as OLD_PATHS
from loudness_latch_bdf_fd_sensitivity import map_metrics
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_windows.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_windows_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_VENTANAS_ESTATICAS_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,WINDOWS,STATIC,Path(__file__).resolve(),PROTOCOL)))


def candidate(old,step,network):
    virtual,c=network.effective_history(old,step["diagnostics"]["actual_dt_s"])
    x=np.array([math.fsum((a,b,d)) for a,b,d in zip(virtual.joint.node_v,
        virtual.node_low_v,step["diagnostics"]["increment_v"])])
    return virtual,c,x


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(WINDOWS.read_bytes()))
    graph=json.loads(gzip.decompress(STATIC.read_bytes()))["graph"]
    prepared=[prepare(graph,mode) for mode in MODES]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));windows=[]
    for window in source["windows"]:
        old=unpack(network,window["initial"]);rows=[]
        if len(window["reference"])!=16:raise ValueError("declared sixteen-interval window required")
        for index,(step,operator) in enumerate(zip(window["reference"],window["operators"])):
            if state_hash(old)!=step["previous_history_sha256"]:raise ValueError("reference history chain changed")
            new=unpack(network,step["history"]);virtual,c,x=candidate(old,step,network)
            original,sj=network.network.joint.evaluator(10.)(x)
            original=original[:66].copy();original[32]+=x[network.network.joint.out]/68000
            r80,j80=decimal_evaluate(graph,x[:66],80);r100,j100=decimal_evaluate(graph,x[:66],100)
            ref_r=np.array([float(v) for v in r80]);dyn=dynamic(network,virtual,x,c["effective_dt_s"])
            b,_,_=stamps(network,new,c["effective_dt_s"])
            def combined(j):
                out=sj.copy();out[:66,:66]=j;return out+dyn
            analytic=solved(combined(floats(j80)),b);precise=solved(combined(floats(j100)),b)
            row=dict(index=index,time_s=new.time_s,actual_dt_s=step["diagnostics"]["actual_dt_s"],
                previous_history_sha256=state_hash(old),coefficients=c,node_candidate_v=x.tolist(),memory_rhs_s=b.tolist(),
                decimal80_audio_residual_a=[str(v) for v in r80],decimal80_audio_jacobian_s=[[str(v) for v in line] for line in j80],
                original_static_discrepancy_a=float(np.max(abs(original-ref_r))),
                decimal80_100_rounded_residual_equal=np.array_equal(ref_r,[float(v) for v in r100]),
                decimal80_100_rounded_jacobian_equal=np.array_equal(floats(j80),floats(j100)),
                analytic=analytic,decimal100=precise,binary=[])
            row["original_static_gate_passed"]=row["original_static_discrepancy_a"]<1e-11
            if analytic["passed"]:
                ax=np.array(analytic["node_map"])
                row["original_mixed_map"]=map_metrics(ax,np.array(operator["node_map"]))
                if precise["passed"]:row["decimal80_100_map"]=map_metrics(ax,np.array(precise["node_map"]))
            for g in prepared:
                r,j=binary_evaluate(g,x[:66]);result=dict(mode=g["reciprocal_mode"],
                    audio_residual_a=r.tolist(),audio_jacobian_s=j.tolist(),
                    static_residual_discrepancy_a=float(np.max(abs(r-ref_r))),
                    derivative_comparison=derivative_metrics(j80,[[Decimal.from_float(float(v)) for v in line] for line in j]),
                    solve=solved(combined(j),b))
                result["static_residual_gate_passed"]=result["static_residual_discrepancy_a"]<1e-11
                if analytic["passed"] and result["solve"]["passed"]:
                    result["map_comparison"]=map_metrics(ax,np.array(result["solve"]["node_map"]))
                    result["map_gate_passed"]=result["map_comparison"]["node_map_max_scaled_difference"]<1e-8
                row["binary"].append(result)
            rows.append(row);old=new
        windows.append(dict(name=window["name"],initial=window["initial"],rows=rows))
        print(json.dumps(dict(window=window["name"],intervals=len(rows),map_passes={mode:sum(
            next(v for v in row["binary"] if v["mode"]==mode).get("map_gate_passed",False) for row in rows) for mode in MODES})),flush=True)
    if hashes(PATHS)!=before:raise ValueError("static-window inputs changed during execution")
    return dict(schema="rf-d/bdf-static-precision-windows/v1",source_sha256=before,environment=env,
        graph=graph,prepared_graphs=prepared,windows=windows,intervals_per_window=16,nonlinear_steps_new=0,
        static_residual_gate_a=1e-11,map_gate=1e-8,backward_gate=1e-10,
        derivative_absolute_gate_s=1e-30,derivative_relative_gate=1e-8,
        original_solver_modified=False,trajectory_retimed=False,history_reset_count=0,
        original_reset_fd_gate_closed=False,previous_reports_modified=False,independent_full_spatial_oracle=False,
        physical_switching_admitted=False,temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        audio_admitted=False,deadline_admitted=False,diagnostic_only=True)


def compact_solve(s):return {k:v for k,v in s.items() if k not in ("jacobian_s","node_map","exact_solve")}


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ("graph","prepared_graphs","windows")}
    summary.update(storage=storage,windows=[dict(name=w["name"],rows=[
        {k:v for k,v in r.items() if k not in ("node_candidate_v","memory_rhs_s","decimal80_audio_residual_a",
            "decimal80_audio_jacobian_s","analytic","decimal100","binary")}
        |dict(analytic=compact_solve(r["analytic"]),decimal100=compact_solve(r["decimal100"]),binary=[
            {k:v for k,v in v.items() if k not in ("audio_residual_a","audio_jacobian_s","solve")}
            |dict(solve=compact_solve(v["solve"])) for v in r["binary"]]) for r in w["rows"]]) for w in report["windows"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
