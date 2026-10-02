"""Correct integrated infinity-norm forcing by maxima of operator columns."""
from fractions import Fraction as F
from loudness_latch_continuous_descriptor import frozen_budget as prior_budget


def forcing_norm_budget(absolute,nv,r_l1,d_l1):
    n=len(absolute);nm=n-nv
    if not 0<nv<n or len(r_l1)!=nv or len(d_l1)!=nm:raise ValueError('complete forcing dimensions required')
    if any(F(v)<0 for row in absolute for v in row) or any(F(v)<0 for v in (*r_l1,*d_l1)):
        raise ValueError('nonnegative magnitude and budgets required')
    columns=[max(F(absolute[nv+i][j]) for i in range(nm)) for j in range(n)]
    return sum((a*F(b) for a,b in zip(columns,(*r_l1,*d_l1))),F(0))


def frozen_budget(x,errors,nv,r_l1,d_l1,r_point,d_point,duration):
    old=prior_budget(x,errors,nv,r_l1,d_l1,r_point,d_point,duration)
    absolute=[[abs(F(v))+e for v,e in zip(row,err)] for row,err in zip(x,errors)]
    norm=forcing_norm_budget(absolute,nv,r_l1,d_l1)
    row_max=max(map(F,old['integrated_derivative_forcing_upper_v']))
    result=old|dict(integrated_forcing_norm_upper_v=str(norm),previous_row_integral_max_v=str(row_max),
        row_integral_max_is_norm_integral_bound=False,prior_uniform_budget_admitted=False)
    if norm<row_max:raise ValueError('norm budget below a row integral')
    if old['growth_supported']:
        forced=F(old['anchor_gain_upper'])*norm
        result.update(zero_anchor_forced_memory_upper_v=str(forced),zero_anchor_forced_node_upper_v=str(
            F(old['node_from_memory_gain_upper'])*forced+max(map(F,old['node_direct_forcing_upper_v']))))
    return result
