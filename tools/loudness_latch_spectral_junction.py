"""Exact LDL transpose spectral bracket plus symmetric interval perturbation."""
from fractions import Fraction as F
from hashlib import sha256
from loudness_latch_bdf_doubling_survey import canonical

BISECTIONS=32
STRICT_SEED_GAP=F(1) # per second; numerical proof margin, not a circuit constant.

def pack(a):return [[str(v) for v in row] for row in a]
def digest(v):return sha256(canonical(v)).hexdigest()

def symmetric_matrix(matrix):
    a=[[F(v) for v in row] for row in matrix];n=len(a)
    if not n or any(len(row)!=n for row in a):raise ValueError('complete symmetric square required')
    if any(a[i][j]!=a[j][i] for i in range(n) for j in range(n)):raise ValueError('symmetric matrix required')
    return a

def ldlt(matrix):
    """Exact unpivoted PD test. A nonpositive pivot rejects strict positivity."""
    a=symmetric_matrix(matrix);n=len(a);l=[[F(i==j) for j in range(n)] for i in range(n)];d=[]
    for k in range(n):
        pivot=a[k][k]-sum((l[k][j]**2*d[j] for j in range(k)),F(0));d.append(pivot)
        if pivot<=0:return dict(positive_definite=False,failed_at=k,pivots=list(map(str,d)),lower=pack(l))
        for i in range(k+1,n):
            l[i][k]=(a[i][k]-sum((l[i][j]*l[k][j]*d[j] for j in range(k)),F(0)))/pivot
    return dict(positive_definite=True,failed_at=None,pivots=list(map(str,d)),lower=pack(l))

def shifted(center,value):return [[F(value)*(i==j)-v for j,v in enumerate(row)] for i,row in enumerate(center)]

def spectral_bound(intervals):
    n=len(intervals)
    if not n or any(len(row)!=n for row in intervals):raise ValueError('complete symmetric interval square required')
    box=[[tuple(map(F,v)) for v in row] for row in intervals]
    if any(len(v)!=2 or v[0]>v[1] for row in box for v in row):raise ValueError('ordered interval required')
    if any(box[i][j]!=box[j][i] for i in range(n) for j in range(n)):raise ValueError('symmetric interval matrix required')
    center=[[(lo+hi)/2 for lo,hi in row] for row in box]
    radius=[[(hi-lo)/2 for lo,hi in row] for row in box]
    delta=max(sum(row,F(0)) for row in radius)
    gersh=max(box[i][i][1]+sum((max(map(abs,box[i][j])) for j in range(n) if j!=i),F(0)) for i in range(n))
    lo=max(center[i][i] for i in range(n))
    hi=max(center[i][i]+sum((abs(center[i][j]) for j in range(n) if j!=i),F(0)) for i in range(n))+STRICT_SEED_GAP
    seed_hi=hi;seed_lo=lo;proof=ldlt(shifted(center,hi))
    if not proof['positive_definite']:raise ValueError('strict Gershgorin seed did not certify')
    probes=[]
    def log(value,p):
        return dict(shift_per_s=str(value),positive_definite=p['positive_definite'],failed_at=p['failed_at'],pivot_sha256=digest(p['pivots']))
    probes.append(log(hi,proof))
    for _ in range(BISECTIONS):
        middle=(lo+hi)/2;query=ldlt(shifted(center,middle));probes.append(log(middle,query))
        if query['positive_definite']:hi=middle;proof=query
        else:lo=middle
    lower=lo-delta;raw_upper=hi+delta;upper=min(raw_upper,gersh)
    if lower>upper:raise ValueError('inconsistent same-norm spectral enclosure')
    return dict(interval_sha256=digest([[[str(a),str(b)] for a,b in row] for row in box]),
        center=pack(center),radius_norm_upper_per_s=str(delta),seed_lower_per_s=str(seed_lo),seed_upper_per_s=str(seed_hi),
        bisections=BISECTIONS,probes=probes,center_lambda_lower_per_s=str(lo),center_lambda_upper_per_s=str(hi),
        final_center_upper_ldlt=proof,raw_lambda_upper_per_s=str(raw_upper),lambda_lower_per_s=str(lower),
        prior_same_norm_gershgorin_upper_per_s=str(gersh),lambda_upper_per_s=str(upper),
        same_norm_gershgorin_intersection=True,strictly_narrower=upper<gersh,
        center_only_bound=False,actual_dae_error_bound=False)

def refine_metrics(metrics):
    certificate=spectral_bound(metrics['junction_symmetric_intervals'])
    if certificate['prior_same_norm_gershgorin_upper_per_s']!=metrics['junction_mu2_gershgorin_upper_per_s']:
        raise ValueError('prior RMS Gershgorin identity differs')
    matrix=[row[:] for row in metrics['comparison_per_s']];matrix[5][5]=certificate['lambda_upper_per_s']
    return dict(metrics,comparison_per_s=matrix,junction_mu2_spectral_upper_per_s=certificate['lambda_upper_per_s']),certificate
