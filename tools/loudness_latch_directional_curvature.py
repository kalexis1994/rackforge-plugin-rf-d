"""Analytic Decimal directional curvature of the conditional 94-node laws."""
from decimal import Decimal as D,localcontext
import math
import numpy as np
from circuit66_decimal_static import graph as audio_graph,evaluate as static_values,lift
from loudness_latch_bdf_memory_transfer import CHARGE_SCALE_C_PER_V


def graph(network,key=10.):
    n=network.network;g=audio_graph(n.joint.values);g["node_count"]=n.joint.n
    # R59 is one physical cross-boundary branch, not two grounded loads.
    r59=next(r for r in g["resistors"] if r["ref"]=="R59-VCA1")
    r59["right"]=n.joint.out
    contour=n.joint.contour;devices=contour.devices
    rails=dict(contour.rails,KEYBOARD_TRIGGER=key)
    g["fixed"].update({"contour/"+name:v for name,v in rails.items()})
    def node(name):
        alias=contour.alias[name]
        return 66+contour.index[alias] if alias in contour.index else "contour/"+alias
    for ref,a,b,ohm in contour.resistors:
        if ohm:g["resistors"].append(dict(ref=ref+"-contour",left=node(a),right=node(b),ohm=ohm))
    for p in contour.bjts:
        g["bjts"].append(dict(ref=p["ref"]+"-contour",base=node(p["base"]),collector=node(p["collector"]),
            emitter=node(p["emitter"]),polarity=1 if p["kind"]=="NPN" else -1,is_a=devices.is_a,
            vt=contour.vt,beta_forward=devices.beta_forward,beta_reverse=devices.beta_reverse))
    for p in contour.diodes:
        g["diodes"].append(dict(ref=p["ref"]+"-contour",anode=node(p["anode"]),cathode=node(p["cathode"]),
            is_a=devices.germanium_is_a if p["marking"]=="1N34A" else devices.silicon_is_a,
            ideality=devices.diode_ideality,vt=contour.vt))
    # The contour's 1/R59 grounded load is replaced by the cross branch above.
    if contour.load!=(1/68000,0.,0.):raise ValueError("registered R59 joint loading required")
    return g


def static_curvature(g,x,direction,precision=80):
    if len(x)!=g["node_count"] or len(direction)!=len(x):raise ValueError("complete node direction required")
    with localcontext() as ctx:
        ctx.prec=precision;v=[lift(u) for u in x];u=[lift(t) for t in direction]
        fixed={k:lift(t) for k,t in g["fixed"].items()};out=[D(0)]*len(v)
        def voltage(i):return v[i] if isinstance(i,int) else fixed[i]
        def slope(i):return u[i] if isinstance(i,int) else D(0)
        def add(i,value):
            if isinstance(i,int):out[i]+=value
        for q in g["bjts"]:
            b,c,e=q["base"],q["collector"],q["emitter"];s=q["polarity"]
            vt=lift(q["vt"]);bf=lift(q["beta_forward"]);br=lift(q["beta_reverse"]);sat=lift(q["is_a"])
            be=s*(voltage(b)-voltage(e))/vt;bc=s*(voltage(b)-voltage(c))/vt
            if max(be,bc)>45:raise ValueError("BJT exponential domain exceeded")
            f=sat*be.exp()*(s*(slope(b)-slope(e))/vt)**2
            r=sat*bc.exp()*(s*(slope(b)-slope(c))/vt)**2
            ib=s*(f/bf+r/br);ic=s*(f-(1+1/br)*r)
            add(b,ib);add(c,ic);add(e,-ib-ic)
        for q in g["diodes"]:
            a,c=q["anode"],q["cathode"];vt=lift(q["ideality"])*lift(q["vt"])
            exponent=(voltage(a)-voltage(c))/vt
            if exponent>45:raise ValueError("diode exponential domain exceeded")
            value=lift(q["is_a"])*exponent.exp()*((slope(a)-slope(c))/vt)**2
            add(a,value);add(c,-value)
        return out


def junction_values(depletion,transit,sat,scale,voltage):
    """Q, Q', Q'' with the same piecewise knee and low-injection law."""
    v=lift(voltage);cj=lift(depletion.cj0_f);potential=lift(depletion.potential_v)
    m=lift(depletion.grading);fc=lift(depletion.forward_fraction)
    knee=lift(depletion.forward_fraction*depletion.potential_v)
    def below(value):
        log=(1-value/potential).ln();power=1-m
        integral=-log if not power else -( (power*log).exp()-1 )/power
        q=cj*potential*integral;c=cj*(-m*log).exp()
        return q,c
    if v<knee:
        q,c=below(v);second=c*m/(potential-v)
    else:
        qk,ck=below(knee);second=ck*m/(potential*(1-fc));delta=v-knee
        q=qk+ck*delta+second*delta*delta/2;c=ck+second*delta
    exponent=v/lift(scale)
    if exponent>45:raise ValueError("charge exponential domain exceeded")
    t=lift(transit);s=lift(sat);vt=lift(scale);ef=s*exponent.exp()
    return q+t*(ef-s),c+t*ef/vt,second+t*ef/(vt*vt)


def charge_terms(network,x,direction,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision;n=network.network;l=n.latch;p=l.device.parameters
        charge=[D(0)]*n.joint.n;curvature=[D(0)]*n.joint.n;publication=[D(0)]*25
        for k,terminals in enumerate(l.terminals):
            v=[lift(x[i] if i is not None else fixed) for i,fixed in terminals]
            u=[lift(direction[i]) if i is not None else D(0) for i,_ in terminals]
            b,c,e=[i for i,_ in terminals];s=p.polarity
            for index,other,dep,transit,scale in ((21+2*k,2,p.depletion_be,p.transit_forward_s,p.emission_be_v),
                                                (22+2*k,1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
                q,_,q2=junction_values(dep,transit,p.saturation_a,scale,s*(v[0]-v[other]))
                value=q2*(s*(u[0]-u[other]))**2
                publication[index]=value/lift(CHARGE_SCALE_C_PER_V)
                for i,sign in ((b,s),((e if other==2 else c),-s)):
                    if i is not None:charge[i]+=sign*q;curvature[i]+=sign*value
        return charge,curvature,publication


def evaluate(network,g,x,direction,dt_s,precision=80):
    if not math.isfinite(dt_s) or dt_s<=0:raise ValueError("positive finite effective interval required")
    with localcontext() as ctx:
        ctx.prec=precision
        static=static_curvature(g,x,direction,precision)
        _,charge,pub=charge_terms(network,x,direction,precision)
        residual=[a+b/lift(dt_s) for a,b in zip(static,charge)]
        return dict(static_a=static,charge_c=charge,residual_a=residual,publication_coordinate_v=pub)


def residual_values(network,g,x,dt_s,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision
        r,_=static_values(g,x,precision,jacobian=False)
        q,_,_=charge_terms(network,x,[D(0)]*len(x),precision)
        return [a+b/lift(dt_s) for a,b in zip(r,q)]


def finite_difference(network,g,x,direction,dt_s,epsilon,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision;h=lift(epsilon);nodes=[lift(v) for v in x];u=[lift(v) for v in direction]
        plus=[v+h*d for v,d in zip(nodes,u)];minus=[v-h*d for v,d in zip(nodes,u)]
        rp=residual_values(network,g,plus,dt_s,precision);rm=residual_values(network,g,minus,dt_s,precision)
        r0=residual_values(network,g,nodes,dt_s,precision)
        # Publication coordinates need branch QBE/QBC, not terminal sums.
        pub=[];p=network.network.latch.device.parameters
        for terminals in network.network.latch.terminals:
            vv=[[v[i] if i is not None else lift(fixed) for i,fixed in terminals] for v in (plus,nodes,minus)]
            for other,dep,t,scale in ((2,p.depletion_be,p.transit_forward_s,p.emission_be_v),
                                     (1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
                charges=[junction_values(dep,t,p.saturation_a,scale,p.polarity*(v[0]-v[other]))[0] for v in vv]
                pub.append((charges[0]-2*charges[1]+charges[2])/(h*h*lift(CHARGE_SCALE_C_PER_V)))
        return dict(residual_a=[(a-2*b+c)/(h*h) for a,b,c in zip(rp,r0,rm)],publication_coordinate_v=[D(0)]*21+pub)


def metrics(reference,candidate):
    with localcontext() as ctx:
        ctx.prec=80
        ratios=[abs(lift(b)-lift(a))/(lift(1e-30)+lift(1e-8)*abs(lift(a))) for a,b in zip(reference,candidate)]
        i=max(range(len(ratios)),key=ratios.__getitem__)
        return dict(maximum_scaled_error=float(ratios[i]),index=i,passed=ratios[i]<1)


def floats(vector):return np.array([float(v) for v in vector])
