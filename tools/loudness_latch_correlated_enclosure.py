"""Correlated polynomial charge rates on frozen smooth pieces; offline only."""
from fractions import Fraction as F
from math import factorial
import loudness_latch_constitutive_enclosure as old
import loudness_latch_charge_balance as balance
import loudness_latch_dense_charge as poly
DEGREE=6
CELLS=8


def intersect(a,b):
    lo=max(a[0],b[0]);hi=min(a[1],b[1])
    if lo>hi:raise ValueError('independent enclosures are disjoint')
    return lo,hi


def active_nodes(network):return sorted({j for terminals in network.network.latch.terminals for j,_ in terminals if j is not None})


def restricted_graph(g,active):
    active=set(active);result=g.copy()
    result['resistors']=[r for r in g['resistors'] if r['left'] in active or r['right'] in active]
    result['conductances']=[r for r in g['conductances'] if r['left'] in active or r['right'] in active]
    result['bjts']=[r for r in g['bjts'] if any(r[k] in active for k in ('base','collector','emitter'))]
    result['diodes']=[r for r in g['diodes'] if r['anode'] in active or r['cathode'] in active]
    return result


def capacitance_polynomial(v,dep,t,sat,emission,a,b,below):
    """Polynomial C(v(z)) and uniform F error on one certified piece."""
    cj=F(dep.cj0_f);vj=F(dep.potential_v);m=F(dep.grading);fc=F(dep.forward_fraction)
    knee=F(dep.forward_fraction*dep.potential_v);t=F(t);sat=F(sat);emission=F(emission)
    # Reuse the declared parameter/point domain guard even for zero prefactors.
    center=poly.evaluate(v,(a+b)/2);old.junction_bounds(dep,t,sat,emission,center)
    vr=old.polynomial_range(v,a,b)
    if vr[1]/emission>45:raise ValueError('whole charge exponent domain exceeded')
    if below:
        if center>=vj:raise ValueError('depletion expansion center outside domain')
        w=poly.scale(poly.add(v,(-center,)),1/(vj-center));rho=max(map(abs,poly.bernstein(w,a,b)))
        if rho>=1:raise ValueError('declared binomial remainder domain exceeded')
        amplitude=old.scale(old.positive_power((1-center/vj,1-center/vj),-m),cj)
        power=(F(1),);series=(F(0),);rising=F(1)
        for k in range(DEGREE+1):
            series=poly.add(series,poly.scale(power,rising/factorial(k)))
            rising*=m+k
            if k<DEGREE:power=poly.multiply(power,w)
        tail=rising/factorial(DEGREE+1)*rho**(DEGREE+1)*old.positive_power((1-rho,1-rho),-m-DEGREE-1)[1]
        middle=sum(amplitude)/2
        dep_poly=poly.scale(series,middle)
        dep_error=(amplitude[1]-amplitude[0])/2*max(map(abs,poly.bernstein(series,a,b)))+amplitude[1]*tail
    else:
        amplitude=old.scale(old.positive_power((1-knee/vj,1-knee/vj),-m),cj)
        shape=poly.add((F(1),),poly.scale(poly.add(v,(-knee,)),m/(vj*(1-fc))))
        middle=sum(amplitude)/2;dep_poly=poly.scale(shape,middle)
        dep_error=(amplitude[1]-amplitude[0])/2*max(map(abs,poly.bernstein(shape,a,b)));rho=F(0)
    exponent=poly.scale(v,1/emission);c=center/emission;delta=poly.add(exponent,(-c,));exp_rho=max(map(abs,poly.bernstein(delta,a,b)))
    power=(F(1),);series=(F(0),)
    for k in range(DEGREE+1):
        series=poly.add(series,poly.scale(power,F(1,factorial(k))))
        if k<DEGREE:power=poly.multiply(power,delta)
    amplitude=old.scale(old.base.exp_bounds(c),t*sat/emission);middle=sum(amplitude)/2
    diffusion=poly.scale(series,middle)
    diffusion_error=(amplitude[1]-amplitude[0])/2*max(map(abs,poly.bernstein(series,a,b)))+t*sat/emission*old.base.exp_bounds(c+exp_rho)[1]*exp_rho**(DEGREE+1)/factorial(DEGREE+1)
    raw=poly.add(dep_poly,diffusion);rounded=tuple(old.base.down(x) for x in raw)
    error=old.base.up(dep_error+diffusion_error+sum((abs(x-y) for x,y in zip(raw,rounded)),F(0)))
    return rounded,error,dict(below=below,binomial_rho=rho,exponential_rho=exp_rho,error_upper_f=error)


def correlated_bounds(network,g,prepared,left,right,prior):
    active=active_nodes(network);duration=prepared['h']*(right-left)
    residual,errors,rates=old.polynomial_residual(network,restricted_graph(g,active),prepared,left,right)
    plan=balance.partition(prepared,left,right);width=right-left
    smooth=[dict(a=(r['left']-left)/width,b=(r['right']-left)/width,below=r['below']) for r in plan['smooth']]
    bridges=[((a-left)/width,(b-left)/width) for a,b in plan['bridges']]
    junctions=[(poly.reparameterize(v,left,right),d,t,e) for v,d,t,e in prepared['junctions']]
    parameter=network.network.latch.device.parameters;s=F(parameter.polarity)
    models=[]
    for piece in smooth:
        correction={j:(F(0),) for j in active};correction_errors={j:F(0) for j in active};diagnostics=[];differences=[]
        for k,(v,dep,t,emission) in enumerate(junctions):
            cp,ce,diag=capacitance_polynomial(v,dep,t,parameter.saturation_a,emission,piece['a'],piece['b'],piece['below'][k])
            velocity=poly.scale(poly.differentiate(v),1/duration)
            difference=poly.add(poly.multiply(cp,velocity),poly.scale(rates[21+k],-1))
            error=ce*max(map(abs,poly.bernstein(velocity,piece['a'],piece['b'])))
            differences.append((difference,error));diagnostics.append(diag)
            b,c,e=[j for j,_ in network.network.latch.terminals[k//2]];other=e if k%2==0 else c
            for j,sign in ((b,s),(other,-s)):
                if j is not None:correction[j]=poly.add(correction[j],poly.scale(difference,sign));correction_errors[j]+=abs(sign)*error
        joint={};joint_errors={}
        for j in active:
            raw=poly.add(residual[j],correction[j]);rounded=tuple(old.base.down(v) for v in raw)
            joint[j]=rounded;joint_errors[j]=old.base.up(errors[j]+correction_errors[j]+sum((abs(x-y) for x,y in zip(raw,rounded)),F(0)))
        models.append(dict(piece=piece,joint=joint,errors=joint_errors,differences=differences,diagnostics=diagnostics))
    cuts=sorted({F(k,CELLS) for k in range(CELLS+1)}|{v for p in smooth for v in (p['a'],p['b'])}|{v for ab in bridges for v in ab})
    upper={j:F(0) for j in active};pointwise={j:F(0) for j in active};segments=[];mismatch_max=[F(0)]*4
    for a,b in zip(cuts,cuts[1:]):
        mid=(a+b)/2;old_cell=min(CELLS-1,int(mid*CELLS));model=next((m for m in models if m['piece']['a']<=a and b<=m['piece']['b']),None)
        raw_ranges={};difference_ranges=[]
        if model is not None:
            for p,error in model['differences']:
                lo,hi=old.polynomial_range(p,a,b);difference_ranges.append(old.enclosing(lo-error,hi+error))
            for j in active:
                lo,hi=old.polynomial_range(model['joint'][j],a,b);err=model['errors'][j];raw_ranges[j]=old.enclosing(lo-err,hi+err)
            kind='correlated-polynomial'
        else:
            if not any(l<=a and b<=r for l,r in bridges):raise ValueError('uncovered piece interval')
            for k,(v,dep,t,emission) in enumerate(junctions):
                vr=old.polynomial_range(v,a,b)
                cr=(old.junction_bounds(dep,t,parameter.saturation_a,emission,vr[0])[1][0],old.junction_bounds(dep,t,parameter.saturation_a,emission,vr[1])[1][1])
                velocity=old.scale(old.polynomial_range(poly.differentiate(v),a,b),1/duration)
                difference_ranges.append(old.sub(old.mul(cr,velocity),old.polynomial_range(rates[21+k],a,b)))
            correction,_=old.charge_stamp(network,[(F(0),F(0))]*21+difference_ranges)
            for j in active:
                lo,hi=old.polynomial_range(residual[j],a,b);raw_ranges[j]=old.add(old.enclosing(lo-errors[j],hi+errors[j]),correction[j])
            kind='bridge-rectangle'
        final=[]
        for j in active:
            inherited=tuple(map(F,prior['cells_a'][old_cell][j]));ab=intersect(raw_ranges[j],inherited)
            upper[j]+=duration*(b-a)*old.magnitude(ab);pointwise[j]=max(pointwise[j],old.magnitude(ab));final.append(ab)
        for k,ab in enumerate(difference_ranges):mismatch_max[k]=max(mismatch_max[k],old.magnitude(ab))
        segments.append(dict(left=a,right=b,old_cell=old_cell,kind=kind,raw_active_a=[raw_ranges[j] for j in active],active_a=final,difference_a=difference_ranges))
    l1=list(map(F,prior['constitutive_l1_upper_c']));point=list(map(F,prior['constitutive_pointwise_upper_a']))
    for j in active:l1[j]=old.base.up(upper[j]);point[j]=old.base.up(pointwise[j])
    if any(a>F(b) for a,b in zip(l1,prior['constitutive_l1_upper_c'])):raise ValueError('intersection did not preserve L1 bound')
    if any(a>F(b) for a,b in zip(point,prior['constitutive_pointwise_upper_a'])):raise ValueError('intersection did not preserve pointwise bound')
    if any(F(a)>b for a,b in zip(prior['constitutive_l1_lower_c'],l1)):raise ValueError('lower and upper L1 bounds disagree')
    return dict(active_nodes=active,segments=segments,constitutive_l1_upper_c=l1,constitutive_pointwise_upper_a=point,
        nonlinear_rate_mismatch_upper_a=list(map(old.base.up,mismatch_max)),
        capacitance_models=[dict(piece=m['piece'],diagnostics=m['diagnostics']) for m in models],
        smooth_pieces=len(smooth),bridges=len(bridges),whole_interval_below_10pa=max(point)<F(1e-11),
        maximum_pointwise_upper_a=max(point),bounds_nonincreasing=True,l1_lower_upper_consistent=True)
