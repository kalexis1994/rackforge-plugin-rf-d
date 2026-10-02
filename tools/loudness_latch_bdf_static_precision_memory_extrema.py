"""Frozen C7 and singular-direction finite nonlinear memory injections."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork,VERSION
from loudness_latch_bdf_static_precision_memory_basis import OUTPUT as BASIS,PATHS as OLD_PATHS
from loudness_latch_bdf_static_precision_memory_long import (OUTPUT as SOURCE,STEP_COUNT,
    continuation,central_metrics,ABSOLUTE_GATE_V,RELATIVE_GATE)
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_memory_transfer import CHARGE_SCALE_C_PER_V
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_extrema.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_extrema_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_DIRECCIONES_EXTREMAS_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,BASIS,SOURCE,Path(__file__).resolve(),PROTOCOL)))
KICK_V=1e-6
AMPLITUDES=(1.,.5,.25)


def directions(network,window):
    c7=18+next(k for k,(ref,_,_,_) in enumerate(network.network.joint.contour.caps) if ref=="C7")
    current=np.zeros(50);current[c7]=1.
    common=current.copy();common[c7+25]=1.;common/=np.sqrt(2.)
    differential=current.copy();differential[c7+25]=-1.;differential/=np.sqrt(2.)
    out=[dict(name=name,unit_direction=v,selection=None) for name,v in (
        ("C7-current",current),("C7-common",common),("C7-differential",differential))]
    for key in ("node_basis","memory_basis","double_history_basis"):
        index=max(range(len(window["rows"])),key=lambda i:window["rows"][i][key]["spectral_norm"])
        row=window["rows"][index];v=np.array(row[key]["maximum_right_direction"])
        if v.shape!=(50,) or not np.isfinite(v).all() or abs(np.linalg.norm(v)-1)>1e-12:
            raise ValueError("frozen singular direction is not normalized")
        if v[int(np.argmax(abs(v)))]<0:raise ValueError("frozen direction sign changed")
        out.append(dict(name="maximum-"+key,unit_direction=v,
            selection=dict(index=index,time_s=row["time_s"],spectral_norm=row[key]["spectral_norm"])))
    return out


def response_metrics(cases):
    rows=[]
    for plus,minus in zip(cases[0]["steps"],cases[1]["steps"]):
        row=dict(time_s=plus["history"]["time_s"])
        for name in ("node","memory"):
            actual=[np.array(s[name+"_difference_v"]) for s in (plus,minus)]
            predicted=[np.array(s["predicted_"+name+"_difference_v"]) for s in (plus,minus)]
            errors=[abs(a-p) for a,p in zip(actual,predicted)]
            scaled=[e/(ABSOLUTE_GATE_V+RELATIVE_GATE*abs(p)) for e,p in zip(errors,predicted)]
            bias=(actual[0]+actual[1])/2
            row.update({"maximum_"+name+"_one_sided_error_v":[float(np.max(e)) for e in errors],
                "maximum_scaled_"+name+"_one_sided_error":[float(np.max(s)) for s in scaled],
                "maximum_"+name+"_even_response_v":float(np.max(abs(bias))),
                "even_"+name+"_response_v":bias.tolist()})
        rows.append(row)
    complete=all(c["complete"] for c in cases)
    peaks={name:max((max(r["maximum_scaled_"+name+"_one_sided_error"]) for r in rows),default=None)
           for name in ("node","memory")}
    return dict(rows=rows,complete=complete,maximum_scaled_node_one_sided_error=peaks["node"],
        maximum_scaled_memory_one_sided_error=peaks["memory"],
        passed=bool(complete and all(v<1 for v in peaks.values())))


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(SOURCE.read_bytes()))
    basis=json.loads(gzip.decompress(BASIS.read_bytes()))
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"));windows=[]
    for wi,(base,bw) in enumerate(zip(source["windows"],basis["windows"])):
        if base["name"]!=bw["name"] or len(base["reference"])!=STEP_COUNT or len(bw["rows"])!=STEP_COUNT:
            raise ValueError("frozen windows mismatch")
        initial=unpack(network,base["initial"])
        operators=[dict(op,node_map=np.array(op["node_map"]),memory_map=np.array(op["memory_map"])) for op in base["operators"]]
        experiments=[]
        for selected in directions(network,bw):
            v=selected["unit_direction"];current=KICK_V*v[:25];previous=KICK_V*v[25:];levels=[]
            for amplitude in AMPLITUDES:
                cases=[continuation(network,initial,base["reference"],operators,current,previous,amplitude,sign) for sign in (1,-1)]
                levels.append(dict(amplitude=amplitude,cases=cases,central_comparison=central_metrics(*cases),
                    one_sided_comparison=response_metrics(cases)))
            experiments.append(dict(direction=selected["name"],selection=selected["selection"],unit_direction=v.tolist(),
                current_direction_v=current.tolist(),previous_direction_v=previous.tolist(),levels=levels))
        window=dict(name=base["name"],source_window_index=wi,initial=base["initial"],
            reference_intervals=STEP_COUNT,reference_end_s=base["end_s"],experiments=experiments)
        windows.append(window)
        print(json.dumps(dict(window=base["name"],nonlinear_intervals=sum(len(c["steps"]) for e in experiments for l in e["levels"] for c in l["cases"]),
            central_passes=sum(l["central_comparison"]["passed"] for e in experiments for l in e["levels"]),
            one_sided_passes=sum(l["one_sided_comparison"]["passed"] for e in experiments for l in e["levels"]))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("extrema experiment inputs changed")
    return dict(schema="rf-d/bdf-static-precision-memory-extrema/v1",source_sha256=before,environment=env,
        integrator_version=VERSION,windows=windows,amplitudes=AMPLITUDES,kick_double_history_euclidean_v=KICK_V,
        charge_coordinate_scale_c_per_v=CHARGE_SCALE_C_PER_V,intervals_per_window=STEP_COUNT,
        absolute_linearization_gate_v=ABSOLUTE_GATE_V,relative_linearization_gate=RELATIVE_GATE,
        initial_memory_injections_are_accepted_states=False,reference_clock_preserved=True,history_reset_count=0,
        local_adaptive_error_gate_applied=False,new_spatial_map_solves=0,
        diagnostic_only=True,full_nonlinear_direction_validation=False,temporal_error_bound_admitted=False,
        temporal_refinement_admitted=False,physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation="selected finite double-memory injections; singular directions chosen from a frozen prior report; no exact temporal defect or global nonlinear bound")


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report["windows"]:
        cases=[c for e in w["experiments"] for l in e["levels"] for c in l["cases"]]
        steps=[s for c in cases for s in c["steps"]];experiments=[]
        for e in w["experiments"]:
            levels=[]
            for l in e["levels"]:
                central=l["central_comparison"];one=l["one_sided_comparison"]
                levels.append(dict(amplitude=l["amplitude"],
                    central={k:v for k,v in central.items() if k!="rows"},
                    one_sided={k:v for k,v in one.items() if k!="rows"},
                    maximum_node_response_v=max((r["maximum_node_response_v"] for r in central["rows"]),default=None),
                    maximum_node_central_error_v=max((r["maximum_node_linearization_error_v"] for r in central["rows"]),default=None),
                    maximum_memory_central_error_v=max((r["maximum_memory_linearization_error_v"] for r in central["rows"]),default=None),
                    maximum_node_even_response_v=max((r["maximum_node_even_response_v"] for r in one["rows"]),default=None),
                    maximum_memory_even_response_v=max((r["maximum_memory_even_response_v"] for r in one["rows"]),default=None),
                    stops=[c["stop"] for c in l["cases"]]))
            experiments.append(dict(direction=e["direction"],selection=e["selection"],levels=levels))
        windows.append(dict(name=w["name"],anchor_time_s=w["initial"]["time_s"],reference_end_s=w["reference_end_s"],
            nonlinear_intervals=len(steps),nonlinear_cases=len(cases),nonlinear_complete=sum(c["complete"] for c in cases),
            central_passes=sum(l["central_comparison"]["passed"] for e in w["experiments"] for l in e["levels"]),
            one_sided_passes=sum(l["one_sided_comparison"]["passed"] for e in w["experiments"] for l in e["levels"]),
            maximum_published_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in steps),default=None),experiments=experiments))
    summary={k:v for k,v in report.items() if k!="windows"}|dict(storage=storage,windows=windows)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
