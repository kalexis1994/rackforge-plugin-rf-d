"""Predeclared ordinary and compensated binary64 static stamp contrasts."""
from decimal import Decimal
import gzip
import json
from pathlib import Path
import numpy as np
from circuit66_static_binary import MODES,prepare,evaluate
from loudness_latch_bdf_static_precision import OUTPUT as SOURCE,PATHS as SOURCE_PATHS,derivative_metrics,solved
from loudness_latch_bdf_fd_sensitivity import map_metrics
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_static_precision import dynamic

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_binary.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_binary_summary.json"
PATHS=tuple(dict.fromkeys((*SOURCE_PATHS,SOURCE,Path(__file__).resolve(),
    ROOT/"tools/circuit66_static_binary.py",ROOT/"docs/BIESTABLE_SELLOS_BINARIOS_PROTOCOLO.md")))


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(SOURCE.read_bytes()))
    graphs=[prepare(source["graph"],mode) for mode in MODES];cases=[]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"))
    for case in source["cases"]:
        row=dict(window=case["window"],node_candidate_v=case["node_candidate_v"],rows=[])
        decimal=[[v for v in r] for r in case["decimal80_audio_static_jacobian_s"]]
        reference_j=[[Decimal(v) for v in r] for r in decimal]
        reference_r=np.array([float(Decimal(v)) for v in case["decimal80_audio_static_residual_a"]])
        reference_x=np.array(case["analytic"]["node_map"])
        b=np.array(case["memory_rhs_s"])
        old=unpack(network,case["initial"]);step=case["reference_step"]
        virtual,c=network.effective_history(old,step["diagnostics"]["actual_dt_s"])
        _,static94=network.network.joint.evaluator(10.)(np.array(case["node_candidate_v"]))
        dyn=dynamic(network,virtual,np.array(case["node_candidate_v"]),c["effective_dt_s"])
        row["coefficients"]=c
        for graph in graphs:
            r,j=evaluate(graph,case["node_candidate_v"][:66])
            result=dict(mode=graph["reciprocal_mode"],audio_residual_a=r.tolist(),audio_jacobian_s=j.tolist(),
                static_residual_discrepancy_a=float(np.max(abs(r-reference_r))),
                static_residual_gate_passed=bool(np.max(abs(r-reference_r))<1e-11),
                derivative_comparison=derivative_metrics(reference_j,[[Decimal.from_float(float(v)) for v in line] for line in j]),
                differing_audio_jacobian_components=int(np.count_nonzero(j!=np.array([[float(v) for v in line] for line in reference_j]))))
            # Rebuild the shared dynamic stamps without subtracting large terms.
            sj=static94.copy();sj[:66,:66]=j;combined=sj+dyn
            result["solve"]=solved(combined,b)
            if result["solve"]["passed"]:
                x=np.array(result["solve"]["node_map"]);comparison=map_metrics(reference_x,x)
                result.update(map_comparison=comparison,map_gate_passed=comparison["node_map_max_scaled_difference"]<1e-8)
                gamma=c["gamma"]
                comparisons=[]
                for d in case["directions"]:
                    central=np.array(d["comparisons"]["decimal-analytic"]["central_v"])
                    kick=np.zeros(25);kick[d["memory"]]=d["amplitude_v"]
                    predicted=x@((1+gamma)*kick)
                    scaled=abs(central-predicted)/(1e-8+1e-3*abs(predicted))
                    comparisons.append(dict(memory=d["memory"],amplitude_v=d["amplitude_v"],central_v=central.tolist(),
                        predicted_v=predicted.tolist(),maximum_scaled_error=float(np.max(scaled)),passed=bool(np.max(scaled)<1)))
                result["reused_direction_comparisons"]=comparisons
            row["rows"].append(result)
            print(json.dumps(dict(window=case["window"],mode=result["mode"],
                static_residual_gate_passed=result["static_residual_gate_passed"],derivative_comparison=result["derivative_comparison"],
                differing_components=result["differing_audio_jacobian_components"],map_comparison=result.get("map_comparison"),
                map_gate_passed=result.get("map_gate_passed"))),flush=True)
        cases.append(row)
    if hashes(PATHS)!=before:raise ValueError("binary static inputs changed during execution")
    return dict(schema="rf-d/bdf-static-binary/v1",environment=env,source_sha256=before,
        prepared_graphs=graphs,cases=cases,modes=MODES,static_residual_gate_a=1e-11,backward_gate=1e-10,map_gate=1e-8,
        nonlinear_steps_new=0,reused_nonlinear_steps=48,reused_central_comparisons=24,
        original_solver_modified=False,original_reset_fd_gate_closed=False,previous_reports_modified=False,
        physical_switching_admitted=False,temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        audio_admitted=False,deadline_admitted=False,diagnostic_only=True)


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ("prepared_graphs","cases")}
    summary.update(storage=storage,cases=[dict(window=case["window"],rows=[
        {k:v for k,v in row.items() if k not in ("audio_residual_a","audio_jacobian_s","solve","reused_direction_comparisons")}
        |dict(solve={k:v for k,v in row["solve"].items() if k not in ("jacobian_s","node_map","exact_solve")},
            reused_direction_comparisons=[{k:v for k,v in d.items() if k not in ("central_v","predicted_v")}
                for d in row.get("reused_direction_comparisons",[])]) for row in case["rows"]]) for case in report["cases"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
