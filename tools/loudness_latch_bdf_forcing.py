"""Lifted coarse-equation forcing relative to sampled fine states, offline only."""
from decimal import Decimal as D,localcontext
import numpy as np
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift
from loudness_latch_bdf_memory_transfer import stamps,CHARGE_SCALE_C_PER_V


def nodes(state):
    return [lift(a)+lift(b) for a,b in zip(state.joint.node_v,state.node_low_v)]


def memories(state):
    return [lift(a)+lift(b) for a,b in state.capacitor_pairs_v]+[
        lift(q)/lift(CHARGE_SCALE_C_PER_V) for device in state.latch.devices for q in (device.be_c,device.bc_c)]


def difference(a,b,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision
        return dict(node_v=[x-y for x,y in zip(nodes(a),nodes(b))],
                    memory_v=[x-y for x,y in zip(memories(a),memories(b))])


def virtual(current,previous,gamma,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision
        return [lift(1+gamma)*lift(a)-lift(gamma)*lift(b) for a,b in zip(current,previous)]


def matvec(matrix,vector):
    return [sum((lift(a)*lift(b) for a,b in zip(row,vector)),D(0)) for row in matrix]


def forcing(network,g,base,reference,virtual_delta,dt_s,precision=80):
    """Independent nonlinear difference; never infer r from J times the error."""
    with localcontext() as ctx:
        ctx.prec=precision
        x=nodes(base.current);y=nodes(reference);delta=[b-a for a,b in zip(x,y)]
        rb=curvature.residual_values(network,g,x,dt_s,precision)
        rr=curvature.residual_values(network,g,y,dt_s,precision)
        b,p,d=stamps(network,base,dt_s)
        residual=[a-z for a,z in zip(rr,rb)]
        for left,right,_,cap,resistance in network.network.branches:
            value=lift(1/(dt_s/cap+resistance))*(delta[left]-(D(0) if right is None else delta[right]))
            residual[left]+=value
            if right is not None:residual[right]-=value
        bv=matvec(b,virtual_delta)
        residual=[a-z for a,z in zip(residual,bv)]
        publication=[a+z for a,z in zip(matvec(p,delta),matvec(d,virtual_delta))]
        params=network.network.latch.device.parameters
        for k,terminals in enumerate(network.network.latch.terminals):
            for j,other,dep,t,scale in ((21+2*k,2,params.depletion_be,params.transit_forward_s,params.emission_be_v),
                                      (22+2*k,1,params.depletion_bc,params.transit_reverse_s,params.emission_bc_v)):
                charges=[]
                for values in (x,y):
                    v=[values[i] if i is not None else lift(fixed) for i,fixed in terminals]
                    charges.append(curvature.junction_values(dep,t,params.saturation_a,scale,
                        params.polarity*(v[0]-v[other]))[0])
                publication[j]=(charges[1]-charges[0])/lift(CHARGE_SCALE_C_PER_V)
        actual=difference(reference,base.current,precision)
        offset=[a-z for a,z in zip(actual['memory_v'],publication)]
        return dict(residual_a=residual,publication_offset_v=offset,publication_difference_v=publication,
                    node_difference_v=actual['node_v'],memory_difference_v=actual['memory_v'])


def serial(values):
    return {key:[str(v) for v in vector] for key,vector in values.items()}


def floats(values):return np.array([float(v) for v in values])
