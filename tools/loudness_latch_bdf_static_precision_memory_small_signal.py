"""Zero-injection controls and separately declared smaller attack injections."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_static_precision_memory_extrema import (OUTPUT as EXTREMA,PATHS as OLD_PATHS,
    SOURCE,KICK_V,continuation,central_metrics,response_metrics)
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_small_signal.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_small_signal_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_PEQUENA_SENAL_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,EXTREMA,Path(__file__).resolve(),PROTOCOL)))
AMPLITUDES=(1/8,1/16,1/32,1/64)
ZERO_GATE_V=1e-8


def operators(base):
    return [dict(op,node_map=np.array(op["node_map"]),memory_map=np.array(op["memory_map"])) for op in base["operators"]]


def zero_comparison(case,base):
    rows=[]
    for row,ref in zip(case["steps"],base["reference"]):
        n=float(np.max(abs(np.array(row["node_difference_v"]))));m=float(np.max(abs(np.array(row["memory_difference_v"]))))
        rows.append(dict(time_s=row["history"]["time_s"],maximum_node_difference_v=n,
            maximum_memory_difference_v=m,canonical_history_equal=canonical(row["history"])==canonical(ref["history"]),
            passed=n<ZERO_GATE_V and m<ZERO_GATE_V))
    return dict(rows=rows,complete=case["complete"],all_canonical_histories_equal=all(r["canonical_history_equal"] for r in rows),
        maximum_node_difference_v=max((r["maximum_node_difference_v"] for r in rows),default=None),
        maximum_memory_difference_v=max((r["maximum_memory_difference_v"] for r in rows),default=None),
        passed=bool(case["complete"] and all(r["passed"] for r in rows)))


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(SOURCE.read_bytes()))
    extrema=json.loads(gzip.decompress(EXTREMA.read_bytes()))
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"));controls=[]
    for i,base in enumerate(source["windows"]):
        initial=unpack(network,base["initial"]);z=np.zeros(25)
        case=continuation(network,initial,base["reference"],operators(base),z,z,0.,1)
        controls.append(dict(name=base["name"],source_window_index=i,case=case,comparison=zero_comparison(case,base)))
    ai=next(i for i,w in enumerate(source["windows"]) if w["name"]=="attack")
    base=source["windows"][ai];old=extrema["windows"][ai]
    if old["name"]!="attack":raise ValueError("frozen attack index mismatch")
    initial=unpack(network,base["initial"]);ops=operators(base);experiments=[]
    for direction in old["experiments"]:
        current=np.array(direction["current_direction_v"]);previous=np.array(direction["previous_direction_v"])
        levels=[]
        for amplitude in AMPLITUDES:
            cases=[continuation(network,initial,base["reference"],ops,current,previous,amplitude,sign) for sign in (1,-1)]
            levels.append(dict(amplitude=amplitude,cases=cases,central_comparison=central_metrics(*cases),
                one_sided_comparison=response_metrics(cases)))
        experiments.append({k:direction[k] for k in ("direction","selection","unit_direction","current_direction_v","previous_direction_v")}|dict(levels=levels))
        print(json.dumps(dict(direction=direction["direction"],central_passes=sum(l["central_comparison"]["passed"] for l in levels),
            one_sided_passes=sum(l["one_sided_comparison"]["passed"] for l in levels))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("small-signal experiment inputs changed")
    return dict(schema="rf-d/bdf-static-precision-memory-small-signal/v1",environment=env,source_sha256=before,
        controls=controls,attack=dict(source_window_index=ai,initial=base["initial"],end_s=base["end_s"],experiments=experiments),
        amplitudes=AMPLITUDES,kick_double_history_euclidean_v=KICK_V,zero_coordinate_gate_v=ZERO_GATE_V,
        absolute_linearization_gate_v=1e-8,relative_linearization_gate=1e-3,intervals_per_window=64,
        original_18_attack_one_sided_failures_resolved=False,amplitude_selected_for_integrator=False,
        initial_memory_injections_are_accepted_states=False,local_adaptive_error_gate_applied=False,
        nonlinear_ball_bound_admitted=False,temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,diagnostic_only=True,
        limitation="four frozen zero controls and six finite attack directions at four smaller amplitudes; earlier failed gates unchanged; not a nonlinear radius bound")


def save(report):
    storage=store(report,OUTPUT);experiments=[]
    for e in report["attack"]["experiments"]:
        levels=[]
        for l in e["levels"]:
            central=l["central_comparison"];one=l["one_sided_comparison"]
            levels.append(dict(amplitude=l["amplitude"],amplitude_v=l["amplitude"]*KICK_V,
                central={k:v for k,v in central.items() if k!="rows"},
                one_sided={k:v for k,v in one.items() if k!="rows"},
                nonlinear_complete=sum(c["complete"] for c in l["cases"]),
                maximum_node_central_error_v=max((r["maximum_node_linearization_error_v"] for r in central["rows"]),default=None),
                maximum_node_even_response_v=max((r["maximum_node_even_response_v"] for r in one["rows"]),default=None),
                maximum_memory_even_response_v=max((r["maximum_memory_even_response_v"] for r in one["rows"]),default=None),
                stops=[c["stop"] for c in l["cases"]]))
        experiments.append(dict(direction=e["direction"],levels=levels))
    zero_steps=[s for c in report["controls"] for s in c["case"]["steps"]]
    attack_cases=[c for e in report["attack"]["experiments"] for l in e["levels"] for c in l["cases"]]
    steps=zero_steps+[s for c in attack_cases for s in c["steps"]]
    summary={k:v for k,v in report.items() if k not in ("controls","attack")}|dict(storage=storage,
        controls=[dict(name=c["name"],**{k:v for k,v in c["comparison"].items() if k!="rows"},stop=c["case"]["stop"]) for c in report["controls"]],
        attack_experiments=experiments,zero_intervals=len(zero_steps),attack_intervals=sum(len(c["steps"]) for c in attack_cases),
        attack_complete=sum(c["complete"] for c in attack_cases),attack_cases=len(attack_cases),
        maximum_published_kcl_a=max((s["publication"]["max_published_kcl_a"] for s in steps),default=None))
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
