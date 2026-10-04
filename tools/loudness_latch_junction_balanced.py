"""Fixed positive proof weights balance the SAME-metric uncertainty majorant."""
from fractions import Fraction as F
import loudness_latch_junction_directed as prior
from loudness_latch_spectral_junction import ldlt
box=prior.box
BISECTIONS=32
BALANCE_BITS=40

def ceil_dyadic(value):
    value=F(value);unit=1<<BALANCE_BITS
    return F((value.numerator*unit+value.denominator-1)//value.denominator,unit)

def balance(prepared):
    d=list(map(F,prepared['diagonal']))
    if len(d)!=4 or any(v<=0 for v in d):raise ValueError('positive four-entry diagonal required')
    brackets=[prior.prior.sqrt_bounds(1/v) for v in d];weights=[ceil_dyadic(hi) for lo,hi in brackets]
    if any(v<=0 for v in weights):raise ValueError('strictly positive balance weights required')
    return dict(basis_sha256=box.digest(prepared),diagonal=list(map(str,d)),
        reciprocal_sqrt_brackets=[[str(lo),str(hi)] for lo,hi in brackets],
        weights=list(map(str,weights)),balance_bits=BALANCE_BITS,
        weight_policy='ceil_40(sqrt_upper_256(1/D_i)), one fixed vector per interval',
        metric_changed=False,norm_changed=False,anchor_changed=False)

def majorant(center,radius,weights):
    c=[[F(v) for v in row] for row in center];q=[[F(v) for v in row] for row in radius];g=list(map(F,weights));n=len(c)
    if not n or len(q)!=n or len(g)!=n or any(len(row)!=n for row in c+q):raise ValueError('complete square and balance vector required')
    if any(v<=0 for v in g):raise ValueError('positive balance weights required')
    if any(v<0 for row in q for v in row):raise ValueError('nonnegative radii required')
    if any(c[i][j]!=c[j][i] or q[i][j]!=q[j][i] for i in range(n) for j in range(n)):raise ValueError('symmetric center and radii required')
    rows=[sum((q[i][j]*g[j]/g[i] for j in range(n)),F(0)) for i in range(n)]
    upper=[[c[i][j]+(rows[i] if i==j else 0) for j in range(n)] for i in range(n)]
    return rows,upper

def rate(prepared,previous,balanced=None):
    balanced=balance(prepared) if balanced is None else balanced
    if balanced['basis_sha256']!=box.digest(prepared) or balanced['diagonal']!=prepared['diagonal']:raise ValueError('balance belongs to another basis')
    if previous['metric_changed'] or not previous['same_metric_intersection'] or not previous['final_raw_upper_ldlt']['positive_definite']:raise ValueError('validated unchanged-metric directed source required')
    d=list(map(F,prepared['diagonal']));rho=F(prepared['time_scale_per_s'])
    if rho<=0:raise ValueError('positive frozen time scale required')
    rows,u=majorant(previous['center'],previous['radius'],balanced['weights'])
    lo=max(u[i][i]/d[i] for i in range(4))
    hi=max((u[i][i]+sum((abs(u[i][j]) for j in range(4) if j!=i),F(0)))/d[i] for i in range(4))+1
    seed_lo=lo;seed_hi=hi;probes=[]
    def query(alpha):return ldlt([[alpha*d[i]*F(i==j)-u[i][j] for j in range(4)] for i in range(4)])
    def log(alpha,proof):return dict(alpha_normalized=str(alpha),positive_definite=proof['positive_definite'],failed_at=proof['failed_at'],pivot_sha256=box.digest(proof['pivots']))
    proof=query(hi)
    if not proof['positive_definite']:raise ValueError('strict balanced seed did not certify')
    probes.append(log(hi,proof))
    for _ in range(BISECTIONS):
        middle=(lo+hi)/2;q=query(middle);probes.append(log(middle,q))
        if q['positive_definite']:hi=middle;proof=q
        else:lo=middle
    raw=hi*rho;old=F(previous['mu_metric_upper_per_s']);final=min(raw,old)
    return dict(center_radius_sha256=box.digest(dict(center=previous['center'],radius=previous['radius'])),
        balance_sha256=box.digest(balanced),weighted_diagonal_radius=list(map(str,rows)),
        prior_directed_diagonal_radius=previous['directed_diagonal_radius'],surrogate_upper=prior.prior.pack(u),
        seed_lower_normalized=str(seed_lo),seed_upper_normalized=str(seed_hi),surrogate_lower_normalized=str(lo),
        raw_upper_normalized=str(hi),raw_mu_metric_upper_per_s=str(raw),prior_directed_mu_upper_per_s=str(old),
        mu_metric_upper_per_s=str(final),same_metric_intersection=True,selected_upper='balanced' if raw<=old else 'prior directed',
        strictly_narrower=final<old,final_raw_upper_ldlt=proof,probes=probes,bisections=BISECTIONS,
        lower_is_actual_log_norm_bound=False,internal_time_varying_contraction_certified=final<0,
        complete_coupled_contraction_certified=False,metric_changed=False,norm_changed=False,anchor_changed=False)

def refine_metrics(metrics,certificate):return prior.refine_metrics(metrics,certificate)
