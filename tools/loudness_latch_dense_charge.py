"""Exact polynomial reconstruction and Bernstein certificates, offline only."""
from fractions import Fraction as F
from math import comb


def add(a,b):
    return tuple((a[i] if i<len(a) else F(0))+(b[i] if i<len(b) else F(0))
                 for i in range(max(len(a),len(b))))


def scale(a,value):return tuple(v*value for v in a)


def multiply(a,b):
    out=[F(0)]*(len(a)+len(b)-1)
    for i,v in enumerate(a):
        for j,w in enumerate(b):out[i+j]+=v*w
    return tuple(out)


def evaluate(a,u):
    out=F(0)
    for v in reversed(a):out=out*u+v
    return out


def differentiate(a):return tuple(i*v for i,v in enumerate(a) if i) or (F(0),)


def cardinal_basis(times):
    tt=tuple(map(F,times))
    if len(tt)<2 or len(set(tt))!=len(tt):raise ValueError('distinct interpolation nodes required')
    out=[]
    for i,t in enumerate(tt):
        poly=(F(1),);den=F(1)
        for j,s in enumerate(tt):
            if i!=j:poly=multiply(poly,(-s,F(1)));den*=t-s
        out.append(scale(poly,1/den))
    return tuple(out)


def interpolate(basis,vectors):
    if len(basis)!=len(vectors) or not vectors or any(len(v)!=len(vectors[0]) for v in vectors):
        raise ValueError('complete interpolation vectors required')
    return tuple(tuple(sum((p[j]*F(v[k]) for p,v in zip(basis,vectors)),F(0))
                       for j in range(len(basis))) for k in range(len(vectors[0])))


def reparameterize(a,left,right):
    if left>=right:raise ValueError('positive certificate interval required')
    out=(F(0),);power=(F(1),)
    for v in a:
        out=add(out,scale(power,v));power=multiply(power,(F(left),F(right-left)))
    return out


def bernstein(a,left=F(0),right=F(1)):
    power=reparameterize(a,left,right);n=len(power)-1
    return tuple(sum((power[k]*F(comb(i,k),comb(n,k)) for k in range(i+1)),F(0)) for i in range(n+1))


def bisect_bernstein(b):
    rows=[tuple(b)]
    while len(rows[-1])>1:rows.append(tuple((a+c)/2 for a,c in zip(rows[-1],rows[-1][1:])))
    return tuple(row[0] for row in rows),tuple(row[-1] for row in reversed(rows))


def isolate_zero(a,left=F(0),right=F(1),depth=40):
    """Pruned cover of all zeros; unresolved leaves are not claimed as roots."""
    if type(depth) is not int or not 0<=depth<=40:raise ValueError('depth 0..40 required')
    b=bernstein(a,left,right);points=set();leaves=[];excluded=0
    if not any(b):return dict(coincident=True,exact_points=(),brackets=(),excluded_leaves=0)
    def visit(bb,l,r,d):
        nonlocal excluded
        if bb[0]==0:points.add(l)
        if bb[-1]==0:points.add(r)
        if min(bb)>=0 or max(bb)<=0:excluded+=1;return
        if d==depth:
            leaves.append(dict(left=l,right=r,bernstein=bb,opposite_endpoint_signs=bb[0]*bb[-1]<0));return
        first,second=bisect_bernstein(bb);mid=(l+r)/2
        visit(first,l,mid,d+1);visit(second,mid,r,d+1)
    visit(b,left,right,0)
    return dict(coincident=False,exact_points=tuple(sorted(points)),brackets=tuple(leaves),excluded_leaves=excluded)
