"""Predeclared 64-interval memory tangents on the archived compensated clock."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from circuit66_decimal_static import graph, evaluate as decimal_evaluate
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork, VERSION
from loudness_latch_bdf_static_precision_fixed_clock import OUTPUT as CLOCK, PATHS as OLD_PATHS, SOURCE
from loudness_latch_bdf_static_precision_windows import candidate
from loudness_latch_bdf_static_precision import dynamic, solved, floats
from loudness_latch_bdf_memory_windows import WINDOWS
from loudness_latch_bdf_memory_transfer import (CHARGE_SCALE_C_PER_V, stamps, transfer, propagate,
    perturb_history, node_difference, memory_difference)
from loudness_latch_bdf_probes import pack, unpack, publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical, store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_long.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_long_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_MEMORIA_LARGA_PROTOCOLO.md"
STEP_COUNT=64
AUDIT_INDICES=(0,31,63)
AMPLITUDES=(1.,.5)
KICK_V=1e-6
ABSOLUTE_GATE_V=1e-8
RELATIVE_GATE=1e-3
MAP_GATE=1e-8
PATHS=tuple(dict.fromkeys((*OLD_PATHS,CLOCK,Path(__file__).resolve(),PROTOCOL,
    ROOT/"tools/loudness_latch_bdf_static_precision_windows.py",
    ROOT/"tools/loudness_latch_bdf_memory_windows.py",
    ROOT/"tools/loudness_latch_bdf_memory_transfer.py")))


def serial(operator):
    return {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in operator.items()}


def audit_map(network,old,step,operator):
    virtual,c,x=candidate(old,step,network)
    _,j=network.network.joint.evaluator(10.)(x)
    g=graph(network.network.joint.values)
    _,j80=decimal_evaluate(g,x[:66],80)
    _,j100=decimal_evaluate(g,x[:66],100)
    j[:66,:66]=floats(j80)
    j+=dynamic(network,virtual,x,c["effective_dt_s"])
    new=unpack(network,step["history"])
    b,p,d=stamps(network,new,c["effective_dt_s"])
    result=solved(j,b)
    result.update(decimal80_100_rounded_jacobian_equal=np.array_equal(floats(j80),floats(j100)),
        decimal80_static_jacobian_s=[[str(v) for v in row] for row in j80],
        memory_rhs_s=b.tolist(),publication_gradient=p.tolist(),direct_memory=d.tolist())
    if result["passed"]:
        xref=np.array(result["node_map"]);tref=p@xref+d
        result.update(memory_map=tref.tolist(),
            maximum_scaled_node_map_difference=float(np.max(abs(xref-operator["node_map"])/(1+abs(xref)))),
            maximum_scaled_memory_map_difference=float(np.max(abs(tref-operator["memory_map"])/(1+abs(tref)))))
    result["map_gate_passed"]=bool(result["passed"] and result["decimal80_100_rounded_jacobian_equal"]
        and result["maximum_scaled_node_map_difference"]<MAP_GATE
        and result["maximum_scaled_memory_map_difference"]<MAP_GATE)
    return result


def directions(network,initial,anchor):
    zero=np.zeros(25);kick=zero.copy()
    c2=18+next(k for k,(ref,_,_,_) in enumerate(network.network.joint.contour.caps) if ref=="C2")
    kick[c2]=KICK_V
    out=[("C2-current",kick,zero),("C2-common",kick,kick),("C2-differential",kick,-kick)]
    for i,name in enumerate(("Q25-BE-current","Q25-BC-current","Q15-BE-current","Q15-BC-current"),21):
        charge=zero.copy();charge[i]=KICK_V;out.append((name,charge,zero))
    shadow=unpack(network,anchor["diagnostics"]["shadow_half_steps"][-1]["history"])
    full=unpack(network,anchor["steps"][-1]["history"])
    out.append(("original-full-to-shadow-memory",memory_difference(shadow.current,full.current),zero))
    return out


def continuation(network,initial,reference,operators,current,previous,amplitude,sign):
    old=perturb_history(network,initial,sign*amplitude*current,sign*amplitude*previous)
    injected=pack(old);pc=sign*amplitude*current;pp=sign*amplitude*previous
    rows=[];stop=None
    for i,(base,op) in enumerate(zip(reference,operators)):
        h=base["diagnostics"]["actual_dt_s"];snapshot=state_hash(old)
        pn,pm=propagate(op,pc,pp);new=None;diag=None;pub=None
        try:
            if not np.isfinite(h) or h<1e-12:raise ValueError("interval outside 1 ps domain")
            if not np.isfinite(pn).all() or not np.isfinite(pm).all():raise ValueError("nonfinite propagated tangent")
            new,diag=network.advance(old,10.,h)
            pub=publication_check(network,old,new,h,diag)
            if state_hash(old)!=snapshot:raise ValueError("incoming double history changed")
            if (not pub["round_trip_exact"] or pub["max_published_kcl_a"]>=1e-11
                    or pub["max_branch_equation_error_v"]>=1e-14):
                raise ValueError("unchanged publication gate failed")
            if new.time_s!=base["history"]["time_s"]:raise ValueError("fixed clock changed")
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            stop=dict(index=i,incoming=pack(old),incoming_sha256=snapshot,dt_s=h,error=str(exc),
                candidate=None if new is None else pack(new),diagnostics=diag,publication=pub)
            break
        actual_base=unpack(network,base["history"])
        rows.append(dict(history=pack(new),diagnostics=diag,publication=pub,
            previous_history_sha256=snapshot,published=False,
            node_difference_v=node_difference(new.current,actual_base.current).tolist(),
            memory_difference_v=memory_difference(new.current,actual_base.current).tolist(),
            predicted_node_difference_v=pn.tolist(),predicted_memory_difference_v=pm.tolist()))
        old=new;pp,pc=pc,pm
    return dict(amplitude=amplitude,sign=sign,initial=injected,steps=rows,
        complete=len(rows)==STEP_COUNT,stop=stop,final=pack(old),hypothetical_initial_memory=True,
        local_adaptive_error_gate_applied=False,published=False)


def central_metrics(plus,minus):
    rows=[]
    for p,m in zip(plus["steps"],minus["steps"]):
        row=dict(time_s=p["history"]["time_s"])
        for name in ("node","memory"):
            central=(np.array(p[name+"_difference_v"])-np.array(m[name+"_difference_v"]))/2
            pred=np.array(p["predicted_"+name+"_difference_v"])
            error=abs(central-pred);scaled=error/(ABSOLUTE_GATE_V+RELATIVE_GATE*abs(pred))
            row.update({"central_"+name+"_response_v":central.tolist(),
                "maximum_"+name+"_response_v":float(np.max(abs(central))),
                "maximum_"+name+"_linearization_error_v":float(np.max(error)),
                "maximum_scaled_"+name+"_linearization_error":float(np.max(scaled)),
                "maximum_error_"+name+"_index":int(np.argmax(scaled))})
        rows.append(row)
    complete=plus["complete"] and minus["complete"]
    peaks={"maximum_scaled_"+name+"_linearization_error":max(
        (r["maximum_scaled_"+name+"_linearization_error"] for r in rows),default=None) for name in ("node","memory")}
    return dict(rows=rows,complete=complete,**peaks,passed=bool(complete and all(v<1 for v in peaks.values())))


def generate():
    before=hashes(PATHS);env=environment()
    original=json.loads(gzip.decompress(SOURCE.read_bytes()))["case"]
    clock=json.loads(gzip.decompress(CLOCK.read_bytes()))
    network=CompensatedBdfNetwork(200,model_parameters(1,"finite_transit"));windows=[]
    for name,limit in WINDOWS:
        ai=max(i for i,r in enumerate(original["accepted"]) if r["steps"][-1]["history"]["time_s"]<=limit)
        ci=max(i for i,r in enumerate(clock["reference_clock"]) if r["trial_index"]==ai)
        initial=unpack(network,clock["rows"][ci]["history"])
        expected=clock["rows"][ci+1:ci+1+STEP_COUNT]
        if len(expected)!=STEP_COUNT:raise ValueError("declared clock coverage absent")
        reference=[];operators=[];audits=[];old=initial;stop=None
        for index,base in enumerate(expected):
            new=unpack(network,base["history"]);h=base["diagnostics"]["actual_dt_s"]
            if state_hash(old)!=base["previous_history_sha256"]:raise ValueError("archived candidate lineage changed")
            pub=publication_check(network,old,new,h,base["diagnostics"])
            if (canonical(pub)!=canonical(base["publication"]) or not pub["round_trip_exact"]
                    or pub["max_published_kcl_a"]>=1e-11 or pub["max_branch_equation_error_v"]>=1e-14):
                raise ValueError("archived publication no longer verifies")
            try:op=transfer(network,old,new,base["diagnostics"])
            except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
                stop=dict(index=index,incoming=pack(old),candidate=base,error=str(exc));break
            if index in AUDIT_INDICES:
                audit=audit_map(network,old,base,op);audits.append(dict(index=index,audit=audit))
            reference.append(base);operators.append(op);old=new
        experiments=[]
        for direction,current,previous in directions(network,initial,original["accepted"][ai]):
            levels=[]
            for amplitude in AMPLITUDES:
                cases=[continuation(network,initial,reference,operators,current,previous,amplitude,sign) for sign in (1,-1)]
                levels.append(dict(amplitude=amplitude,cases=cases,central_comparison=central_metrics(*cases)))
            experiments.append(dict(direction=direction,current_direction_v=current.tolist(),
                previous_direction_v=previous.tolist(),levels=levels))
        window=dict(name=name,anchor_limit_s=limit,E4G8_accepted_anchor_index=ai,
            compensated_clock_anchor_index=ci,initial=pack(initial),reference=reference,
            operators=[serial(op) for op in operators],audits=audits,stop=stop,
            experiments=experiments,end_s=old.time_s,reference_complete=len(reference)==STEP_COUNT)
        windows.append(window)
        print(json.dumps(dict(window=name,reference_intervals=len(reference),audit_passes=sum(a["audit"]["map_gate_passed"] for a in audits),
            nonlinear_intervals=sum(len(c["steps"]) for e in experiments for l in e["levels"] for c in l["cases"]),
            central_passes=sum(l["central_comparison"]["passed"] for e in experiments for l in e["levels"]))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("memory-long inputs changed during execution")
    return dict(schema="rf-d/bdf-static-precision-memory-long/v1",source_sha256=before,environment=env,
        integrator_version=VERSION,windows=windows,intervals_per_window=STEP_COUNT,audit_indices=AUDIT_INDICES,
        amplitudes=AMPLITUDES,kick_coordinate_v=KICK_V,charge_coordinate_scale_c_per_v=CHARGE_SCALE_C_PER_V,
        absolute_linearization_gate_v=ABSOLUTE_GATE_V,relative_linearization_gate=RELATIVE_GATE,map_gate=MAP_GATE,
        inherited_residual=True,fresh_dc_new=False,reference_clock_preserved=True,history_reset_count=0,
        initial_memory_injections_are_accepted_states=False,local_adaptive_error_gate_applied=False,
        diagnostic_only=True,independent_full_spatial_oracle=False,temporal_error_bound_admitted=False,
        temporal_refinement_admitted=False,physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation="fixed-clock finite hypothetical injections; selected Decimal/rational spatial checks; binary64 tangent products; no global error bound or exact temporal defect")


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report["windows"]:
        cases=[c for e in w["experiments"] for l in e["levels"] for c in l["cases"]]
        steps=w["reference"]+[s for c in cases for s in c["steps"]]
        experiments=[]
        for e in w["experiments"]:
            norm=float(max(np.max(abs(np.array(e["current_direction_v"]))),np.max(abs(np.array(e["previous_direction_v"])))))
            levels=[]
            for l in e["levels"]:
                c=l["central_comparison"];rows=c["rows"]
                level={k:v for k,v in c.items() if k!="rows"}
                level.update(amplitude=l["amplitude"],stops=[case["stop"] for case in l["cases"]])
                for name in ("node","memory"):
                    peak=max((r["maximum_"+name+"_response_v"] for r in rows),default=None)
                    level["maximum_"+name+"_response_v"]=peak
                    level["observed_"+name+"_response_gain"]=None if peak is None or norm==0 else peak/(norm*l["amplitude"])
                levels.append(level)
            experiments.append(dict(direction=e["direction"],input_coordinate_norm_v=norm,levels=levels))
        windows.append(dict(name=w["name"],anchor_time_s=w["initial"]["time_s"],end_s=w["end_s"],
            reference_intervals=len(w["reference"]),reference_complete=w["reference_complete"],stop=w["stop"],
            nonlinear_intervals=sum(len(c["steps"]) for c in cases),nonlinear_complete=sum(c["complete"] for c in cases),
            nonlinear_cases=len(cases),central_passes=sum(l["central_comparison"]["passed"] for e in w["experiments"] for l in e["levels"]),
            maximum_published_kcl_a=max(s["publication"]["max_published_kcl_a"] for s in steps),
            maximum_linear_backward_error=max((op["max_componentwise_backward_error"] for op in w["operators"]),default=None),
            audits=[dict(index=a["index"],**{k:v for k,v in a["audit"].items() if k in (
                "passed","map_gate_passed","backward_errors","decimal80_100_rounded_jacobian_equal",
                "maximum_scaled_node_map_difference","maximum_scaled_memory_map_difference","error")}) for a in w["audits"]],
            experiments=experiments))
    summary={k:v for k,v in report.items() if k!="windows"}|dict(windows=windows,storage=storage)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
