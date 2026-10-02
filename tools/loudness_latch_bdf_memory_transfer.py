"""Fixed-clock tangent map for 21 voltage and four scaled charge memories."""
from dataclasses import replace
import math
import numpy as np
from loudness_latch_increment_reference import pair
from loudness_latch_bdf_reference import coefficients
from loudness_latch_bdf_transfer_solve import solve

CHARGE_SCALE_C_PER_V=1e-12  # Coordinate scale only, not a physical capacitance.


def incidence(n,left,right):
    row=np.zeros(n)
    if left is not None:row[left]+=1.
    if right is not None:row[right]-=1.
    return row


def memory_difference(a,b):
    caps=[math.fsum((*x,*(-v for v in y))) for x,y in zip(a.capacitor_pairs_v,b.capacitor_pairs_v)]
    charges=[math.fsum((x,-y))/CHARGE_SCALE_C_PER_V for da,db in zip(a.latch.devices,b.latch.devices)
             for x,y in ((da.be_c,db.be_c),(da.bc_c,db.bc_c))]
    return np.array(caps+charges)


def node_difference(a,b):
    return np.array([math.fsum((x,lx,-y,-ly)) for x,lx,y,ly in
                     zip(a.joint.node_v,a.node_low_v,b.joint.node_v,b.node_low_v)])


def perturb_state(network,state,delta):
    """Hypothetical stored-memory perturbation; never an accepted past solve."""
    delta=np.asarray(delta,dtype=float)
    if delta.shape!=(25,) or not np.isfinite(delta).all():raise ValueError("25 finite memory coordinates required")
    caps=tuple(pair((*p,d)) for p,d in zip(state.capacitor_pairs_v,delta[:21]))
    contour=replace(state.joint.contour,capacitor_v={ref:caps[18+k][0]
        for k,(ref,_,_,_) in enumerate(network.network.joint.contour.caps)})
    joint=replace(state.joint,audio_capacitor_v=tuple(p[0] for p in caps[:17]),c10_v=caps[17][0],contour=contour)
    devices=tuple(replace(d,be_c=math.fsum((d.be_c,CHARGE_SCALE_C_PER_V*delta[21+2*k])),
        bc_c=math.fsum((d.bc_c,CHARGE_SCALE_C_PER_V*delta[22+2*k]))) for k,d in enumerate(state.latch.devices))
    result=replace(state,joint=joint,latch=replace(state.latch,devices=devices),capacitor_pairs_v=caps)
    network.network.validate(result)
    return result


def perturb_history(network,old,current,previous):
    if old.previous is None:raise ValueError("two-state continuation required; no perturbation of DC startup")
    result=replace(old,current=perturb_state(network,old.current,current),
                   previous=perturb_state(network,old.previous,previous))
    network.validate(result)
    return result


def stamps(network,new,dt):
    n=network.network;nnode=n.joint.n
    b=np.zeros((nnode,25));p=np.zeros((25,nnode));direct=np.zeros((25,25))
    for k,(left,right,_,c,resistance) in enumerate(n.branches):
        row=incidence(nnode,left,right);g=1/(dt/c+resistance)
        b[:,k]=g*row
        weight=dt/(dt+c*resistance)
        p[k]=weight*row;direct[k,k]=1-weight
    charge=n.latch.evaluate(new.current.joint.node_v)
    for k,(terminals,(be,bc)) in enumerate(zip(n.latch.terminals,charge["junction_cap_f"])):
        base,collector,emitter=[i for i,_ in terminals]
        for j,row,cap in ((21+2*k,incidence(nnode,base,emitter),be),
                          (22+2*k,incidence(nnode,base,collector),bc)):
            b[:,j]=CHARGE_SCALE_C_PER_V/dt*row
            p[j]=cap/CHARGE_SCALE_C_PER_V*row
    return b,p,direct


def transfer(network,old,new,diag,use_fd=False):
    h=diag["actual_dt_s"];virtual,c=network.effective_history(old,h)
    dt=c["effective_dt_s"]
    evaluate=network.network.increment_evaluator(new.key_v,virtual,dt)
    _,j=evaluate(np.array(diag["increment_v"]),use_fd=use_fd)
    b,p,direct=stamps(network,new,dt)
    x,audit=solve(j,b);t=p@x+direct
    if not np.isfinite(x).all() or not np.isfinite(t).all():raise ValueError("finite transfer matrices required")
    return dict(coefficients=c,node_map=x,memory_map=t,linear_solve=audit,
        max_componentwise_backward_error=max(audit["binary_componentwise_backward_error"],
                                             audit["decimal80_componentwise_backward_error"]))


def propagate(operator,current,previous):
    gamma=operator["coefficients"]["gamma"]
    virtual=(1+gamma)*current-gamma*previous
    return operator["node_map"]@virtual,operator["memory_map"]@virtual
