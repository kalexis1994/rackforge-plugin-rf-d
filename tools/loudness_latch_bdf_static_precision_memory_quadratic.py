"""Circuit-derived second variations, with no nonlinear-response coefficient fit."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
import loudness_latch_directional_curvature as curvature
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_static_precision_memory_extrema import (OUTPUT as DIRECTIONS,SOURCE,PATHS as OLD_PATHS)
from loudness_latch_bdf_static_precision_windows import candidate
from loudness_latch_bdf_memory_transfer import stamps
from loudness_latch_bdf_transfer_solve import solve
from loudness_latch_bdf_static_precision import solved
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_quadratic.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_quadratic_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_CURVATURA_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,DIRECTIONS,Path(__file__).resolve(),PROTOCOL,
    ROOT/"tools/loudness_latch_directional_curvature.py")))
AUDIT_INDICES=(0,31,63)
EPSILONS=(2**-10,2**-12,2**-14)


def definitions(window):
    return [{k:e[k] for k in ("direction","selection","unit_direction","current_direction_v","previous_direction_v")}
            for e in window["experiments"]]


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(SOURCE.read_bytes()))
    directions=[dict(name=w["name"],definitions=definitions(w)) for w in json.loads(gzip.decompress(DIRECTIONS.read_bytes()))["windows"]]
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"));g=curvature.graph(network);windows=[]
    for base,selected in zip(source["windows"],directions):
        if base["name"]!=selected["name"] or len(base["reference"])!=64:raise ValueError("frozen base coverage mismatch")
        defs=selected["definitions"];pc1=np.array([d["current_direction_v"] for d in defs]).T
        pp1=np.array([d["previous_direction_v"] for d in defs]).T
        pc2=np.zeros_like(pc1);pp2=np.zeros_like(pp1);old=unpack(network,base["initial"]);rows=[];stop=None
        for index,(step,operator) in enumerate(zip(base["reference"],base["operators"])):
            new=unpack(network,step["history"]);virtual,c,x=candidate(old,step,network)
            gamma=c["gamma"];v1=(1+gamma)*pc1-gamma*pp1;v2=(1+gamma)*pc2-gamma*pp2
            n1=np.array(operator["node_map"])@v1;m1=np.array(operator["memory_map"])@v1
            _,j=network.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(np.array(step["diagnostics"]["increment_v"]))
            b,p,direct=stamps(network,new,c["effective_dt_s"])
            terms=[]
            for k in range(6):
                a=curvature.evaluate(network,g,x,n1[:,k],c["effective_dt_s"],80)
                a100=curvature.evaluate(network,g,x,n1[:,k],c["effective_dt_s"],100)
                terms.append(dict(residual_a=[str(v) for v in a["residual_a"]],
                    publication_coordinate_v=[str(v) for v in a["publication_coordinate_v"]],
                    precision_comparison={key:curvature.metrics(a[key],a100[key]) for key in ("residual_a","publication_coordinate_v")}))
            h=np.array([[float(v) for v in t["residual_a"]] for t in terms]).T
            publication=np.array([[float(v) for v in t["publication_coordinate_v"]] for t in terms]).T
            rhs=b@v2-h
            try:n2,audit=solve(j,rhs)
            except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
                stop=dict(index=index,error=str(exc),incoming_first_current=pc1.tolist(),incoming_first_previous=pp1.tolist(),
                    incoming_second_current=pc2.tolist(),incoming_second_previous=pp2.tolist(),rhs_a=rhs.tolist(),terms=terms);break
            m2=p@n2+direct@v2+publication
            row=dict(index=index,time_s=new.time_s,coefficients=c,node_candidate_v=x.tolist(),
                node_first_v=n1.tolist(),memory_first_v=m1.tolist(),node_second_v=n2.tolist(),memory_second_v=m2.tolist(),
                rhs_second_a=rhs.tolist(),terms=terms,linear_solve=audit,
                precision_gate_passed=all(v["passed"] for t in terms for v in t["precision_comparison"].values()))
            if index in AUDIT_INDICES:
                r,_=curvature.static_values(g,x,80,jacobian=False);original,_=network.network.joint.evaluator(10.)(x,False)
                discrepancy=float(np.max(abs(curvature.floats(r)-original)))
                exact=solved(j,rhs)
                if exact["passed"]:
                    reference=np.array(exact["node_map"])
                    exact["maximum_scaled_second_difference"]=float(np.max(abs(n2-reference)/(1+abs(reference))))
                    exact["map_gate_passed"]=exact["maximum_scaled_second_difference"]<1e-8
                else:exact["map_gate_passed"]=False
                fd=[]
                for k in range(6):
                    reference=curvature.evaluate(network,g,x,n1[:,k],c["effective_dt_s"],80)
                    levels=[]
                    for epsilon in EPSILONS:
                        value=curvature.finite_difference(network,g,x,n1[:,k],c["effective_dt_s"],epsilon,80)
                        levels.append(dict(epsilon=epsilon,comparisons={key:curvature.metrics(reference[key],value[key])
                            for key in ("residual_a","publication_coordinate_v")}))
                    fd.append(dict(direction=defs[k]["direction"],levels=levels))
                row["audit"]=dict(static_current_discrepancy_a=discrepancy,static_current_gate_passed=discrepancy<1e-11,
                    exact=exact,fd=fd,fd_all_passed=all(v["passed"] for f in fd for level in f["levels"] for v in level["comparisons"].values()))
            rows.append(row);old=new;pp1,pc1=pc1,m1;pp2,pc2=pc2,m2
        windows.append(dict(name=base["name"],initial=base["initial"],definitions=defs,rows=rows,stop=stop,complete=len(rows)==64))
        print(json.dumps(dict(window=base["name"],intervals=len(rows),precision_passes=sum(r["precision_gate_passed"] for r in rows),
            fd_audit_passes=sum(r["audit"]["fd_all_passed"] for r in rows if "audit" in r))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("quadratic derivation inputs changed")
    return dict(schema="rf-d/bdf-static-precision-memory-quadratic/v1",source_sha256=before,environment=env,
        graph=g,windows=windows,audit_indices=AUDIT_INDICES,fd_epsilons=EPSILONS,new_nonlinear_solves=0,
        initial_second_variations_zero=True,coefficients_fitted_to_responses=False,
        reserved_response_amplitudes=(.75,.375,.1875),curvature_absolute_gate=1e-30,curvature_relative_gate=1e-8,
        static_current_gate_a=1e-11,second_solve_backward_gate=1e-10,second_solve_map_gate=1e-8,
        diagnostic_only=True,temporal_error_bound_admitted=False,physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation="second variations of conditional circuit laws along frozen base trajectory; shared topology and parameters, no physical calibration or global Taylor remainder bound")


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report["windows"]:
        audits=[r["audit"] for r in w["rows"] if "audit" in r]
        windows.append(dict(name=w["name"],intervals=len(w["rows"]),complete=w["complete"],stop=w["stop"],
            precision_passes=sum(r["precision_gate_passed"] for r in w["rows"]),
            maximum_second_backward_error=max((max(r["linear_solve"][key] for key in (
                "binary_componentwise_backward_error","decimal80_componentwise_backward_error")) for r in w["rows"]),default=None),
            audits=[dict(static_current_discrepancy_a=a["static_current_discrepancy_a"],static_current_gate_passed=a["static_current_gate_passed"],
                exact_passed=a["exact"]["passed"],exact_map_passed=a["exact"]["map_gate_passed"],
                maximum_scaled_second_difference=a["exact"].get("maximum_scaled_second_difference"),fd_all_passed=a["fd_all_passed"],fd=a["fd"]) for a in audits]))
    summary={k:v for k,v in report.items() if k not in ("windows","graph")}|dict(storage=storage,windows=windows,
        graph_counts={key:len(report["graph"][key]) for key in ("resistors","conductances","bjts","diodes")})
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
