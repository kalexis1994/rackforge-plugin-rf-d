"""Outward rational constitutive charge and reconstructed residual L1 bounds."""
from fractions import Fraction as F
from functools import lru_cache
from math import factorial
import loudness_latch_charge_enclosure as base
import loudness_latch_dense_charge as poly
DEGREE=6
CELLS=8
LOG_TERMS=64


def enclosing(a,b):
    if a>b:raise ValueError('ordered interval required')
    return base.down(a),base.up(b)


def add(a,b):return enclosing(a[0]+b[0],a[1]+b[1])
def neg(a):return -a[1],-a[0]
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    v=[x*y for x in a for y in b];return enclosing(min(v),max(v))
def scale(a,c):return mul(a,(F(c),F(c)))
def div(a,b):
    if b[0]<=0<=b[1]:raise ValueError('division interval contains zero')
    return mul(a,enclosing(1/b[1],1/b[0]))
def magnitude(a):return max(map(abs,a))
def minimum_magnitude(a):return F(0) if a[0]<=0<=a[1] else min(map(abs,a))


def atanh_log(z):
    zz=enclosing(z,z);z2=mul(zz,zz);power=zz;total=(F(0),F(0))
    if not 0<=zz[0]<=zz[1]<1 or z2[1]>=1:raise ValueError('positive log series domain required')
    for k in range(LOG_TERMS):
        total=add(total,scale(power,F(2,2*k+1)));power=mul(power,z2)
    tail=2*power[1]/((2*LOG_TERMS+1)*(1-z2[1]))
    return enclosing(total[0],total[1]+tail)


@lru_cache(maxsize=1)
def log_two():return atanh_log(F(1,3))


def log_bounds(x):
    x=F(x)
    if x<=0:raise ValueError('positive logarithm argument required')
    y=x;k=0
    while y<1:
        y*=2;k-=1
        if k<-4096:raise ValueError('log reduction budget exceeded')
    while y>=2:
        y/=2;k+=1
        if k>4096:raise ValueError('log reduction budget exceeded')
    return add(atanh_log((y-1)/(y+1)),scale(log_two(),k))


def exp_interval(a):return base.exp_bounds(a[0])[0],base.exp_bounds(a[1])[1]
def positive_power(a,p):
    if a[0]<=0:raise ValueError('positive power base required')
    logs=(log_bounds(a[0])[0],log_bounds(a[1])[1])
    return exp_interval(scale(logs,p))


def junction_bounds(dep,transit,sat,emission,v):
    """Point Q and C intervals; preserve rounded binary64 knee and FC denominator."""
    v=F(v);cj=F(dep.cj0_f);potential=F(dep.potential_v);m=F(dep.grading);fc=F(dep.forward_fraction)
    knee=F(dep.forward_fraction*dep.potential_v);t=F(transit);sat=F(sat);emission=F(emission)
    if not (cj>=0 and potential>0 and 0<=m<=1 and 0<=fc<1 and knee<potential and t>=0 and sat>0 and emission>0):
        raise ValueError('declared monotone junction domain required')
    def below(value):
        argument=1-value/potential;power=1-m
        logs=log_bounds(argument)
        integral=neg(logs) if not power else scale(sub((F(1),F(1)),exp_interval(scale(logs,power))),1/power)
        return scale(integral,cj*potential),scale(exp_interval(scale(logs,-m)),cj)
    if v<knee:q,c=below(v)
    else:
        qk,ck=below(knee);second=scale(ck,m/(potential*(1-fc)));delta=v-knee
        q=add(add(qk,scale(ck,delta)),scale(second,delta*delta/2));c=add(ck,scale(second,delta))
    exponent=v/emission
    if exponent>45:raise ValueError('charge exponential domain exceeded')
    ef=scale(base.exp_bounds(exponent),sat)
    return add(q,scale(sub(ef,(sat,sat)),t)),add(c,scale(ef,t/emission))


def polynomial_range(p,left=F(0),right=F(1)):
    b=poly.bernstein(p,left,right);return min(b),max(b)


def charge_stamp(network,values):
    if len(values)!=25:raise ValueError('25 charge intervals required')
    nodes=[(F(0),F(0)) for _ in range(94)];boundary=(F(0),F(0))
    def stamp(a,b,value):
        nonlocal boundary
        if a is None:boundary=add(boundary,value)
        else:nodes[a]=add(nodes[a],value)
        if b is None:boundary=sub(boundary,value)
        else:nodes[b]=sub(nodes[b],value)
    for (a,b,_,_,_),v in zip(network.network.branches,values[:21]):stamp(a,b,v)
    s=network.network.latch.device.parameters.polarity
    for i,terminals in enumerate(network.network.latch.terminals):
        b,c,e=[j for j,_ in terminals];stamp(b,e,scale(values[21+2*i],s));stamp(b,c,scale(values[22+2*i],s))
    return nodes,boundary


def polynomial_residual(network,g,prepared,left,right):
    """Degree <=18 polynomial plus uniform absolute A errors on normalized z."""
    x=[poly.reparameterize(p,left,right) for p in prepared['x']]
    duration=prepared['h']*(right-left);out=[(F(0),) for _ in x];errors=[F(0)]*len(x)
    def voltage(i):return x[i] if isinstance(i,int) else (F(g['fixed'][i]),)
    def diff(a,b):return poly.add(voltage(a),poly.scale(voltage(b),-1))
    def stamp(node,p,error,coefficient):
        if isinstance(node,int):
            out[node]=poly.add(out[node],poly.scale(p,coefficient));errors[node]+=abs(coefficient)*error
    for r in g['resistors']+g['conductances']:
        conductance=1/F(r['ohm']) if 'ohm' in r else F(r['siemens']);p=poly.scale(diff(r['left'],r['right']),conductance)
        stamp(r['left'],p,F(0),F(1));stamp(r['right'],p,F(0),F(-1))
    def exponential(p,sat,stamps):
        b=poly.bernstein(p)
        if max(b)>45:raise ValueError('whole static exponent domain exceeded')
        center=poly.evaluate(p,F(1,2));delta=poly.add(p,(-center,));rho=max(map(abs,poly.bernstein(delta)))
        power=(F(1),);t=(F(0),)
        for k in range(DEGREE+1):
            t=poly.add(t,poly.scale(power,F(1,factorial(k))))
            if k<DEGREE:power=poly.multiply(power,delta)
        lo,hi=base.exp_bounds(center);mid=(lo+hi)/2
        error=(hi-lo)/2*max(map(abs,poly.bernstein(t)))+base.exp_bounds(center+rho)[1]*rho**(DEGREE+1)/factorial(DEGREE+1)
        current=poly.scale(poly.add(poly.scale(t,mid),(F(-1),)),sat)
        for node,coefficient in stamps:stamp(node,current,sat*error,coefficient)
    for q in g['bjts']:
        b,c,e=q['base'],q['collector'],q['emitter'];s=F(q['polarity']);bf=F(q['beta_forward']);br=F(q['beta_reverse']);sat=F(q['is_a'])
        exponential(poly.scale(diff(b,e),s/F(q['vt'])),sat,((b,s/bf),(c,s),(e,-s*(1+1/bf))))
        exponential(poly.scale(diff(b,c),s/F(q['vt'])),sat,((b,s/br),(c,-s*(1+1/br)),(e,s)))
    for d in g['diodes']:
        a,c=d['anode'],d['cathode'];exponential(poly.scale(diff(a,c),1/(F(d['ideality'])*F(d['vt']))),F(d['is_a']),((a,F(1)),(c,F(-1))))
    q=[poly.reparameterize(p,left,right) for p in prepared['q']];rates=[poly.scale(poly.differentiate(p),1/duration) for p in q]
    for (a,b,_,_,_),p in zip(network.network.branches,rates[:21]):stamp(a,p,F(0),F(1));stamp(b,p,F(0),F(-1))
    s=F(network.network.latch.device.parameters.polarity)
    for i,terminals in enumerate(network.network.latch.terminals):
        b,c,e=[j for j,_ in terminals]
        for other,p in ((e,rates[21+2*i]),(c,rates[22+2*i])):stamp(b,p,F(0),s);stamp(other,p,F(0),-s)
    # Quantize coefficients only after cancellation; include all coefficient errors uniformly on z in [0,1].
    rounded=[]
    for j,p in enumerate(out):
        dyadic=tuple(base.down(a) for a in p);errors[j]=base.up(errors[j]+sum((abs(a-b) for a,b in zip(p,dyadic)),F(0)));rounded.append(dyadic)
    return rounded,errors,rates


def residual_bounds(network,g,prepared,left,right):
    residual,errors,rates=polynomial_residual(network,g,prepared,left,right)
    duration=prepared['h']*(right-left);p=network.network.latch.device.parameters
    qleft=[];qright=[];junctions=[]
    for voltage,dep,transit,emission in prepared['junctions']:
        v=poly.reparameterize(voltage,left,right);junctions.append((v,dep,transit,emission))
        qleft.append(junction_bounds(dep,transit,p.saturation_a,emission,poly.evaluate(v,F(0)))[0])
        qright.append(junction_bounds(dep,transit,p.saturation_a,emission,poly.evaluate(v,F(1)))[0])
    delta=[(poly.evaluate(q,right)-poly.evaluate(q,left),)*2 for q in prepared['q'][:21]]+[sub(b,a) for a,b in zip(qleft,qright)]
    dynamic,boundary=charge_stamp(network,delta)
    poly_l1=[F(0)]*94;const_l1=[F(0)]*94;pointwise=[F(0)]*94;mismatch_max=[F(0)]*4;cells=[]
    for k in range(CELLS):
        a=F(k,CELLS);b=F(k+1,CELLS);mismatch=[]
        for j,(v,dep,t,emission) in enumerate(junctions):
            vr=polynomial_range(v,a,b)
            # C(v) is continuous and nondecreasing on the declared domain, including the knee.
            cr=(junction_bounds(dep,t,p.saturation_a,emission,vr[0])[1][0],
                junction_bounds(dep,t,p.saturation_a,emission,vr[1])[1][1])
            slope=scale(polynomial_range(poly.differentiate(v),a,b),1/duration)
            current=mul(cr,slope);difference=sub(current,polynomial_range(rates[21+j],a,b))
            mismatch.append(difference);mismatch_max[j]=max(mismatch_max[j],magnitude(difference))
        correction,_=charge_stamp(network,[(F(0),F(0))]*21+mismatch)
        row=[]
        for j,r in enumerate(residual):
            rr=polynomial_range(r,a,b);rp=enclosing(rr[0]-errors[j],rr[1]+errors[j]);rc=add(rp,correction[j])
            poly_l1[j]+=duration*magnitude(rp)/CELLS;const_l1[j]+=duration*magnitude(rc)/CELLS
            pointwise[j]=max(pointwise[j],magnitude(rc));row.append(rc)
        cells.append(row)
    return dict(delta_constitutive_c=delta,dynamic_constitutive_c=dynamic,dynamic_boundary_c=boundary,
        qleft_c=qleft,qright_c=qright,polynomial_l1_upper_c=list(map(base.up,poly_l1)),
        constitutive_l1_upper_c=list(map(base.up,const_l1)),constitutive_pointwise_upper_a=list(map(base.up,pointwise)),
        polynomial_uniform_remainder_a=errors,nonlinear_rate_mismatch_upper_a=list(map(base.up,mismatch_max)),cells_a=cells)
