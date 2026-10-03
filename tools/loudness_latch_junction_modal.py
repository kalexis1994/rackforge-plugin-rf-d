"""Exact signed inverse slice and interval quartic Routh certificate, offline only."""
from fractions import Fraction as F
from itertools import combinations, permutations
from hashlib import sha256
from loudness_latch_bdf_doubling_survey import canonical

ZERO=(F(0),F(0))
ONE=(F(1),F(1))

def interval(value):
    if len(value)!=2:raise ValueError('two interval endpoints required')
    lo,hi=map(F,value)
    if lo>hi:raise ValueError('ordered interval required')
    return lo,hi

def add(a,b):return a[0]+b[0],a[1]+b[1]
def neg(a):return -a[1],-a[0]
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    values=[x*y for x in a for y in b];return min(values),max(values)
def div(a,b):
    if b[0]<=0<=b[1]:raise ValueError('denominator contains zero')
    return mul(a,(1/b[1],1/b[0]))
def sign(a):return 1 if a[0]>0 else -1 if a[1]<0 else 0
def pack(a):return [[[str(lo),str(hi)] for lo,hi in row] for row in a]
def digest(value):return sha256(canonical(value)).hexdigest()

def inverse_slice(inverse,scales,cover,parent_q,indices):
    """The archived first-order Neumann formula, evaluated only at selected entries.

    Every dot product remains exact rational; no truncated defect rows/columns.
    This is an enclosure reconstruction, not a new inverse or circuit solve.
    """
    x=[[F(v) for v in row] for row in inverse];n=len(x);d=list(map(F,scales));idx=tuple(indices)
    if not n or any(len(r)!=n for r in x) or len(d)!=n or any(v<=0 for v in d):raise ValueError('complete square and positive scales required')
    if not idx or len(set(idx))!=len(idx) or any(not isinstance(i,int) or not 0<=i<n for i in idx):raise ValueError('distinct valid slice indices required')
    e=[[interval(v) for v in row] for row in cover['preconditioned_defect_intervals']]
    if len(e)!=n or any(len(r)!=n for r in e):raise ValueError('complete defect square required')
    rows=[sum((max(map(abs,v)) for v in row),F(0)) for row in e];q=max(rows);parent_q=F(parent_q)
    if q!=F(cover['contraction_upper']) or not 0<=q<=parent_q<1:raise ValueError('consistent contracted parent required')
    out=[]
    for i in idx:
        row=[]
        for j in idx:
            column=[d[k]*x[k][j] for k in range(n)];peak=max(map(abs,column))
            correction=ZERO
            for k,v in enumerate(column):correction=add(correction,mul(e[i][k],(v,v)))
            tail=rows[i]*q/(1-q)*peak
            lo=(d[i]*x[i][j]+correction[0]-tail)/d[i];hi=(d[i]*x[i][j]+correction[1]+tail)/d[i]
            row_error=rows[i]/(1-q)*peak/d[i];parent_error=parent_q/(1-parent_q)*peak/d[i]
            a=max(lo,x[i][j]-row_error,x[i][j]-parent_error);b=min(hi,x[i][j]+row_error,x[i][j]+parent_error)
            if a>b:raise ValueError('empty slice intersection')
            row.append((a,b))
        out.append(row)
    return out

def generator(inverse,weights):
    n=len(inverse);w=list(map(F,weights))
    if n!=4 or any(len(row)!=n for row in inverse) or len(w)!=n or any(v<=0 for v in w):raise ValueError('four junctions and positive weights required')
    return [[mul(neg(interval(v)),(w[i]/w[j],w[i]/w[j])) for j,v in enumerate(row)] for i,row in enumerate(inverse)]

def determinant(a):
    n=len(a)
    if not n or any(len(row)!=n for row in a):raise ValueError('nonempty square required')
    result=ZERO
    for p in permutations(range(n)):
        term=ONE
        for i,j in enumerate(p):term=mul(term,a[i][j])
        inversions=sum(p[i]>p[j] for i in range(n) for j in range(i+1,n))
        result=add(result,neg(term) if inversions%2 else term)
    return result

def characteristic(a):
    """Coefficients of det(z I-A), descending, via all principal minors."""
    n=len(a)
    if n!=4 or any(len(row)!=4 for row in a):raise ValueError('quartic matrix required')
    a=[[interval(v) for v in row] for row in a];coefficients=[ONE]
    for k in range(1,5):
        value=ZERO
        for idx in combinations(range(n),k):value=add(value,determinant([[a[i][j] for j in idx] for i in idx]))
        coefficients.append(neg(value) if k%2 else value)
    return coefficients

def routh(coefficients):
    if len(coefficients)!=5:raise ValueError('monic quartic required')
    c=list(map(interval,coefficients))
    if c[0]!=ONE:raise ValueError('monic quartic required')
    _,a1,a2,a3,a4=c;d2=sub(mul(a1,a2),a3);d3=sub(mul(d2,a3),mul(mul(a1,a1),a4))
    column=[ONE,a1];blocked=None
    if not sign(a1):blocked='a1 contains zero'
    elif not sign(d2):blocked='delta2 contains zero'
    else:column.extend((div(d2,a1),div(d3,d2),a4))
    signs=[sign(v) for v in column]
    if blocked is None and not all(signs):blocked='Routh first column contains zero'
    changes=None if blocked else sum(a!=b for a,b in zip(signs,signs[1:]))
    return dict(hurwitz_delta2=[str(v) for v in d2],hurwitz_delta3=[str(v) for v in d3],
        first_column=[[str(v) for v in t] for t in column],strict_signs=signs,blocked=blocked,
        right_half_plane_roots=changes,imaginary_axis_excluded=changes is not None,
        all_frozen_matrices_hurwitz=changes==0,
        all_frozen_matrices_have_rhp_root=changes is not None and changes>0,
        positive_real_root_certified=a4[1]<0)

def analyze(b):
    b=[[interval(v) for v in row] for row in b]
    if len(b)!=4 or any(len(row)!=4 for row in b):raise ValueError('four junction generator required')
    size=max(sum((max(map(abs,v)) for v in row),F(0)) for row in b)
    scale=F(1)
    while scale<size:scale*=2
    normalized=[[div(v,(scale,scale)) for v in row] for row in b];c=characteristic(normalized)
    return dict(generator_intervals_per_s=pack(b),generator_sha256=digest(pack(b)),
        positive_time_scale_per_s=str(scale),normalized_coefficients=[[str(v) for v in t] for t in c],
        coefficient_policy='signed sums of all principal minors; exact rational interval endpoints',
        routh_certificate=routh(c),center_only_bound=False,time_varying_stability_certified=False,
        complete_25_memory_modal_certificate=False,actual_dae_error_bound=False)
