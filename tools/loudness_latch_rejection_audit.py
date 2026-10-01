"""Fixed-history Newton floor and charge-origin audit; no gate relaxation."""
from dataclasses import asdict
from decimal import Decimal,localcontext
import hashlib
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_charge_reference import ChargedNetwork
from loudness_latch_time_probes import unpack,pack,state_hash,POLICIES
from loudness_latch_time_reference import charges
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_rejection_audit.json"


def diagnose(network,old,h,use_fd=False):
    evaluate=network.evaluator(10.0,old,h)
    x=np.array(old.joint.node_v)
    rows=[]
    for iteration in range(80):
        r,j=evaluate(x,use_fd=use_fd);d=np.linalg.solve(j,-r)
        error=float(np.max(np.abs(r)));correction=float(np.max(np.abs(d)))
        row=dict(iteration=iteration,node_v=x.tolist(),max_kcl_a=error,correction_v=correction,
                 limiting_row=int(np.argmax(np.abs(r))),jacobian_condition_number=float(np.linalg.cond(j)),
                 linear_residual_a=float(np.max(np.abs(r+j@d))),trials=[])
        rows.append(row)
        if error<1e-11 and correction<1e-8:
            return dict(status="accepted",iterations=rows,dt_s=h,use_fd=use_fd,final_node_v=x.tolist())
        for power in range(24):
            candidate=x+2.0**-power*d
            try:
                rt,_=evaluate(candidate,False);te=float(np.max(np.abs(rt)))
                accepted=te<error
                tc=None
                if error<1e-11 and te<1e-11:
                    rt,jt=evaluate(candidate,use_fd=use_fd);td=np.linalg.solve(jt,-rt)
                    tc=float(np.max(np.abs(td)));accepted=tc<correction
                elif error<1e-11:accepted=False
                row["trials"].append(dict(power=power,max_kcl_a=te,correction_v=tc,
                    changed_coordinates=int(np.sum(candidate!=x)),accepted=accepted))
                if accepted:x=candidate;break
            except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
                row["trials"].append(dict(power=power,error=str(exc),accepted=False,
                    changed_coordinates=int(np.sum(candidate!=x))))
        else:return dict(status="line-search-rejected",iterations=rows,dt_s=h,use_fd=use_fd,final_node_v=x.tolist())
    return dict(status="iteration-budget",iterations=rows,dt_s=h,use_fd=use_fd,final_node_v=x.tolist())


def terminal(q):
    return (q[0]+q[1],-q[1],-q[0])


def origin_scaled_error(a,b,offset,absolute,relative):
    # Hold the original numerator exactly unchanged in this shadow. Only
    # the denominator uses the conventional reference shift.
    a,b=np.asarray(a),np.asarray(b)
    return float(np.max(np.abs(a-b)/(absolute+relative*np.maximum(np.abs(a+offset),np.abs(b+offset)))))


def coordinate_floor(network,old,audit):
    x=np.array(audit["final_node_v"])
    evaluate=network.evaluator(10.0,old,audit["dt_s"])
    r,j=evaluate(x,use_fd=audit["use_fd"])
    d=np.linalg.solve(j,-r)
    index=66+network.joint.contour.index["TIMING_C2"]
    neighbors=[]
    for toward in (-np.inf,np.inf):
        shifted=x.copy();shifted[index]=np.nextafter(x[index],toward)
        rt,_=evaluate(shifted,False)
        neighbors.append(dict(node_v=float(shifted[index]),delta_v=float(shifted[index]-x[index]),
                              timing_kcl_a=float(rt[index]),max_kcl_a=float(np.max(np.abs(rt)))))
    return dict(index=index,node="TIMING_C2",node_v=float(x[index]),timing_kcl_a=float(r[index]),
                timing_newton_delta_v=float(d[index]),timing_coordinate_changes=bool(x[index]+d[index]!=x[index]),
                timing_jacobian_s=float(j[index,index]),nearest_representable_neighbors=neighbors)


def gauge_difference_error(full,fine,offset,h):
    # Exact decimal arithmetic on the recorded binary64 values isolates the
    # algebraic gauge identity from rounding introduced by a large offset.
    with localcontext() as ctx:
        ctx.prec=80
        a=[Decimal.from_float(float(v)) for v in full]
        b=[Decimal.from_float(float(v)) for v in fine]
        c=Decimal.from_float(float(offset));dt=Decimal.from_float(float(h))
        errors=[]
        for k in (0,2):
            original=[(x-y)/dt for x,y in zip(terminal(a[k:k+2]),terminal(b[k:k+2]))]
            shifted=[(x-y)/dt for x,y in zip(terminal([x+c for x in a[k:k+2]]),terminal([x+c for x in b[k:k+2]]))]
            errors.extend(abs(x-y) for x,y in zip(original,shifted))
        return float(max(errors))


def generate():
    data=json.loads((ROOT/"evidence/loudness_latch_time_probes.json").read_text())
    network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
    strict=data["cases"][1]
    old=unpack(network,strict["final"],10.0)
    snapshot=state_hash(old)
    h=next(r["dt_s"] for r in strict["rejected"] if r["diagnostics"]["reason"]=="solve-rejected")
    full,full_diag=network.step(old,10.0,h)
    half,half_diag=network.step(old,10.0,h/2)
    hybrid=diagnose(network,half,h/2)
    fd=diagnose(network,half,h/2,use_fd=True)
    hybrid["coordinate_floor"]=coordinate_floor(network,half,hybrid)
    fd["coordinate_floor"]=coordinate_floor(network,half,fd)
    # Repeat the actual production call, not just the instrumented observer.
    try:
        result,diag=network.step(half,10.0,h/2)
        production=dict(status="accepted",diagnostics=diag)
    except ValueError as exc:production=dict(status="rejected",error=str(exc))
    shadows=[]
    for index,case in enumerate(data["cases"]):
        policy=POLICIES[index]
        previous={0.0:unpack(network,case["initial"],0.0)}
        for row in case["accepted"]:
            previous[row["start_s"]+row["dt_s"]]=unpack(network,row["fine"],10.0)
        candidates=[r for r in case["rejected"] if r["diagnostics"].get("voltage_error_ratio",2)<1
                    and r["diagnostics"].get("charge_error_ratio",0)>1
                    and r["diagnostics"].get("junction_increment_v",1)<policy.junction_increment_v]
        row=candidates[-1];before=previous[row["time_s"]];step=row["dt_s"]
        coarse,_=network.step(before,10.0,step)
        middle,_=network.step(before,10.0,step/2)
        fine,_=network.step(middle,10.0,step/2)
        a,b=charges(coarse),charges(fine)
        shadows.append(dict(policy_index=index,time_s=row["time_s"],dt_s=step,
            previous=pack(before),full_charge_c=a.tolist(),fine_charge_c=b.tolist(),
            original_diagnostics=row["diagnostics"],offsets=[dict(offset_c=o,
                charge_error_ratio=origin_scaled_error(a,b,o,policy.charge_abs_c,policy.charge_relative),
                decimal_terminal_increment_difference_a=gauge_difference_error(a,b,o,step)) for o in (-1e-9,0.,1e-9)],
            original_rejection_retained=True,published_shadow=False))
    assert state_hash(old)==snapshot
    paths=[ROOT/"tools/loudness_latch_rejection_audit.py",ROOT/"tools/loudness_latch_charge_reference.py",
           ROOT/"tools/loudness_latch_time_reference.py",ROOT/"tools/loudness_latch_time_probes.py",
           ROOT/"evidence/loudness_latch_time_probes.json"]
    return dict(schema="rf-d/latch-rejection-audit/v1",environment=environment(),
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        replay=dict(previous=pack(old),previous_state_sha256=snapshot,macro_dt_s=h,
                    full_diagnostics=full_diag,half_diagnostics=half_diag,half_state=pack(half),
                    failing_stage="second-half",production=production,hybrid=hybrid,full_fd=fd),
        charge_origin_shadows=shadows,gates_unchanged=True,original_report_modified=False,
        physical_switching_admitted=False,temporal_refinement_admitted=False,audio_admitted=False,selected=None,
        limitation="diagnoses numerical rejection and conventional charge-origin sensitivity; no new trajectory or physical parameter fit")


if __name__=="__main__":
    report=generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(hybrid=report["replay"]["hybrid"]["status"],fd=report["replay"]["full_fd"]["status"],
                         production=report["replay"]["production"],
                         origin_ratios=[[o["charge_error_ratio"] for o in s["offsets"]] for s in report["charge_origin_shadows"]])))
