"""Supplement retained FD failures with an exact solve of identical coefficients."""
import gzip
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_memory_transfer import stamps
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_rational_solve import solve
from loudness_latch_bdf_memory_windows import OUTPUT as WINDOWS,PATHS as WINDOW_PATHS
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_memory_fd_audit.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_memory_fd_audit_summary.json"
BACKWARD_GATE=1e-10
MAP_GATE=1e-8
PATHS=tuple(dict.fromkeys((*WINDOW_PATHS,WINDOWS,Path(__file__).resolve(),
                         ROOT/"tools/loudness_latch_bdf_rational_solve.py")))


def generate():
    before=hashes(PATHS);env=environment()
    report=json.loads(gzip.decompress(WINDOWS.read_bytes()))
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));rows=[]
    for window in report["windows"]:
        old=unpack(network,window["initial"]);step=window["reference"][0]
        new=unpack(network,step["history"]);d=step["diagnostics"]
        virtual,c=network.effective_history(old,d["actual_dt_s"])
        evaluate=network.network.increment_evaluator(10.,virtual,c["effective_dt_s"])
        _,j=evaluate(np.array(d["increment_v"]),use_fd=True)
        b,_,_=stamps(network,new,c["effective_dt_s"])
        row=dict(window=window["name"],old=window["initial"],reference_step=step,
            original_fd_diagnostic={k:v for k,v in window["operators"][0].items() if k.startswith("fd_")},
            fd_jacobian_s=j.tolist(),memory_rhs_s=b.tolist(),passed=False,
            binary_and_decimal_backward_gate=BACKWARD_GATE,scaled_map_gate=MAP_GATE)
        started=perf_counter()
        try:
            x,audit=solve(j,b);_,errors=backward_errors(j,b,x)
            mixed=np.array(window["operators"][0]["node_map"])
            difference=float(np.max(np.abs(mixed-x)/(1+np.abs(mixed))))
            row.update(node_map=x.tolist(),exact_solve=audit,backward_errors=errors,
                node_map_max_scaled_difference=difference,
                passed=max(errors.values())<BACKWARD_GATE and difference<MAP_GATE)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            row.update(error=str(exc))
        row["offline_solve_wall_s"]=perf_counter()-started
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k in ("window","passed","error","backward_errors","node_map_max_scaled_difference","offline_solve_wall_s")}),flush=True)
    if hashes(PATHS)!=before:raise ValueError("FD audit inputs changed during execution")
    return dict(schema="rf-d/bdf-memory-fd-audit/v1",source_sha256=before,environment=env,rows=rows,
        binary_and_decimal_backward_gate=BACKWARD_GATE,scaled_map_gate=MAP_GATE,
        previous_reports_modified=False,original_fd_failures_retained=True,diagnostic_only=True,
        temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="exact arithmetic solves the rounded FD matrix, not exact circuit derivatives; same spatial laws; finite first-interval probes only")


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!="rows"}|dict(storage=storage,
        rows=[{k:v for k,v in row.items() if k not in ("old","reference_step","fd_jacobian_s","memory_rhs_s","node_map")} for row in report["rows"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":save(generate())
