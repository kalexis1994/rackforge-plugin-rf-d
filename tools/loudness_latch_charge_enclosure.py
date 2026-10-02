"""Exact rational Taylor integration with outward dyadic exponential bounds."""
from fractions import Fraction as F
from math import factorial
import loudness_latch_dense_charge as poly
import loudness_latch_charge_balance as balance
BITS=256
DEGREE=12
EXP_TERMS=64
UNIT=1<<BITS


def down(x):
    x=F(x);return F(x.numerator*UNIT//x.denominator,UNIT)


def up(x):return -down(-F(x))


def exp_bounds(x):
    """Positive Taylor, geometric tail, reciprocal and interval squaring."""
    x=F(x)
    if abs(x)>4096:raise ValueError('declared exponential range exceeded')
    if x<0:
        a,b=exp_bounds(-x);return down(1/b),up(1/a)
    scale=0;y=x
    while y>1:y/=2;scale+=1
    lo=hi=term_lo=term_hi=F(1)
    for k in range(1,EXP_TERMS+1):
        term_lo=down(term_lo*y/k);term_hi=up(term_hi*y/k)
        lo+=term_lo;hi+=term_hi
    # Next term bounds first omitted term; remaining ratios <=1/(N+2)<1/2.
    hi+=2*up(term_hi*y/(EXP_TERMS+1))
    lo=down(lo);hi=up(hi)
    for _ in range(scale):lo=down(lo*lo);hi=up(hi*hi)
    return lo,hi


def exponential_integral(p,left=F(0),right=F(1)):
    """Enclose ideal integral exp(cubic) du; no Decimal operations."""
    if left>=right:raise ValueError('positive interval required')
    z=poly.reparameterize(p,left,right);center=poly.evaluate(z,F(1,2))
    delta=poly.add(z,(-center,));bern=poly.bernstein(delta)
    rho=max(map(abs,bern));power=(F(1),);t=F(0)
    for k in range(DEGREE+1):
        t+=balance.integral(power,F(0),F(1))/factorial(k)
        if k<DEGREE:power=poly.multiply(power,delta)
    ec=exp_bounds(center);er=exp_bounds(center+rho)[1]*rho**(DEGREE+1)/factorial(DEGREE+1)
    endpoints=[t*v for v in ec];width=right-left
    return (down(width*(min(endpoints)-er)),up(width*(max(endpoints)+er))),dict(
        center=center,rho_upper=rho,taylor_remainder_upper=er,degree=DEGREE)


def static_integral(g,x,h,left=F(0),right=F(1)):
    """Lift all binary coefficients exactly, stamp ideal conditional laws."""
    nodes=[[F(0),F(0)] for _ in x];terms=[]
    def voltage(node):return x[node] if isinstance(node,int) else (F(g['fixed'][node]),)
    def diff(a,b):return poly.add(voltage(a),poly.scale(voltage(b),-1))
    def stamp(node,interval,coefficient):
        if not isinstance(node,int):return
        v=[coefficient*a for a in interval];nodes[node][0]+=min(v);nodes[node][1]+=max(v)
    for item in g['resistors']+g['conductances']:
        conductance=1/F(item['ohm']) if 'ohm' in item else F(item['siemens'])
        v=h*conductance*balance.integral(diff(item['left'],item['right']),left,right)
        stamp(item['left'],(v,v),F(1));stamp(item['right'],(v,v),F(-1))
    def exponential(p,sat,stamps,ref):
        bern=poly.bernstein(p,left,right)
        if max(bern)>45:raise ValueError('whole exponential domain exceeded')
        interval,diagnostic=exponential_integral(p,left,right)
        v=tuple(h*sat*(a-(right-left)) for a in interval)
        for node,coefficient in stamps:stamp(node,v,coefficient)
        terms.append(diagnostic|dict(ref=ref,interval_c=(down(v[0]),up(v[1]))))
    for q in g['bjts']:
        b,c,e=q['base'],q['collector'],q['emitter'];s=F(q['polarity'])
        bf=F(q['beta_forward']);br=F(q['beta_reverse']);sat=F(q['is_a'])
        exponential(poly.scale(diff(b,e),s/F(q['vt'])),sat,
                    ((b,s/bf),(c,s),(e,-s*(1+1/bf))),q['ref']+'/BE')
        exponential(poly.scale(diff(b,c),s/F(q['vt'])),sat,
                    ((b,s/br),(c,-s*(1+1/br)),(e,s)),q['ref']+'/BC')
    for d in g['diodes']:
        a,c=d['anode'],d['cathode']
        exponential(poly.scale(diff(a,c),1/(F(d['ideality'])*F(d['vt']))),F(d['is_a']),
                    ((a,F(1)),(c,F(-1))),d['ref'])
    return [(down(a),up(b)) for a,b in nodes],terms


def dynamic_charge(network,q,left,right):
    delta=[poly.evaluate(p,right)-poly.evaluate(p,left) for p in q];nodes=[F(0)]*94;boundary=F(0)
    def stamp(a,b,v):
        nonlocal boundary
        if a is None:boundary+=v
        else:nodes[a]+=v
        if b is None:boundary-=v
        else:nodes[b]-=v
    for (a,b,_,_,_),v in zip(network.network.branches,delta[:21]):stamp(a,b,v)
    s=F(network.network.latch.device.parameters.polarity)
    for i,terminals in enumerate(network.network.latch.terminals):
        b,c,e=[j for j,_ in terminals];stamp(b,e,s*delta[21+2*i]);stamp(b,c,s*delta[22+2*i])
    if sum(nodes)+boundary!=0:raise ValueError('exact charge conservation failed')
    return nodes,boundary
