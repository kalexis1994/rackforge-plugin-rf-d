"""BDF2 publication checked directly from true histories with Decimal arithmetic."""
from decimal import Decimal,localcontext
import json
import math
from pathlib import Path
import numpy as np
from loudness_latch_bdf_reference import History,BdfNetwork,coefficients
from loudness_latch_increment_probes import pack as pack_state,unpack as unpack_state,hashes,SOURCE_PATHS
from loudness_lab_metadata import environment
from bjt_charge_ngspice_probes import model_parameters

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_probes.json"
PATHS=(*SOURCE_PATHS,Path(__file__).resolve(),ROOT/"tools/loudness_latch_bdf_reference.py")


def pack(history):
    return dict(schema="rf-d/bdf-two-state/v1",current=pack_state(history.current),
        previous=None if history.previous is None else pack_state(history.previous),
        previous_dt_s=history.previous_dt_s,time_s=history.time_s,key_v=history.key_v,
        previous_key_v=history.previous_key_v)


def unpack(network,record):
    if record["schema"]!="rf-d/bdf-two-state/v1":raise ValueError("versioned BDF history required")
    history=History(unpack_state(network.network,record["current"],record["key_v"]),
        None if record["previous"] is None else unpack_state(network.network,record["previous"],record["previous_key_v"]),
        record["previous_dt_s"],record["time_s"],record["key_v"],record["previous_key_v"])
    network.validate(history)
    return history


def publication_check(network,old,new,h,diag):
    """Independent direct BDF formula, not differences from virtual histories."""
    n=network.network;x=new.current.joint.node_v
    r,_=n.joint.evaluator(new.key_v)(x,False)
    checks=[]
    with localcontext() as ctx:
        ctx.prec=80
        D=lambda x:Decimal.from_float(float(x))
        S=lambda p:sum(map(D,p),Decimal(0))
        if old.previous is None:a0,a2=D(1.),D(0.)
        else:
            c=coefficients(h,old.previous_dt_s);a0,a2=D(c["a0"]),D(c["a2"])
        derivative=lambda a,b,c:(a0*(a-b)-a2*(b-c))/D(h)
        for k,(left,right,fixed,c,resistance) in enumerate(n.branches):
            a=S(new.current.capacitor_pairs_v[k]);b=S(old.current.capacitor_pairs_v[k])
            z=b if old.previous is None else S(old.previous.capacitor_pairs_v[k])
            current=D(c)*derivative(a,b,z)
            branch=S((x[left],new.current.node_low_v[left]))
            branch-=D(fixed) if right is None else S((x[right],new.current.node_low_v[right]))
            equation=branch-a-D(resistance)*current
            checks.append(dict(index=k,current_a=float(current),branch_equation_error_v=float(equation)))
            r[left]+=float(current)
            if right is not None:r[right]-=float(current)
        charge_rows=[]
        for k,terminals in enumerate(n.latch.terminals):
            a=new.current.latch.devices[k];b=old.current.latch.devices[k]
            z=b if old.previous is None else old.previous.latch.devices[k]
            be=derivative(D(a.be_c),D(b.be_c),D(z.be_c))
            bc=derivative(D(a.bc_c),D(b.bc_c),D(z.bc_c))
            terminal=(be+bc,-bc,-be)
            charge_rows.append(dict(device=k,junction_current_a=[float(be),float(bc)],
                                    terminal_current_a=list(map(float,terminal)),sum_terminal_a=float(sum(terminal))))
            for (i,_),current in zip(terminals,terminal):
                if i is not None:r[i]+=float(current)
    restored=unpack(network,json.loads(json.dumps(pack(new))))
    return dict(max_published_kcl_a=float(np.max(np.abs(r))),linear_branches=checks,nonlinear_devices=charge_rows,
        max_branch_equation_error_v=max(abs(c["branch_equation_error_v"]) for c in checks),
        round_trip_exact=restored==new,derivative="[a0*(Qnew-Qold)-a2*(Qold-Qolder)]/h; Decimal80")


def scalar_rc(h,end=5e-4,tau=1e-4):
    """Synthetic 1 V discharge; independently solves the scalar recurrence."""
    old=1.;older=None;k=None;t=0.;rows=[]
    while t<end:
        dt=min(h,end-t)
        if older is None:new=old/(1+dt/tau)
        else:
            c=coefficients(dt,k)
            new=((1+c["ratio"])*old-c["a2"]*older)/(c["a0"]+dt/tau)
        t+=dt;rows.append((t,new));older,old=old,new;k=dt
    return dict(dt_s=h,steps=len(rows),final_v=old,exact_final_v=math.exp(-end/tau),
                max_error_v=max(abs(v-math.exp(-t/tau)) for t,v in rows),final_error_v=abs(old-math.exp(-end/tau)))


def generate():
    before=hashes(PATHS);n=BdfNetwork(200,model_parameters(1,"finite_transit"))
    initial,dc=n.initial_history();old=initial;rows=[]
    # Declared intervals exercise ratio 2, 1/2, 1 and rapid reductions.
    for h in (25e-6,25e-6,50e-6,25e-6,12.5e-6,1e-9,2e-9):
        new,diag=n.advance(old,10.,h)
        virtual,c=(n.effective_history(old,h) if old.previous is not None else (old.current,dict(effective_dt_s=h)))
        ev=n.network.increment_evaluator(10.,virtual,c["effective_dt_s"])
        delta=np.array(diag["increment_v"]);_,j=ev(delta);_,fd=ev(delta,use_fd=True)
        replay,d=n.advance(old,10.,h,use_fd=True)
        rows.append(dict(old=pack(old),new=pack(new),dt_s=h,diagnostics=diag,
            publication=publication_check(n,old,new,h,diag),
            fd_max_node_difference_v=float(np.max(np.abs(np.array(replay.current.joint.node_v)-new.current.joint.node_v))),
            fd_diagnostics=d,jacobian_max_scaled_difference=float(np.max(np.abs(j-fd)/(1+np.abs(j))))))
        old=new
    if hashes(PATHS)!=before:raise ValueError("BDF probe sources changed")
    return dict(schema="rf-d/bdf-charge-probes/v1",source_sha256=before,environment=environment(),
        initial=pack(initial),dc_diagnostics=dc,intervals=rows,
        scalar_rc=[scalar_rc(h) for h in (10e-6,5e-6,2.5e-6,1.25e-6)],
        fixed_kcl_gate_a=1e-11,fixed_correction_gate_v=1e-8,jacobian_gate=1e-8,fd_voltage_gate_v=1e-8,
        history_reset_count=0,independent_spatial_oracle=False,physical_switching_admitted=False,
        temporal_refinement_admitted=False,audio_admitted=False,selected=None)


if __name__=="__main__":
    report=generate();OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(max_kcl_a=max(r["publication"]["max_published_kcl_a"] for r in report["intervals"]),
                         rc_errors=[r["final_error_v"] for r in report["scalar_rc"]])))
