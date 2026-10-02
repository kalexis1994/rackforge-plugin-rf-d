"""Continuous charge descriptor and exact inverse certificate for lifted matrices."""
from decimal import localcontext
from fractions import Fraction as F
import numpy as np
from circuit66_decimal_static import evaluate,lift
from loudness_latch_directional_curvature import junction_values
from loudness_latch_bdf_memory_transfer import CHARGE_SCALE_C_PER_V,incidence
from loudness_latch_bdf_transfer_solve import solve
from loudness_latch_charge_enclosure import exp_bounds


def descriptor(network,g,x,precision=100):
    """H [delta v; delta ydot] = [-r; -delta y-d] plus nonlinear terms."""
    n=network.network;nv=n.joint.n;nm=len(n.branches)+4
    with localcontext() as ctx:
        ctx.prec=precision
        _,j=evaluate(g,x,precision)
        h=[[lift(0) for _ in range(nv+nm)] for _ in range(nv+nm)]
        for i,row in enumerate(j):h[i][:nv]=row
        columns=[];scales=[];taus=[]
        for k,(left,right,_,cap,resistance) in enumerate(n.branches):
            a=incidence(nv,left,right);scale=lift(cap);tau=lift(cap)*lift(resistance)
            columns.append(a.tolist());scales.append(scale);taus.append(tau)
            for i,v in enumerate(a):
                h[i][nv+k]=lift(v)*scale;h[nv+k][i]=-lift(v)
            h[nv+k][nv+k]=tau
        p=n.latch.device.parameters
        for k,terminals in enumerate(n.latch.terminals):
            vv=[lift(x[i]) if i is not None else lift(fixed) for i,fixed in terminals]
            base,collector,emitter=[i for i,_ in terminals]
            for other,index,dep,transit,emission in ((2,21+2*k,p.depletion_be,p.transit_forward_s,p.emission_be_v),
                                                   (1,22+2*k,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
                a=incidence(nv,base,emitter if other==2 else collector)*p.polarity
                _,cap,_=junction_values(dep,transit,p.saturation_a,emission,p.polarity*(vv[0]-vv[other]))
                scale=lift(CHARGE_SCALE_C_PER_V)
                columns.append(a.tolist());scales.append(scale);taus.append(lift(0))
                for i,v in enumerate(a):
                    h[i][nv+index]=lift(v)*scale;h[nv+index][i]=-cap/scale*lift(v)
        return h,dict(incidence_columns=columns,coordinate_scales_c_per_v=list(map(str,scales)),
                      rc_time_constants_s=list(map(str,taus)))


def exact_rank(matrix):
    a=[[F(v) for v in row] for row in matrix];rank=0;pivots=[]
    for col in range(len(a[0])):
        pivot=next((i for i in range(rank,len(a)) if a[i][col]),None)
        if pivot is None:continue
        a[rank],a[pivot]=a[pivot],a[rank];d=a[rank][col]
        a[rank]=[v/d for v in a[rank]]
        for i in range(rank+1,len(a)):
            c=a[i][col]
            if c:a[i]=[u-c*v for u,v in zip(a[i],a[rank])]
        pivots.append(col);rank+=1
    return dict(rank=rank,pivot_columns=pivots)


def inverse_certificate(h,x,column_scales):
    """E=I-D X H D^-1; ||E||inf<1 proves invertibility of exact binary H."""
    n=len(h)
    if len(x)!=n or any(len(row)!=n for row in (*h,*x)) or len(column_scales)!=n:
        raise ValueError('complete square matrix, inverse and scales required')
    hf=[[F(v) for v in row] for row in h];xf=[[F(v) for v in row] for row in x]
    d=list(map(F,column_scales))
    if any(v<=0 for v in d):raise ValueError('positive scales required')
    columns=[[(k,hf[k][j]) for k in range(n) if hf[k][j]] for j in range(n)]
    sums=[]
    for i in range(n):
        sums.append(sum((abs((F(i==j)-sum((xf[i][k]*v for k,v in columns[j]),F(0)))*d[i]/d[j])
                         for j in range(n)),F(0)))
    q=max(sums)
    if q>=1:raise ValueError('Neumann contraction failed: '+str(q))
    # |H^-1_ij-X_ij| <= q/(1-q) * max_k |D_k X_kj| / D_i.
    peaks=[max(abs(d[k]*xf[k][j]) for k in range(n)) for j in range(n)]
    errors=[[q/(1-q)*v/di for v in peaks] for di in d]
    return errors,dict(scaled_left_defect_row_sums=list(map(str,sums)),
        contraction_upper=str(q),strict_contraction=True,exact_binary_matrix_only=True,
        error_column_peaks=list(map(str,peaks)),column_scales=list(map(str,d)))


def frozen_budget(x,errors,nv,r_l1,d_l1,r_point,d_point,duration):
    """Rational Gronwall budget for a constant certified lifted descriptor only."""
    n=len(x);nm=n-nv;duration=F(duration)
    if duration<=0 or any(F(v)<0 for group in (r_l1,d_l1,r_point,d_point) for v in group):
        raise ValueError('positive duration and nonnegative residual bounds required')
    if any(len(v)!=k for v,k in ((r_l1,nv),(r_point,nv),(d_l1,nm),(d_point,nm))):
        raise ValueError('complete nodal and constitutive bounds required')
    xf=[[F(v) for v in row] for row in x]
    absolute=[[abs(v)+e for v,e in zip(row,err)] for row,err in zip(xf,errors)]
    mu=max(-xf[nv+i][nv+i]+errors[nv+i][nv+i]+sum((absolute[nv+i][nv+j] for j in range(nm) if j!=i),F(0))
           for i in range(nm))
    forcing=[sum((absolute[nv+i][j]*F(v) for j,v in enumerate(r_l1)),F(0))+
             sum((absolute[nv+i][nv+j]*F(v) for j,v in enumerate(d_l1)),F(0)) for i in range(nm)]
    node_forcing=[sum((absolute[i][j]*F(v) for j,v in enumerate(r_point)),F(0))+
                  sum((absolute[i][nv+j]*F(v) for j,v in enumerate(d_point)),F(0)) for i in range(nv)]
    node_gain=max(sum(row[nv:],F(0)) for row in absolute[:nv])
    exponent=max(mu,F(0))*duration
    result=dict(logarithmic_norm_upper_per_s=str(mu),growth_exponent_upper=str(exponent),
        integrated_derivative_forcing_upper_v=list(map(str,forcing)),
        node_direct_forcing_upper_v=list(map(str,node_forcing)),node_from_memory_gain_upper=str(node_gain),
        initial_memory_error_known=False,time_varying_operator_bound=False,nonlinear_remainder_bound=False)
    if exponent>4096:
        return result|dict(growth_supported=False,unsupported_reason='frozen exponential domain >4096')
    growth=exp_bounds(exponent)[1];forced=growth*max(forcing)
    return result|dict(growth_supported=True,anchor_gain_upper=str(growth),
        zero_anchor_forced_memory_upper_v=str(forced),
        zero_anchor_forced_node_upper_v=str(node_gain*forced+max(node_forcing)))
