"""Directed block comparison and outward positive semigroup bounds, offline only."""
from fractions import Fraction as F
from math import factorial
from hashlib import sha256
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_charge_enclosure import up,exp_bounds
from loudness_latch_cell_propagation import interval_dyadic_product

BLOCKS=(tuple(range(17)),(17,),(18,),(19,),(20,),tuple(range(21,25)))
NAMES=('audio','C10','C2','C4','C7','junctions')
TERMS=32
MAX_SCALED_NORM=4096

def pack(a):return [[str(v) for v in row] for row in a]
def digest(a):return sha256(canonical(pack(a))).hexdigest()
def identity(n):return [[F(i==j) for j in range(n)] for i in range(n)]
def multiply(a,b):
    # Inputs are nonnegative dyadics; exact integer products, then round outward.
    if any(v<0 for row in a+b for v in row):raise ValueError('positive product required')
    out=interval_dyadic_product([[(v,v) for v in row] for row in a],b)
    return [[up(v[1]) for v in row] for row in out]
def apply(a,v):return [up(sum((x*y for x,y in zip(row,v)),F(0))) for row in a]

def positive_exponential(a):
    """Upper exp(A), nonnegative dyadic A, ||A||inf<=1; fixed 32 terms."""
    n=len(a);rho=max(sum(row,F(0)) for row in a)
    if rho>1 or any(v<0 for row in a for v in row):raise ValueError('unit positive exponential domain required')
    total=identity(n);term=identity(n)
    for k in range(1,TERMS+1):
        term=[[up(v/k) for v in row] for row in multiply(term,a)]
        total=[[up(total[i][j]+term[i][j]) for j in range(n)] for i in range(n)]
    tail=up(rho**(TERMS+1)/factorial(TERMS+1)/(1-rho/F(TERMS+2)))
    # A structural zero outside transitive support stays exactly zero.
    reach=[[i==j or a[i][j]>0 for j in range(n)] for i in range(n)]
    for k in range(n):
        for i in range(n):
            for j in range(n):reach[i][j]=reach[i][j] or (reach[i][k] and reach[k][j])
    return [[up(total[i][j]+(tail if reach[i][j] else 0)) for j in range(n)] for i in range(n)],tail

def kernels(matrix,duration):
    """Endpoint exp(Mh), and entrywise sup exp(Mt), 0<=t<=h, for Metzler M."""
    m=[[F(v) for v in row] for row in matrix];n=len(m);h=F(duration)
    if not n or any(len(row)!=n for row in m) or h<=0:raise ValueError('positive complete square kernel required')
    if any(m[i][j]<0 for i in range(n) for j in range(n) if i!=j):raise ValueError('Metzler off-diagonal required')
    shift=max(F(0),max(-m[i][i] for i in range(n)))
    c=[[m[i][j]+(shift if i==j else 0) for j in range(n)] for i in range(n)]
    norm=max(max(sum(row,F(0)) for row in c)*h,shift*h)
    if norm>MAX_SCALED_NORM:raise ValueError('declared scaled norm >4096')
    scale=0
    while norm/F(2)**scale>F(1,2):scale+=1
    step=h/F(2)**scale
    small=[[up(v*step) for v in row] for row in c]
    positive=[[up(max(v,F(0))*step) for v in row] for row in m]
    end,tail=positive_exponential(small);peak,peak_tail=positive_exponential(positive)
    damping=exp_bounds(-shift*step)[1]
    end=[[up(v*damping) for v in row] for row in end]
    for _ in range(scale):
        later=multiply(peak,end)
        peak=[[max(a,b) for a,b in zip(row,late)] for row,late in zip(peak,later)]
        end=multiply(end,end)
    return end,peak,dict(shift_per_s=str(shift),scalings=scale,small_duration_s=str(step),
        small_shifted_norm_upper=str(max(sum(row,F(0)) for row in small)),terms=TERMS,
        small_endpoint_tail_upper=str(tail),small_peak_tail_upper=str(peak_tail),
        endpoint_sha256=digest(end),peak_sha256=digest(peak))

def block_metrics(inverse,nv,weights,forcing,blocks=BLOCKS):
    n=len(inverse);nm=n-nv;w=list(map(F,weights));groups=[tuple(b) for b in blocks]
    if nv<=0 or len(w)!=nm or any(v<=0 for v in w) or not groups or any(not b for b in groups):raise ValueError('positive complete block coordinates required')
    if sorted(j for b in groups for j in b)!=list(range(nm)):raise ValueError('disjoint complete memory partition required')
    if any(len(row)!=n for row in inverse) or any(F(lo)>F(hi) for row in inverse for lo,hi in row):raise ValueError('ordered square inverse required')
    absolute=[[max(abs(F(lo)),abs(F(hi))) for lo,hi in row] for row in inverse]
    values=list(map(F,forcing['nodal_l1_c']+forcing['constraint_l1_v_s']))
    point=list(map(F,forcing['nodal_point_a']+forcing['constraint_point_v']))
    if len(values)!=n or len(point)!=n or min(values+point)<0:raise ValueError('complete nonnegative forcing required')
    matrix=[];budget=[]
    for a,block in enumerate(groups):
        row=[]
        for b,other in enumerate(groups):
            row.append(max((-F(inverse[nv+i][nv+i][0]) if a==b else F(0))+
                sum((w[i]/w[j]*absolute[nv+i][nv+j] for j in other if a!=b or j!=i),F(0)) for i in block))
        matrix.append(row)
        budget.append(sum((max(w[i]*absolute[nv+i][j] for i in block)*v for j,v in enumerate(values)),F(0)))
    gains=[[sum((absolute[i][nv+j]/w[j] for j in block),F(0)) for block in groups] for i in range(nv)]
    direct=[sum((absolute[i][j]*v for j,v in enumerate(point)),F(0)) for i in range(nv)]
    return dict(comparison_per_s=pack(matrix),block_forcing_l1_v=list(map(str,budget)),
        nodal_block_gains=pack(gains),nodal_direct_v=list(map(str,direct)))

def propagate(cells):
    if not cells:raise ValueError('nonempty block propagation required')
    n=len(cells[0]['metrics']['comparison_per_s']);anchor=[F(1)]*n;forced=[F(0)]*n
    node_anchor=node_forced=F(0);last=F(0);trace=[]
    for cell in cells:
        f=cell['forcing_inputs'];m=cell['metrics'];left=F(f['left']);right=F(f['right'])
        if left!=last or right<=left:raise ValueError('contiguous positive partition required')
        e,p,cert=kernels(m['comparison_per_s'],f['duration_s'])
        b=list(map(F,m['block_forcing_l1_v']));g=[[F(v) for v in row] for row in m['nodal_block_gains']];d=list(map(F,m['nodal_direct_v']))
        if len(e)!=n or len(b)!=n or len(g)!=len(d) or any(len(row)!=n for row in g) or min(b+d+[v for row in g for v in row])<0:raise ValueError('complete nonnegative block budgets required')
        pa=apply(p,anchor);pf=apply(p,[a+v for a,v in zip(forced,b)])
        na=max(sum((v*a for v,a in zip(row,pa)),F(0)) for row in g)
        nf=max(sum((v*a for v,a in zip(row,pf)),F(0))+di for row,di in zip(g,d))
        node_anchor=max(node_anchor,na);node_forced=max(node_forced,nf)
        anchor=apply(e,anchor);fb=apply(p,b);forced=[up(a+v) for a,v in zip(apply(e,forced),fb)]
        trace.append(dict(left=str(left),right=str(right),kernel_certificate=cert,
            endpoint_kernel=pack(e),peak_kernel=pack(p),endpoint_anchor=list(map(str,anchor)),
            endpoint_forced_v=list(map(str,forced)),peak_anchor=list(map(str,pa)),peak_forced_v=list(map(str,pf)),
            peak_node_anchor=str(na),peak_node_forced_v=str(nf)))
        last=right
    if last!=1:raise ValueError('complete normalized interval required')
    return dict(trace=trace,endpoint_block_anchor=list(map(str,anchor)),endpoint_block_forced_v=list(map(str,forced)),
        peak_node_anchor_gain_upper=str(node_anchor),peak_zero_anchor_node_upper_v=str(node_forced),
        initial_error_known=False,nonlinear_remainder_bound=False,actual_dae_error_bound=False)
