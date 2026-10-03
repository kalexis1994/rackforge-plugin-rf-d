"""Fixed rational quadratic junction metric with interval rate and dual conversions."""
from fractions import Fraction as F
from itertools import product
import loudness_latch_junction_modal as box
from loudness_latch_spectral_junction import ldlt
from loudness_latch_junction_rms import sqrt_bounds
import loudness_latch_block_comparison as blocks

CANDIDATE_BITS=40
BISECTIONS=32

def pack(a):return [[str(v) for v in row] for row in a]
def nearest(v):return F(round(F(v)*(1<<CANDIDATE_BITS)),1<<CANDIDATE_BITS)
def solve(a,b):
    """Exact pivoted elimination; singular candidates are recorded, never regularized."""
    n=len(a)
    if not n or len(b)!=n or any(len(row)!=n for row in a):raise ValueError('complete linear system required')
    a=[[F(v) for v in row]+[F(rhs)] for row,rhs in zip(a,b)]
    for k in range(n):
        pivot=next((i for i in range(k,n) if a[i][k]),None)
        if pivot is None:raise ValueError('singular linear system')
        a[k],a[pivot]=a[pivot],a[k];p=a[k][k]
        a[k]=[v/p for v in a[k]]
        for i in range(n):
            if i==k:continue
            factor=a[i][k]
            if factor:a[i]=[v-factor*w for v,w in zip(a[i],a[k])]
    return [row[-1] for row in a]

def invert(a):
    n=len(a);columns=[solve(a,[F(i==j) for i in range(n)]) for j in range(n)]
    return [[columns[j][i] for j in range(n)] for i in range(n)]

def candidate(generators):
    if not generators:raise ValueError('nonempty complete generator family required')
    family=[[[box.interval(v) for v in row] for row in b] for b in generators]
    if any(len(b)!=4 or any(len(row)!=4 for row in b) for b in family):raise ValueError('four-junction family required')
    hull=[[(min(b[i][j][0] for b in family),max(b[i][j][1] for b in family)) for j in range(4)] for i in range(4)]
    size=max(sum((max(map(abs,v)) for v in row),F(0)) for row in hull);rho=F(1)
    while rho<size:rho*=2
    center=[[nearest((lo+hi)/(2*rho)) for lo,hi in row] for row in hull]
    positions=[(i,j) for i in range(4) for j in range(i,4)];system=[];rhs=[]
    for i,j in positions:
        row=[]
        for r,s in positions:
            basis=[[F((k==r and l==s) or (k==s and l==r)) for l in range(4)] for k in range(4)]
            row.append(sum((center[k][i]*basis[k][j]+basis[i][k]*center[k][j] for k in range(4)),F(0)))
        system.append(row);rhs.append(-F(i==j))
    out=dict(hull_sha256=box.digest(box.pack(hull)),normalized_center=pack(center),time_scale_per_s=str(rho),
        candidate_bits=CANDIDATE_BITS,normalization_policy='trace(P)=4 before fixed nearest-even dyadic rounding',
        numerical_metric_systems=1,circuit_inverse_systems=0)
    try:solution=solve(system,rhs)
    except ValueError:
        return out|dict(accepted=False,rejection='singular Lyapunov candidate system',raw_solution=None,raw_pd_proof=None,metric=None)
    p=[[F(0) for _ in range(4)] for _ in range(4)]
    for (i,j),v in zip(positions,solution):p[i][j]=p[j][i]=v
    proof=ldlt(p);out.update(raw_solution=pack(p),raw_pd_proof=proof)
    if not proof['positive_definite']:return out|dict(accepted=False,rejection='Lyapunov candidate is not positive definite',metric=None)
    trace=sum(p[i][i] for i in range(4));p=[[nearest(4*v/trace) for v in row] for row in p];proof=ldlt(p)
    out.update(rounded_pd_proof=proof,metric=pack(p))
    if not proof['positive_definite']:return out|dict(accepted=False,rejection='rounded candidate is not positive definite')
    pi=invert(p)
    vertices=[sum((F(s[i])*p[i][j]*s[j] for i in range(4) for j in range(4)),F(0)) for s in product((-1,1),repeat=4)]
    vmax=max(vertices);anchor=sqrt_bounds(vmax)[1]/2
    return out|dict(accepted=True,rejection=None,inverse_metric=pack(pi),anchor_vertex_quadratics=list(map(str,vertices)),
        anchor_quadratic_max=str(vmax),anchor_normalization_upper=str(anchor),
        metric_norm='sqrt(z^T P z)/(2*a), z=W_J e_J, fixed a bounds sqrt(max_sign s^T P s)/2',
        common_weighted_infinity_anchor_preserved=True)

def symmetric_metric_part(p,b):
    n=len(p)
    return [[box.mul(box.add(
        sum_intervals(box.mul((p[i][k],p[i][k]),b[k][j]) for k in range(n)),
        sum_intervals(box.mul(b[k][i],(p[k][j],p[k][j])) for k in range(n))),
        (F(1,2),F(1,2))) for j in range(n)] for i in range(n)]

def sum_intervals(values):
    total=box.ZERO
    for value in values:total=box.add(total,value)
    return total

def rate(metric,generator):
    p=[[F(v) for v in row] for row in metric['metric']];pi=[[F(v) for v in row] for row in metric['inverse_metric']]
    rho=F(metric['time_scale_per_s']);b=[[box.div(box.interval(v),(rho,rho)) for v in row] for row in generator]
    s=symmetric_metric_part(p,b);c=[[(lo+hi)/2 for lo,hi in row] for row in s]
    delta=max(sum(((hi-lo)/2 for lo,hi in row),F(0)) for row in s)
    # All S lie below C+delta I in Loewner order. Generalized max eigenvalue is bounded by exact PD queries.
    size=max(sum((abs(v) for v in row),F(0)) for row in c)+delta
    pinorm=max(sum((abs(v) for v in row),F(0)) for row in pi)
    hi=size*pinorm+1;lo=-hi;seed=hi;probes=[]
    def query(alpha):return ldlt([[alpha*p[i][j]-c[i][j]-(delta if i==j else 0) for j in range(4)] for i in range(4)])
    def log(alpha,proof):return dict(alpha_normalized=str(alpha),positive_definite=proof['positive_definite'],failed_at=proof['failed_at'],pivot_sha256=box.digest(proof['pivots']))
    proof=query(hi)
    if not proof['positive_definite']:raise ValueError('strict generalized seed did not certify')
    probes.append(log(hi,proof))
    for _ in range(BISECTIONS):
        middle=(lo+hi)/2;q=query(middle);probes.append(log(middle,q))
        if q['positive_definite']:hi=middle;proof=q
        else:lo=middle
    return dict(symmetric_metric_intervals=box.pack(s),radius_norm_upper=str(delta),seed_upper_normalized=str(seed),
        surrogate_lower_normalized=str(lo),upper_normalized=str(hi),mu_metric_upper_per_s=str(hi*rho),
        final_upper_ldlt=proof,probes=probes,bisections=BISECTIONS,
        lower_is_actual_log_norm_bound=False,metric_constant_within_interval=True,
        internal_time_varying_contraction_certified=hi<0,complete_coupled_contraction_certified=False)

def square(v):
    lo,hi=v;return (F(0) if lo<=0<=hi else min(lo*lo,hi*hi),max(lo*lo,hi*hi))

def quadratic_upper(matrix,vector):
    v=list(map(box.interval,vector));n=len(matrix)
    if not n or len(v)!=n or any(len(row)!=n for row in matrix):raise ValueError('complete quadratic form required')
    if any(matrix[i][j]!=matrix[j][i] for i in range(n) for j in range(n)):raise ValueError('symmetric quadratic form required')
    total=box.ZERO
    for i in range(n):
        total=box.add(total,box.mul((matrix[i][i],matrix[i][i]),square(v[i])))
        for j in range(i+1,n):total=box.add(total,box.mul((2*matrix[i][j],2*matrix[i][j]),box.mul(v[i],v[j])))
    if total[1]<0:raise ValueError('negative quadratic upper: invalid metric')
    return sqrt_bounds(total[1])[1]

def metrics(inverse,weights,forcing,old,metric,certificate):
    n=len(inverse);nv=94;w=list(map(F,weights));junction=blocks.BLOCKS[5]
    if n!=119 or len(w)!=25 or any(v<=0 for v in w):raise ValueError('fixed positive circuit coordinates required')
    inverse=[[box.interval(v) for v in row] for row in inverse]
    if any(len(row)!=n for row in inverse):raise ValueError('complete inverse square required')
    p=[[F(v) for v in row] for row in metric['metric']];pi=[[F(v) for v in row] for row in metric['inverse_metric']]
    normal=2*F(metric['anchor_normalization_upper'])
    matrix=[[F(v) for v in row] for row in old['comparison_per_s']];matrix[5][5]=F(certificate['mu_metric_upper_per_s'])
    def scale(v,f):return box.mul(v,(f,f))
    for a,group in enumerate(blocks.BLOCKS[:5]):
        matrix[a][5]=normal*max(quadratic_upper(pi,[scale(inverse[nv+i][nv+j],w[i]/w[j]) for j in junction]) for i in group)
        matrix[5][a]=sum((quadratic_upper(p,[scale(inverse[nv+i][nv+j],w[i]/w[j]) for i in junction]) for j in group),F(0))/normal
    values=list(map(F,forcing['nodal_l1_c']+forcing['constraint_l1_v_s']))
    if len(values)!=n or min(values)<0:raise ValueError('complete nonnegative forcing required')
    budget=list(map(F,old['block_forcing_l1_v']))
    budget[5]=sum((quadratic_upper(p,[scale(inverse[nv+i][j],w[i]) for i in junction])*v for j,v in enumerate(values)),F(0))/normal
    gains=[[F(v) for v in row] for row in old['nodal_block_gains']]
    for i in range(nv):gains[i][5]=normal*quadratic_upper(pi,[scale(inverse[i][nv+j],1/w[j]) for j in junction])
    return dict(comparison_per_s=blocks.pack(matrix),block_forcing_l1_v=list(map(str,budget)),
        nodal_block_gains=blocks.pack(gains),nodal_direct_v=old['nodal_direct_v'],
        initial_common_weighted_infinity_anchor_conversion='fixed normalization a makes junction anchor <=1',
        norm_policy=metric['metric_norm'])

def propagate(cells):return blocks.propagate(cells)
