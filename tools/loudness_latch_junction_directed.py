"""Rational congruence and directed diagonal uncertainty in the SAME metric."""
from fractions import Fraction as F
import loudness_latch_junction_metric as prior
from loudness_latch_spectral_junction import ldlt
box=prior.box
BISECTIONS=32

def multiply(a,b):return [[sum((a[i][k]*b[k][j] for k in range(len(b))),F(0)) for j in range(len(b[0]))] for i in range(len(a))]
def transpose(a):return [list(row) for row in zip(*a)]

def basis(metric):
    if not metric['accepted']:raise ValueError('accepted fixed metric required')
    p=[[F(v) for v in row] for row in metric['metric']]
    if len(p)!=4 or any(len(row)!=4 for row in p):raise ValueError('complete fixed metric required')
    proof=ldlt(p)
    if not proof['positive_definite'] or proof!=metric['rounded_pd_proof']:raise ValueError('frozen metric factorization differs')
    l=[[F(v) for v in row] for row in proof['lower']];d=list(map(F,proof['pivots']))
    r=[[F(i==j) for j in range(4)] for i in range(4)]
    for i in range(4):
        for j in range(i):r[i][j]=-sum((l[i][k]*r[k][j] for k in range(j,i)),F(0))
    diagonal=[[d[i]*F(i==j) for j in range(4)] for i in range(4)]
    if multiply(multiply(r,p),transpose(r))!=diagonal:raise ValueError('exact congruence identity failed')
    rho=F(metric['time_scale_per_s'])
    if rho<=0:raise ValueError('positive frozen time scale required')
    return dict(lower=prior.pack(l),inverse_lower=prior.pack(r),diagonal=list(map(str,d)),time_scale_per_s=str(rho),
        metric_sha256=box.digest(metric['metric']),metric_changed=False)

def enclosure(prepared,generator):
    l=[[F(v) for v in row] for row in prepared['lower']];r=[[F(v) for v in row] for row in prepared['inverse_lower']];d=list(map(F,prepared['diagonal']));rho=F(prepared['time_scale_per_s'])
    if len(generator)!=4 or any(len(row)!=4 for row in generator):raise ValueError('complete junction generator required')
    b=[[box.div(box.interval(v),(rho,rho)) for v in row] for row in generator]
    t=[[box.ZERO for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(i,4):
            value=box.ZERO
            for k in range(4):
                for q in range(4):
                    # Compile the two appearances of each B[k,q] BEFORE interval evaluation.
                    coefficient=(d[i]*l[k][i]*r[j][q]+d[j]*l[k][j]*r[i][q])/2
                    if coefficient:value=box.add(value,box.mul((coefficient,coefficient),b[k][q]))
            t[i][j]=t[j][i]=value
    center=[[(lo+hi)/2 for lo,hi in row] for row in t]
    radius=[[(hi-lo)/2 for lo,hi in row] for row in t]
    rows=[sum(row,F(0)) for row in radius]
    upper=[[center[i][j]+(rows[i] if i==j else 0) for j in range(4)] for i in range(4)]
    return dict(transformed_symmetric_intervals=box.pack(t),center=prior.pack(center),radius=prior.pack(radius),
        directed_diagonal_radius=list(map(str,rows)),surrogate_upper=prior.pack(upper),
        coefficient_policy='combine each generator coefficient in R*(PB+B^T P)*R^T/2 before interval evaluation')

def rate(metric,generator,previous,prepared=None):
    prepared=basis(metric) if prepared is None else prepared
    if prepared['metric_sha256']!=box.digest(metric['metric']) or F(prepared['time_scale_per_s'])!=F(metric['time_scale_per_s']):raise ValueError('congruence belongs to another metric or time scale')
    if not previous['metric_constant_within_interval'] or not previous['final_upper_ldlt']['positive_definite']:raise ValueError('validated same-metric upper required')
    certificate=enclosure(prepared,generator);d=list(map(F,prepared['diagonal']));u=[[F(v) for v in row] for row in certificate['surrogate_upper']];rho=F(prepared['time_scale_per_s'])
    # D^-1 U is similar to a symmetric matrix; real eigenvalues and exact row Gershgorin seed.
    lo=max(u[i][i]/d[i] for i in range(4))
    hi=max((u[i][i]+sum((abs(u[i][j]) for j in range(4) if j!=i),F(0)))/d[i] for i in range(4))+1
    seed_lo=lo;seed_hi=hi;probes=[]
    def query(alpha):return ldlt([[alpha*d[i]*F(i==j)-u[i][j] for j in range(4)] for i in range(4)])
    def log(alpha,proof):return dict(alpha_normalized=str(alpha),positive_definite=proof['positive_definite'],failed_at=proof['failed_at'],pivot_sha256=box.digest(proof['pivots']))
    proof=query(hi)
    if not proof['positive_definite']:raise ValueError('strict directed seed did not certify')
    probes.append(log(hi,proof))
    for _ in range(BISECTIONS):
        middle=(lo+hi)/2;q=query(middle);probes.append(log(middle,q))
        if q['positive_definite']:hi=middle;proof=q
        else:lo=middle
    raw=hi*rho;old=F(previous['mu_metric_upper_per_s']);final=min(raw,old)
    return certificate|dict(seed_lower_normalized=str(seed_lo),seed_upper_normalized=str(seed_hi),surrogate_lower_normalized=str(lo),
        raw_upper_normalized=str(hi),raw_mu_metric_upper_per_s=str(raw),prior_isotropic_mu_upper_per_s=str(old),
        mu_metric_upper_per_s=str(final),same_metric_intersection=True,selected_upper='directed' if raw<=old else 'prior isotropic',
        strictly_narrower=final<old,final_raw_upper_ldlt=proof,probes=probes,bisections=BISECTIONS,
        lower_is_actual_log_norm_bound=False,internal_time_varying_contraction_certified=final<0,
        complete_coupled_contraction_certified=False,metric_changed=False)

def refine_metrics(metrics,certificate):
    matrix=[row[:] for row in metrics['comparison_per_s']];matrix[5][5]=certificate['mu_metric_upper_per_s']
    return dict(metrics,comparison_per_s=matrix)
