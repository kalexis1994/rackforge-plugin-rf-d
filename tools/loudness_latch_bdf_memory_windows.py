"""Declared finite memory perturbations and fixed-clock tangent propagation."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_bdf_growth_dc import OUTPUT as SOURCE,PATHS as SOURCE_PATHS
from loudness_latch_bdf_memory_transfer import (CHARGE_SCALE_C_PER_V,memory_difference,node_difference,
    perturb_history,transfer,propagate)
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_memory_windows.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_memory_windows_summary.json"
WINDOWS=(("prefix",.0023),("attack",.0024222),("reset",.00244205),("tail",.0025))
STEP_COUNT=16
AMPLITUDES=(1.,.5)
C2_KICK_V=1e-6
ABSOLUTE_GATE_V=1e-8
RELATIVE_GATE=1e-3
BACKWARD_GATE=1e-10
JACOBIAN_GATE=1e-8
PATHS=tuple(dict.fromkeys((*SOURCE_PATHS,SOURCE,Path(__file__).resolve(),
                         ROOT/"tools/loudness_latch_bdf_memory_transfer.py")))


def checked_step(network,old,h):
    if not np.isfinite(h) or h<1e-12:raise ValueError("reference interval outside declared 1 ps domain")
    snapshot=state_hash(old);new,d=network.advance(old,10.,h)
    check=publication_check(network,old,new,h,d)
    if state_hash(old)!=snapshot:raise ValueError("memory-window solve changed its incoming histories")
    if (not check["round_trip_exact"] or check["max_published_kcl_a"]>=1e-11
            or check["max_branch_equation_error_v"]>=1e-14):
        raise ValueError("memory-window publication failed unchanged charge gates")
    return new,dict(history=pack(new),diagnostics=d,publication=check,
                    previous_history_sha256=snapshot,published=False)


def continuation(network,initial,reference,operators,current,previous,amplitude,sign):
    old=perturb_history(network,initial,sign*amplitude*current,sign*amplitude*previous)
    injected=pack(old);pred_current=sign*amplitude*current;pred_previous=sign*amplitude*previous
    steps=[];stop=None
    for base,operator in zip(reference,operators):
        h=base["diagnostics"]["actual_dt_s"]
        predicted_nodes,predicted_memory=propagate(operator,pred_current,pred_previous)
        try:new,row=checked_step(network,old,h)
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            stop=dict(reason="solve-or-publication-failed",time_s=old.time_s,dt_s=h,error=str(exc));break
        actual_base=unpack(network,base["history"])
        row.update(node_difference_v=node_difference(new.current,actual_base.current).tolist(),
                   memory_difference_v=memory_difference(new.current,actual_base.current).tolist(),
                   predicted_node_difference_v=predicted_nodes.tolist(),
                   predicted_memory_difference_v=predicted_memory.tolist())
        steps.append(row);old=new
        pred_previous,pred_current=pred_current,predicted_memory
    return dict(amplitude=amplitude,sign=sign,initial=injected,steps=steps,
        complete=len(steps)==len(reference),stop=stop,final=pack(old),
        hypothetical_initial_memory=True,local_adaptive_error_gate_applied=False,published=False)


def central_metrics(plus,minus):
    rows=[]
    for p,m in zip(plus["steps"],minus["steps"]):
        central=(np.array(p["node_difference_v"])-np.array(m["node_difference_v"]))/2
        predicted=np.array(p["predicted_node_difference_v"])
        error=np.abs(central-predicted);scale=ABSOLUTE_GATE_V+RELATIVE_GATE*np.abs(predicted)
        rows.append(dict(time_s=p["history"]["time_s"],maximum_node_response_v=float(np.max(np.abs(central))),
            maximum_node_linearization_error_v=float(np.max(error)),
            maximum_scaled_linearization_error=float(np.max(error/scale)),
            maximum_error_node=int(np.argmax(error)),central_node_response_v=central.tolist()))
    return dict(rows=rows,complete=plus["complete"] and minus["complete"],
        maximum_scaled_linearization_error=max((r["maximum_scaled_linearization_error"] for r in rows),default=None),
        passed=bool(plus["complete"] and minus["complete"] and all(r["maximum_scaled_linearization_error"]<1 for r in rows)))


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(SOURCE.read_bytes()))["case"]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));windows=[]
    c2_index=18+next(k for k,(ref,_,_,_) in enumerate(network.network.joint.contour.caps) if ref=="C2")
    for name,limit in WINDOWS:
        index=max(k for k,row in enumerate(source["accepted"]) if row["steps"][-1]["history"]["time_s"]<=limit)
        anchor=source["accepted"][index];initial=unpack(network,anchor["steps"][-1]["history"])
        expected=source["accepted"][index+1:index+1+STEP_COUNT]
        if len(expected)!=STEP_COUNT:raise ValueError("declared reference window lacks coverage")
        reference=[];operators=[];old=initial
        for row in expected:
            new,s=checked_step(network,old,row["dt_s"])
            if new!=unpack(network,row["steps"][-1]["history"]):raise ValueError("fixed-step reference does not replay E4G8")
            operator=transfer(network,old,new,s["diagnostics"])
            if operator["max_componentwise_backward_error"]>=BACKWARD_GATE:raise ValueError("linear map solve failed declared gate")
            if not reference:
                try:
                    fd=transfer(network,old,new,s["diagnostics"],use_fd=True)
                    operator["fd_node_map_max_scaled_difference"]=float(np.max(np.abs(operator["node_map"]-fd["node_map"])/(1+np.abs(operator["node_map"]))))
                    operator["fd_backward_error"]=fd["max_componentwise_backward_error"]
                    operator["fd_passed"]=bool(operator["fd_node_map_max_scaled_difference"]<JACOBIAN_GATE
                                               and operator["fd_backward_error"]<BACKWARD_GATE)
                except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
                    operator.update(fd_passed=False,fd_error=str(exc))
            reference.append(s);operators.append(operator);old=new
        kick=np.zeros(25);kick[c2_index]=C2_KICK_V;zero=np.zeros(25)
        shadow=unpack(network,anchor["diagnostics"]["shadow_half_steps"][-1]["history"])
        defect=memory_difference(shadow.current,initial.current)
        directions=(("C2-current",kick,zero),("C2-common",kick,kick),("C2-differential",kick,-kick),
                    ("full-to-shadow-memory",defect,zero))
        experiments=[]
        for direction,current,previous in directions:
            levels=[]
            for amplitude in AMPLITUDES:
                cases=[continuation(network,initial,reference,operators,current,previous,amplitude,sign) for sign in (1,-1)]
                levels.append(dict(amplitude=amplitude,cases=cases,central_comparison=central_metrics(*cases)))
            experiments.append(dict(direction=direction,current_direction_v=current.tolist(),
                previous_direction_v=previous.tolist(),levels=levels))
        stored_operators=[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in op.items()} for op in operators]
        window=dict(name=name,anchor_limit_s=limit,E4G8_accepted_anchor_index=index,initial=pack(initial),
            end_s=old.time_s,reference=reference,operators=stored_operators,experiments=experiments,
            initial_memory_injections_are_accepted_states=False,reference_clock_preserved=True)
        windows.append(window)
        print(json.dumps(dict(window=name,end_s=old.time_s,reference_steps=len(reference),
            nonlinear_steps=sum(len(c["steps"]) for e in experiments for l in e["levels"] for c in l["cases"]),
            central_passes=sum(l["central_comparison"]["passed"] for e in experiments for l in e["levels"]),
            central_cases=len(experiments)*len(AMPLITUDES))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("memory-window inputs changed during execution")
    return dict(schema="rf-d/bdf-memory-windows/v1",source_sha256=before,environment=env,windows=windows,
        charge_coordinate_scale_c_per_v=CHARGE_SCALE_C_PER_V,step_count=STEP_COUNT,C2_kick_v=C2_KICK_V,
        amplitudes=AMPLITUDES,absolute_node_linearization_gate_v=ABSOLUTE_GATE_V,
        relative_node_linearization_gate=RELATIVE_GATE,linear_backward_gate=BACKWARD_GATE,
        fd_scaled_map_gate=JACOBIAN_GATE,hypothetical_memory_injections=True,diagnostic_only=True,
        previous_reports_modified=False,trajectory_retimed=False,temporal_refinement_admitted=False,
        temporal_error_bound_admitted=False,physical_switching_admitted=False,audio_admitted=False,
        limitation="fixed-clock finite memory injections are not accepted past states or a DC refinement; raw full/shadow differences are not exact temporal defects; shared circuit and solver")


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report["windows"]:
        cases=[c for e in w["experiments"] for l in e["levels"] for c in l["cases"]]
        steps=w["reference"]+[s for c in cases for s in c["steps"]]
        windows.append(dict(name=w["name"],anchor_limit_s=w["anchor_limit_s"],
            anchor_time_s=w["initial"]["time_s"],end_s=w["end_s"],reference_intervals=len(w["reference"]),
            nonlinear_intervals=sum(len(c["steps"]) for c in cases),nonlinear_complete=sum(c["complete"] for c in cases),
            nonlinear_cases=len(cases),max_published_kcl_a=max(s["publication"]["max_published_kcl_a"] for s in steps),
            maximum_linear_backward_error=max(op["max_componentwise_backward_error"] for op in w["operators"]),
            fd_first_map={k:v for k,v in w["operators"][0].items() if k.startswith("fd_")},
            experiments=[dict(direction=e["direction"],levels=[dict(amplitude=l["amplitude"],
                **{k:v for k,v in l["central_comparison"].items() if k!="rows"},
                maximum_node_response_v=max((r["maximum_node_response_v"] for r in l["central_comparison"]["rows"]),default=None),
                stops=[c["stop"] for c in l["cases"]]) for l in e["levels"]]) for e in w["experiments"]]))
    summary={k:v for k,v in report.items() if k!="windows"}|dict(windows=windows,storage=storage)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":save(generate())
