"""Reserved fresh nonlinear responses against frozen circuit-derived curvature."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_static_precision_memory_quadratic import OUTPUT as COEFFICIENTS,PATHS as OLD_PATHS,SOURCE
from loudness_latch_bdf_static_precision_memory_long import continuation,central_metrics
from loudness_latch_bdf_static_precision_memory_extrema import response_metrics
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_quadratic_response.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_quadratic_response_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_RESPUESTA_CUADRATICA_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,COEFFICIENTS,Path(__file__).resolve(),PROTOCOL)))
AMPLITUDES=(.75,.375,.1875)
ABSOLUTE_GATE_V=1e-8
RELATIVE_GATE=1e-3


def comparisons(cases):
    rows=[]
    for plus,minus in zip(cases[0]["steps"],cases[1]["steps"]):
        row=dict(time_s=plus["history"]["time_s"])
        for name in ("node","memory"):
            actual=[np.array(s[name+"_difference_v"]) for s in (plus,minus)]
            pred=[np.array(s["quadratic_"+name+"_prediction_v"]) for s in (plus,minus)]
            even=(actual[0]+actual[1])/2
            even_pred=np.array(plus["quadratic_even_"+name+"_prediction_v"])
            errors=[abs(a-p) for a,p in zip(actual,pred)]
            scaled=[e/(ABSOLUTE_GATE_V+RELATIVE_GATE*abs(p)) for e,p in zip(errors,pred)]
            even_error=abs(even-even_pred);even_scaled=even_error/(ABSOLUTE_GATE_V+RELATIVE_GATE*abs(even_pred))
            row.update({"maximum_"+name+"_individual_error_v":[float(np.max(e)) for e in errors],
                "maximum_scaled_"+name+"_individual_error":[float(np.max(s)) for s in scaled],
                "maximum_"+name+"_even_error_v":float(np.max(even_error)),
                "maximum_scaled_"+name+"_even_error":float(np.max(even_scaled))})
        rows.append(row)
    complete=all(c["complete"] for c in cases)
    peaks={"maximum_scaled_"+name+"_individual_error":max(
        (max(r["maximum_scaled_"+name+"_individual_error"]) for r in rows),default=None) for name in ("node","memory")}
    evens={"maximum_scaled_"+name+"_even_error":max(
        (r["maximum_scaled_"+name+"_even_error"] for r in rows),default=None) for name in ("node","memory")}
    return dict(rows=rows,complete=complete,**peaks,**evens,
        individual_passed=bool(complete and all(v<1 for v in peaks.values())),
        even_passed=bool(complete and all(v<1 for v in evens.values())))


def generate():
    before=hashes(PATHS);env=environment()
    coefficient=json.loads(gzip.decompress(COEFFICIENTS.read_bytes()))
    if coefficient["reserved_response_amplitudes"]!=list(AMPLITUDES):raise ValueError("reserved amplitudes changed")
    source=json.loads(gzip.decompress(SOURCE.read_bytes()))
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"));windows=[]
    for base,coef in zip(source["windows"],coefficient["windows"]):
        if base["name"]!=coef["name"] or not coef["complete"]:raise ValueError("complete frozen coefficient window required")
        initial=unpack(network,base["initial"])
        ops=[dict(op,node_map=np.array(op["node_map"]),memory_map=np.array(op["memory_map"])) for op in base["operators"]]
        experiments=[]
        for k,definition in enumerate(coef["definitions"]):
            levels=[];current=np.array(definition["current_direction_v"]);previous=np.array(definition["previous_direction_v"])
            for amplitude in AMPLITUDES:
                cases=[continuation(network,initial,base["reference"],ops,current,previous,amplitude,sign) for sign in (1,-1)]
                for case in cases:
                    for step,row in zip(case["steps"],coef["rows"]):
                        for name in ("node","memory"):
                            even=amplitude*amplitude/2*np.array(row[name+"_second_v"])[:,k]
                            linear=np.array(step["predicted_"+name+"_difference_v"])
                            step["quadratic_"+name+"_prediction_v"]=(linear+even).tolist()
                            step["quadratic_even_"+name+"_prediction_v"]=even.tolist()
                levels.append(dict(amplitude=amplitude,cases=cases,linear_central=central_metrics(*cases),
                    linear_individual=response_metrics(cases),quadratic=comparisons(cases)))
            experiments.append(dict(definition=definition,levels=levels))
        windows.append(dict(name=base["name"],initial=base["initial"],reference_end_s=base["end_s"],experiments=experiments))
        print(json.dumps(dict(window=base["name"],linear_individual_passes=sum(l["linear_individual"]["passed"] for e in experiments for l in e["levels"]),
            quadratic_individual_passes=sum(l["quadratic"]["individual_passed"] for e in experiments for l in e["levels"]),
            quadratic_even_passes=sum(l["quadratic"]["even_passed"] for e in experiments for l in e["levels"]))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("reserved response inputs changed")
    return dict(schema="rf-d/bdf-static-precision-memory-quadratic-response/v1",source_sha256=before,environment=env,
        windows=windows,amplitudes=AMPLITUDES,absolute_response_gate_v=ABSOLUTE_GATE_V,relative_response_gate=RELATIVE_GATE,
        coefficients_fitted_to_responses=False,reserved_amplitudes_preserved=True,new_coefficient_solves=0,
        initial_memory_injections_are_accepted_states=False,local_adaptive_error_gate_applied=False,
        history_reset_count=0,previous_failures_modified=False,diagnostic_only=True,
        global_nonlinear_remainder_bound_admitted=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation="fresh finite responses at reserved amplitudes on frozen windows; conditional circuit coefficients and shared nonlinear solver; no global error or vintage fidelity claim")


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report["windows"]:
        cases=[c for e in w["experiments"] for l in e["levels"] for c in l["cases"]]
        steps=[s for c in cases for s in c["steps"]];experiments=[]
        for e in w["experiments"]:
            levels=[]
            for l in e["levels"]:
                q=l["quadratic"]
                levels.append(dict(amplitude=l["amplitude"],
                    linear_individual={k:v for k,v in l["linear_individual"].items() if k!="rows"},
                    quadratic={k:v for k,v in q.items() if k!="rows"},
                    maximum_quadratic_node_error_v=max((max(r["maximum_node_individual_error_v"]) for r in q["rows"]),default=None),
                    maximum_quadratic_memory_error_v=max((max(r["maximum_memory_individual_error_v"]) for r in q["rows"]),default=None),
                    maximum_quadratic_node_even_error_v=max((r["maximum_node_even_error_v"] for r in q["rows"]),default=None),
                    stops=[c["stop"] for c in l["cases"]]))
            experiments.append(dict(direction=e["definition"]["direction"],levels=levels))
        windows.append(dict(name=w["name"],nonlinear_cases=len(cases),nonlinear_complete=sum(c["complete"] for c in cases),nonlinear_intervals=len(steps),
            linear_individual_passes=sum(l["linear_individual"]["passed"] for e in w["experiments"] for l in e["levels"]),
            quadratic_individual_passes=sum(l["quadratic"]["individual_passed"] for e in w["experiments"] for l in e["levels"]),
            quadratic_even_passes=sum(l["quadratic"]["even_passed"] for e in w["experiments"] for l in e["levels"]),
            maximum_published_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in steps),default=None),experiments=experiments))
    summary={k:v for k,v in report.items() if k!="windows"}|dict(storage=storage,windows=windows)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
