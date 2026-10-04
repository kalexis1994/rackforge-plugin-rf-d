"""Signed polynomial inverse actions with uniform remainder and Neumann tail."""
from fractions import Fraction as F
import loudness_latch_fine_prefix as prior
iv=prior.real.tube.iv
poly=prior.real.poly
up=iv.base.up
SUBCELLS=8


def compile_polynomials(inverse,scales,polynomials):
    x=[[F(v) for v in row] for row in inverse];d=list(map(F,scales));p=[tuple(map(F,v)) for v in polynomials];n=len(x)
    if not n or len(d)!=n or len(p)!=n or any(len(row)!=n for row in x) or any(v<=0 for v in d) or any(not v for v in p):
        raise ValueError('complete square preconditioner, positive scales and RHS polynomials required')
    out=[]
    for i,row in enumerate(x):
        total=(F(0),)
        for j,v in enumerate(row):
            if v:total=poly.add(total,poly.scale(p[j],d[i]*v))
        out.append(total)
    return out


def enclose(inverse,scales,cover,compiled,remainder,left,right):
    n=len(inverse);d=list(map(F,scales));x=[[F(v) for v in row] for row in inverse];p=[tuple(map(F,v)) for v in compiled];r=list(map(F,remainder))
    e=[[tuple(map(F,v)) for v in row] for row in cover['preconditioned_defect_intervals']]
    if not n or len(d)!=n or len(p)!=n or len(r)!=n or len(e)!=n or any(len(row)!=n for row in x+e) or any(v<=0 for v in d) or min(r)<0 or F(left)>=F(right) or F(left)<0 or F(right)>1:
        raise ValueError('complete nonnegative remainder and normalized action partition required')
    if any(len(v)!=2 or v[0]>v[1] for row in e for v in row):raise ValueError('ordered complete defect intervals required')
    rows=[sum((iv.magnitude(v) for v in row),F(0)) for row in e];q=max(rows)
    if q!=F(cover['contraction_upper']) or not cover['strict_contraction'] or q>=1:
        raise ValueError('same strictly contracted mean descriptor required')
    yerrors=[sum((abs(d[i]*v)*r[j] for j,v in enumerate(row)),F(0)) for i,row in enumerate(x)]
    yranges=[]
    for pp,err in zip(p,yerrors):
        b=poly.bernstein(pp,F(left),F(right));yranges.append(iv.enclosing(min(b)-err,max(b)+err))
    peak=max(map(iv.magnitude,yranges));bounds=[];tails=[];corrections=[]
    for i,row in enumerate(e):
        correction=(F(0),F(0))
        for coefficient,yy in zip(row,yranges):
            if coefficient!=(F(0),F(0)):correction=iv.add(correction,iv.mul(coefficient,yy))
        tail=rows[i]*q/(1-q)*peak;coarse=rows[i]/(1-q)*peak
        a=max(yranges[i][0]+correction[0]-tail,yranges[i][0]-coarse)/d[i]
        b=min(yranges[i][1]+correction[1]+tail,yranges[i][1]+coarse)/d[i]
        if a>b:raise ValueError('empty same-action enclosure intersection')
        bounds.append(iv.enclosing(a,b));tails.append(str(up(tail/d[i])));corrections.append(correction)
    return dict(left=str(F(left)),right=str(F(right)),contraction_upper=str(q),row_defect_upper=list(map(str,rows)),
        preconditioned_remainder_upper=list(map(str,yerrors)),preconditioned_rhs_intervals=prior.real.tube.cells.packed_matrix([yranges])[0],
        preconditioned_peak_upper=str(peak),first_correction_intervals=prior.real.tube.cells.packed_matrix([corrections])[0],
        tail_upper=list(tails),action_intervals=prior.real.tube.cells.packed_matrix([bounds])[0],
        tail_policy='row_defect*q/(1-q)*max|D*X*rhs|/D_i',order=1,mean_descriptor_uncertainty_included=True,
        correlated_polynomial_preserved=True,independent_remainders_cancelled=False)


def rhs(network,graph,prepared,left,right):
    residual,errors,rates=iv.polynomial_residual(network,graph,prepared,F(left),F(right))
    duration=prepared['h']*(F(right)-F(left))
    equations=[poly.reparameterize(p,F(left),F(right)) for p in prepared['equations']]
    polynomials=residual+equations+[(F(0),)]*4
    parameters=network.network.latch.device.parameters
    junctions=[(poly.reparameterize(v,F(left),F(right)),dep,t,em) for v,dep,t,em in prepared['junctions']]
    remainders=[]
    for k in range(SUBCELLS):
        a,b=F(k,SUBCELLS),F(k+1,SUBCELLS);mismatch=[]
        for j,(v,dep,t,em) in enumerate(junctions):
            vr=iv.polynomial_range(v,a,b)
            cap=(iv.junction_bounds(dep,t,parameters.saturation_a,em,vr[0])[1][0],iv.junction_bounds(dep,t,parameters.saturation_a,em,vr[1])[1][1])
            slope=iv.scale(iv.polynomial_range(poly.differentiate(v),a,b),1/duration)
            mismatch.append(iv.sub(iv.mul(cap,slope),iv.polynomial_range(rates[21+j],a,b)))
        correction,_=iv.charge_stamp(network,[(F(0),F(0))]*21+mismatch)
        remainders.append(dict(left=str(a),right=str(b),nodal_uniform_remainder_a=list(map(str,errors)),
            constitutive_correction_intervals=prior.real.tube.cells.packed_matrix([correction])[0],
            rhs_remainder_upper=list(map(str,[up(err+iv.magnitude(c)) for err,c in zip(errors,correction)]+[F(0)]*25))))
    if len(polynomials)!=119:raise ValueError('full 119-equation RHS required')
    return dict(polynomials=[list(map(str,p)) for p in polynomials],subcells=remainders,duration_s=str(duration),
        polynomial_source='frozen degree-six constitutive residual and exact linear constraints',omitted_rhs_components=0)


def budgets(inverse,scales,cover,source,weights,metric):
    if not metric['accepted']:raise ValueError('same accepted metric required')
    w=list(map(F,weights));p=[[F(v) for v in row] for row in metric['metric']];normal=2*F(metric['anchor_normalization_upper'])
    if len(w)!=25 or any(v<=0 for v in w) or normal<=0 or not prior.blocks.quadratic.ldlt(p)['positive_definite']:
        raise ValueError('positive complete memory norms required')
    compiled=compile_polynomials(inverse,scales,source['polynomials']);subcells=[];direct=[F(0)]*94;l1=[F(0)]*22;last=F(0)
    duration=F(source['duration_s'])
    if duration<=0 or len(source['subcells'])!=SUBCELLS:raise ValueError('complete positive action support required')
    for row in source['subcells']:
        a,b=F(row['left']),F(row['right'])
        if a!=last or b<=a:raise ValueError('contiguous RHS remainder partition required')
        cert=enclose(inverse,scales,cover,compiled,row['rhs_remainder_upper'],a,b);action=[tuple(map(F,v)) for v in cert['action_intervals']]
        for i in range(94):direct[i]=max(direct[i],iv.magnitude(action[i]))
        values=[w[i]*iv.magnitude(action[94+i]) for i in range(21)]
        values.append(prior.blocks.quadratic.quadratic_upper(p,[iv.scale(action[94+i],w[i]) for i in range(21,25)])/normal)
        for i,v in enumerate(values):l1[i]+=duration*(b-a)*v
        subcells.append(cert|dict(block_point_upper_v_s=list(map(str,values))));last=b
    if last!=1:raise ValueError('complete RHS action support required')
    return dict(compiled_preconditioned_polynomials=[list(map(str,p)) for p in compiled],subcells=subcells,
        nodal_direct_upper_v=list(map(str,direct)),block_forcing_l1_upper_v=list(map(lambda v:str(up(v)),l1)),
        action_enclosed=True,new_trajectory_solve=False,point_and_l1=True)


def refine_metrics(original,action,include_memory):
    if not action['action_enclosed'] or not action['point_and_l1']:raise ValueError('complete action point and L1 bounds required')
    old=list(map(F,original['nodal_direct_v']));new=list(map(F,action['nodal_direct_upper_v']))
    if len(old)!=94 or len(new)!=94 or min(old+new)<0:raise ValueError('complete nonnegative nodal action required')
    result=original|dict(nodal_direct_v=list(map(str,[min(a,b) for a,b in zip(old,new)])))
    if include_memory:
        old=list(map(F,original['block_forcing_l1_v']));new=list(map(F,action['block_forcing_l1_upper_v']))
        if len(old)!=22 or len(new)!=22 or min(old+new)<0:raise ValueError('complete nonnegative block action required')
        result['block_forcing_l1_v']=list(map(str,[min(a,b) for a,b in zip(old,new)]))
    return result
