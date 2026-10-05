"""Immutable preparation for exactly the frozen offline residual action arithmetic."""
from dataclasses import dataclass,replace
from fractions import Fraction as F
import hashlib,json
import loudness_latch_residual_action as reference
prior=reference.prior;iv=reference.iv;poly=reference.poly;up=reference.up;SUBCELLS=reference.SUBCELLS


def _serial(value):
    if isinstance(value,F):return str(value)
    if isinstance(value,dict):return {k:_serial(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_serial(v) for v in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(_serial(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def identity(inverse,scales,cover):
    # Entire cover includes radius, domains, partition and proof flags.
    return digest(dict(inverse=inverse,scales=scales,cover=cover))


@dataclass(frozen=True)
class Prepared:
    n:int
    x:tuple
    d:tuple
    e:tuple
    rows:tuple
    q:F
    scaled_x:tuple
    absolute_scaled_x:tuple
    tail_factors:tuple
    coarse_factors:tuple
    input_sha256:str
    state_sha256:str


def state_digest(state):
    return digest({name:getattr(state,name) for name in ('n','x','d','e','rows','q','scaled_x','absolute_scaled_x','tail_factors','coarse_factors','input_sha256')})


def prepare(inverse,scales,cover):
    n=len(inverse);x=tuple(tuple(F(v) for v in row) for row in inverse);d=tuple(map(F,scales))
    e=tuple(tuple(tuple(map(F,v)) for v in row) for row in cover['preconditioned_defect_intervals'])
    if not n or len(d)!=n or len(e)!=n or any(len(row)!=n for row in x+e) or any(v<=0 for v in d):
        raise ValueError('complete square preconditioner, positive scales and defect required')
    if any(len(v)!=2 or v[0]>v[1] for row in e for v in row):raise ValueError('ordered complete defect intervals required')
    rows=tuple(sum((iv.magnitude(v) for v in row),F(0)) for row in e);q=max(rows)
    if q!=F(cover['contraction_upper']) or not cover['strict_contraction'] or q>=1:
        raise ValueError('same strictly contracted mean descriptor required')
    scaled=tuple(tuple(d[i]*v for v in row) for i,row in enumerate(x))
    state=Prepared(n,x,d,e,rows,q,scaled,tuple(tuple(abs(v) for v in row) for row in scaled),
        tuple(v*q/(1-q) for v in rows),tuple(v/(1-q) for v in rows),identity(inverse,scales,cover),'')
    return replace(state,state_sha256=state_digest(state))


def verify(state,inverse,scales,cover):
    if not isinstance(state,Prepared):raise ValueError('identified immutable preparation required')
    if identity(inverse,scales,cover)!=state.input_sha256:raise ValueError('preparation input identity mismatch')
    if state_digest(state)!=state.state_sha256:raise ValueError('preparation state identity mismatch')
    return state


def enclose(state,inverse,scales,cover,compiled,remainder,left,right):
    verify(state,inverse,scales,cover)
    return _enclose(state,compiled,remainder,left,right)


def _compile(state,polynomials):
    x=state.x;d=state.d;p=[tuple(map(F,v)) for v in polynomials];n=state.n
    if not n or len(d)!=n or len(p)!=n or any(len(row)!=n for row in x) or any(v<=0 for v in d) or any(not v for v in p):
        raise ValueError('complete square preconditioner, positive scales and RHS polynomials required')
    out=[]
    for i,row in enumerate(x):
        total=(F(0),)
        for j,v in enumerate(row):
            if v:total=poly.add(total,poly.scale(p[j],state.scaled_x[i][j]))
        out.append(total)
    return out


def _enclose(state,compiled,remainder,left,right):
    n=state.n;d=state.d;x=state.x;p=[tuple(map(F,v)) for v in compiled];r=list(map(F,remainder))
    e=state.e
    if not n or len(d)!=n or len(p)!=n or len(r)!=n or len(e)!=n or any(len(row)!=n for row in x+e) or any(v<=0 for v in d) or min(r)<0 or F(left)>=F(right) or F(left)<0 or F(right)>1:
        raise ValueError('complete nonnegative remainder and normalized action partition required')
    if any(len(v)!=2 or v[0]>v[1] for row in e for v in row):raise ValueError('ordered complete defect intervals required')
    rows=state.rows;q=state.q
    yerrors=[sum((state.absolute_scaled_x[i][j]*r[j] for j,v in enumerate(row)),F(0)) for i,row in enumerate(x)]
    yranges=[]
    for pp,err in zip(p,yerrors):
        b=poly.bernstein(pp,F(left),F(right));yranges.append(iv.enclosing(min(b)-err,max(b)+err))
    peak=max(map(iv.magnitude,yranges));bounds=[];tails=[];corrections=[]
    for i,row in enumerate(e):
        correction=(F(0),F(0))
        for coefficient,yy in zip(row,yranges):
            if coefficient!=(F(0),F(0)):correction=iv.add(correction,iv.mul(coefficient,yy))
        tail=state.tail_factors[i]*peak;coarse=state.coarse_factors[i]*peak
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


def budgets(state,inverse,scales,cover,source,weights,metric):
    verify(state,inverse,scales,cover)
    if state.n!=119:raise ValueError("complete 119-equation budget required")
    if not metric['accepted']:raise ValueError('same accepted metric required')
    w=list(map(F,weights));p=[[F(v) for v in row] for row in metric['metric']];normal=2*F(metric['anchor_normalization_upper'])
    if len(w)!=25 or any(v<=0 for v in w) or normal<=0 or not prior.blocks.quadratic.ldlt(p)['positive_definite']:
        raise ValueError('positive complete memory norms required')
    compiled=_compile(state,source['polynomials']);subcells=[];direct=[F(0)]*94;l1=[F(0)]*22;last=F(0)
    duration=F(source['duration_s'])
    if duration<=0 or len(source['subcells'])!=SUBCELLS:raise ValueError('complete positive action support required')
    for row in source['subcells']:
        a,b=F(row['left']),F(row['right'])
        if a!=last or b<=a:raise ValueError('contiguous RHS remainder partition required')
        cert=_enclose(state,compiled,row['rhs_remainder_upper'],a,b);action=[tuple(map(F,v)) for v in cert['action_intervals']]
        for i in range(94):direct[i]=max(direct[i],iv.magnitude(action[i]))
        values=[w[i]*iv.magnitude(action[94+i]) for i in range(21)]
        values.append(prior.blocks.quadratic.quadratic_upper(p,[iv.scale(action[94+i],w[i]) for i in range(21,25)])/normal)
        for i,v in enumerate(values):l1[i]+=duration*(b-a)*v
        subcells.append(cert|dict(block_point_upper_v_s=list(map(str,values))));last=b
    if last!=1:raise ValueError('complete RHS action support required')
    return dict(compiled_preconditioned_polynomials=[list(map(str,p)) for p in compiled],subcells=subcells,
        nodal_direct_upper_v=list(map(str,direct)),block_forcing_l1_upper_v=list(map(lambda v:str(up(v)),l1)),
        action_enclosed=True,new_trajectory_solve=False,point_and_l1=True)


