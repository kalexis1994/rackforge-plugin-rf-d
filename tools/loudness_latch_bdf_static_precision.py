"""Frozen static-current/derivative audit and hypothetical memory directions."""
from decimal import localcontext
import gzip
import json
import math
from pathlib import Path
import sys
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack,pack
from loudness_latch_bdf_memory_windows import OUTPUT as WINDOWS,checked_step
from loudness_latch_bdf_memory_transfer import stamps,perturb_history,node_difference
from loudness_latch_bdf_fd_sensitivity import PATHS as OLD_PATHS,OUTPUT as OLD_FD,STEPS_V,map_metrics
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_rational_solve import solve
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
from circuit66_decimal_static import graph,evaluate,lift

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_PRECISION_ESTATICA_PROTOCOLO.md"


def dependencies():
    paths=[]
    for module in tuple(sys.modules.values()):
        path=Path(getattr(module,"__file__","") or ".").resolve()
        if path.parent!=ROOT/"tools":continue
        paths.append(path)
        for name,value in vars(module).items():
            if "EVIDENCE" in name and isinstance(value,Path) and value.exists():
                paths.append(value)
    return paths


PATHS=tuple(dict.fromkeys((*OLD_PATHS,OLD_FD,Path(__file__).resolve(),PROTOCOL,
                         ROOT/"evidence/.gitattributes",*dependencies())))


def floats(matrix):return np.array([[float(v) for v in row] for row in matrix])
def strings(matrix):return [[str(v) for v in row] for row in matrix]


def derivative_metrics(analytic,fd):
    with localcontext() as ctx:
        ctx.prec=80;worst=lift(0);location=(0,0)
        for row,(a,b) in enumerate(zip(analytic,fd)):
            for col,(u,v) in enumerate(zip(a,b)):
                error=abs(u-v)/(lift(1e-30)+lift(1e-8)*abs(u))
                if error>worst:worst=error;location=(row,col)
        return dict(maximum_scaled_derivative_error=float(worst),maximum_row=location[0],
                    maximum_column=location[1],passed=worst<1)


def decimal_fd(g,x,step):
    with localcontext() as ctx:
        ctx.prec=80;x=[lift(v) for v in x];h=lift(step);n=len(x)
        result=[[lift(0) for _ in x] for _ in x]
        for col in range(n):
            plus=x.copy();minus=x.copy();plus[col]+=h;minus[col]-=h
            rp,_=evaluate(g,plus,jacobian=False);rm,_=evaluate(g,minus,jacobian=False)
            for row in range(n):result[row][col]=(rp[row]-rm[row])/(2*h)
        return result


def dynamic(network,virtual,x,dt):
    n=network.network;j=np.zeros((94,94))
    for left,right,_,cap,resistance in n.branches:
        g=1/(dt/cap+resistance);j[left,left]+=g
        if right is not None:
            j[right,right]+=g;j[left,right]-=g;j[right,left]-=g
    return j+n.latch.evaluate(x,virtual.latch,dt)["capacitance_f"]/dt


def solved(j,b):
    row=dict(jacobian_s=j.tolist(),passed=False)
    try:
        x,audit=solve(j,b);_,errors=backward_errors(j,b,x)
        row.update(node_map=x.tolist(),exact_solve=audit,backward_errors=errors,passed=max(errors.values())<1e-10)
    except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:row["error"]=str(exc)
    return row


def directional_cases(network,old,reference,analytic,mixed,c):
    results=[];h=reference["diagnostics"]["actual_dt_s"]
    base=unpack(network,reference["history"])
    for index in (7,10,18):
        for amplitude in (1e-6,.5e-6):
            kick=np.zeros(25);kick[index]=amplitude;cases=[]
            for sign in (1,-1):
                injected=perturb_history(network,old,sign*kick,np.zeros(25))
                row=dict(sign=sign,initial=pack(injected),hypothetical_initial_memory=True,published=False)
                try:
                    new,s=checked_step(network,injected,h)
                    row.update(**s,node_difference_v=node_difference(new.current,base.current).tolist(),complete=True)
                except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:row.update(error=str(exc),complete=False)
                cases.append(row)
            result=dict(memory=index,amplitude_v=amplitude,cases=cases,comparisons={})
            if all(r["complete"] for r in cases):
                central=(np.array(cases[0]["node_difference_v"])-np.array(cases[1]["node_difference_v"]))/2
                for name,x in (("decimal-analytic",analytic),("original-mixed",mixed)):
                    predicted=x@((1+c["gamma"])*kick)
                    scaled=abs(central-predicted)/(1e-8+1e-3*abs(predicted))
                    result["comparisons"][name]=dict(central_v=central.tolist(),prediction_v=predicted.tolist(),
                        maximum_scaled_error=float(np.max(scaled)),passed=bool(np.max(scaled)<1))
            results.append(result)
    return results


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(WINDOWS.read_bytes()))
    fd_source=json.loads(gzip.decompress(OLD_FD.read_bytes()))
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));g=graph(network.network.joint.values)
    cases=[]
    for window,old_fd in zip(source["windows"],fd_source["cases"]):
        old=unpack(network,window["initial"]);reference=window["reference"][0]
        new=unpack(network,reference["history"]);diag=reference["diagnostics"]
        virtual,c=network.effective_history(old,diag["actual_dt_s"]);delta=np.array(diag["increment_v"])
        x=np.array([math.fsum((a,b,d)) for a,b,d in zip(virtual.joint.node_v,virtual.node_low_v,delta)])
        binary_static,static_j=network.network.joint.evaluator(10.)(x)
        # Remove the R59 cross-boundary current already in the joint residual.
        original=binary_static[:66].copy();original[32]+=x[network.network.joint.out]/68000
        r80,j80=evaluate(g,x[:66],80);r100,j100=evaluate(g,x[:66],100)
        discrepancy=float(np.max(abs(np.array([float(v) for v in r80])-original)))
        row=dict(window=window["name"],initial=window["initial"],reference_step=reference,node_candidate_v=x.tolist(),
            original_audio_static_residual_a=original.tolist(),decimal80_audio_static_residual_a=[str(v) for v in r80],
            decimal80_audio_static_jacobian_s=strings(j80),static_residual_discrepancy_a=discrepancy,
            static_residual_gate_passed=discrepancy<1e-11,
            decimal80_100_rounded_residual_equal=np.array_equal([float(v) for v in r80],[float(v) for v in r100]),
            decimal80_100_rounded_jacobian_equal=np.array_equal(floats(j80),floats(j100)),fd=[],directions=[])
        if discrepancy<1e-11:
            dyn=dynamic(network,virtual,x,c["effective_dt_s"])
            b,_,_=stamps(network,new,c["effective_dt_s"])
            def combined(j):
                out=static_j.copy();out[:66,:66]=floats(j);return out+dyn
            analytic=solved(combined(j80),b);precise=solved(combined(j100),b)
            row.update(memory_rhs_s=b.tolist(),analytic=analytic,decimal100=precise)
            if analytic["passed"] and precise["passed"]:
                ax=np.array(analytic["node_map"]);mixed=np.array(window["operators"][0]["node_map"])
                row["decimal80_100_map"]=map_metrics(ax,np.array(precise["node_map"]))
                row["original_mixed_map"]=map_metrics(ax,mixed)
                frozen=next(r for r in old_fd["rows"] if r["step_v"]==1e-6 and r["mode"]=="full-residual-FD")
                row["original_full_fd_map"]=map_metrics(ax,np.array(frozen["node_map"]))
                for h in STEPS_V:
                    jf=decimal_fd(g,x[:66],h);f=solved(combined(jf),b)
                    f.update(step_v=h,decimal80_audio_fd_jacobian_s=strings(jf),derivative_comparison=derivative_metrics(j80,jf))
                    if f["passed"]:
                        f["map_comparison"]=map_metrics(ax,np.array(f["node_map"]))
                        f["map_gate_passed"]=f["map_comparison"]["node_map_max_scaled_difference"]<1e-8
                    row["fd"].append(f)
                row["directions"]=directional_cases(network,old,reference,ax,mixed,c)
        cases.append(row)
        print(json.dumps(dict(window=row["window"],static_discrepancy_a=discrepancy,
            static_residual_gate_passed=row["static_residual_gate_passed"],fd_matrices=len(row["fd"]),
            directions=len(row["directions"]),original_mixed_map=row.get("original_mixed_map"))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("static precision inputs changed during execution")
    return dict(schema="rf-d/bdf-static-precision/v1",source_sha256=before,environment=env,graph=g,cases=cases,
        producer_source_utf8=Path(__file__).read_text(encoding="utf-8"),
        decimal_evaluator_source_utf8=(ROOT/"tools/circuit66_decimal_static.py").read_text(encoding="utf-8"),
        steps_v=STEPS_V,derivative_absolute_gate_s=1e-30,derivative_relative_gate=1e-8,
        static_residual_gate_a=1e-11,backward_gate=1e-10,map_gate=1e-8,
        independent_static_transcription=True,independent_full_spatial_oracle=False,
        original_reset_fd_gate_closed=False,previous_reports_modified=False,new_step_selected=False,
        original_solver_modified=False,temporal_error_bound_admitted=False,physical_switching_admitted=False,
        temporal_refinement_admitted=False,audio_admitted=False,diagnostic_only=True)


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ("graph","cases","producer_source_utf8","decimal_evaluator_source_utf8")}
    summary.update(storage=storage,graph_counts={k:len(report["graph"][k]) for k in ("resistors","conductances","bjts","diodes")},
        cases=[{k:v for k,v in case.items() if k not in ("initial","reference_step","node_candidate_v",
            "original_audio_static_residual_a","decimal80_audio_static_residual_a","decimal80_audio_static_jacobian_s",
            "memory_rhs_s","analytic","decimal100","fd","directions")}
            | dict(analytic={k:v for k,v in case.get("analytic",{}).items() if k not in ("jacobian_s","node_map","exact_solve")},
                fd=[{k:v for k,v in f.items() if k not in ("jacobian_s","node_map","exact_solve","decimal80_audio_fd_jacobian_s")} for f in case["fd"]],
                directions=[{k:v for k,v in d.items() if k not in ("cases","comparisons")}
                    | dict(complete=all(r["complete"] for r in d["cases"]),comparisons={k:{a:b for a,b in v.items()
                    if a not in ("central_v","prediction_v")} for k,v in d["comparisons"].items()}) for d in case["directions"]])
            for case in report["cases"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
