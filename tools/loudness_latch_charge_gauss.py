"""Offline Decimal Gauss-Legendre rules; scalar roots are not circuit solves."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import math
import loudness_latch_charge_balance as balance
import loudness_latch_dense_charge as poly
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import evaluate as static_values

ORDERS=(4,8,16)


def legendre(n,x):
    a=D(1);b=x
    for j in range(2,n+1):a,b=b,((2*j-1)*x*b-(j-1)*a)/j
    return b,n*(x*b-a)/(x*x-1)


def rule(order,precision):
    if order not in ORDERS or precision<40:raise ValueError('registered even Gauss order and Decimal40 required')
    with localcontext() as ctx:
        ctx.prec=precision;points=[];iterations=[];threshold=D(10)**(-precision+8)
        for i in range(order//2):
            x=D.from_float(math.cos(math.pi*(i+.75)/(order+.5)))
            for count in range(1,33):
                value,slope=legendre(order,x);dx=value/slope;x-=dx
                if abs(dx)<threshold:break
            else:raise ValueError('Legendre scalar root budget exhausted')
            _,slope=legendre(order,x);w=2/((1-x*x)*slope*slope)
            points.extend(((-x,w),(x,w)));iterations.append(count)
        moments=[curvature.metrics([D(0) if degree%2 else D(2)/(degree+1)],
            [sum((w*x**degree for x,w in points),D(0))]) for degree in range(2*order)]
        return dict(points=points,iterations=iterations,moments=moments)


def integrate(network,g,prepared,left,right,rules,precision):
    with localcontext() as ctx:
        ctx.prec=precision;cv=law.decimal_fraction;p=network.network.latch.device.parameters
        plan=balance.partition(prepared,left,right);xp=[tuple(map(cv,v)) for v in prepared['x']]
        junctions=[(tuple(map(cv,v)),tuple(map(cv,poly.differentiate(v))),dep,t,s)
                   for v,dep,t,s in prepared['junctions']]
        def quadrature(function,a,b,points,h=F(1)):
            half=cv((b-a)/2);mid=cv((a+b)/2);values=[]
            for x,w in points:values.append((w,function(mid+half*x)))
            return [half*cv(h)*sum((w*v[j] for w,v in values),D(0)) for j in range(len(values[0][1]))]
        def static(u):return static_values(g,[balance.decimal_polynomial(v,u) for v in xp],precision,jacobian=False)[0]
        def chain(u):
            out=[]
            for v,d,dep,t,s in junctions:
                _,c,_=curvature.junction_values(dep,t,p.saturation_a,s,balance.decimal_polynomial(v,u))
                out.append(c*balance.decimal_polynomial(d,u))
            return out
        bridge=[D(0)]*4
        for a,b in plan['bridges']:
            q0=balance.constitutive(prepared,a,p);q1=balance.constitutive(prepared,b,p)
            bridge=[v+y-x for v,x,y in zip(bridge,q0,q1)]
        qp=[cv(poly.evaluate(v,right)-poly.evaluate(v,left)) for v in prepared['q']]
        q0=balance.constitutive(prepared,left,p);q1=balance.constitutive(prepared,right,p);qc=qp[:21]+[b-a for a,b in zip(q0,q1)]
        levels=[]
        for order in ORDERS:
            points=rules[order]['points'];current=quadrature(static,left,right,points,prepared['h']);charge=list(bridge)
            for piece in plan['smooth']:
                charge=[v+w for v,w in zip(charge,quadrature(chain,piece['left'],piece['right'],points))]
            levels.append(dict(count=order,static_integral_c=current,chain_integral_c=charge,
                chain_endpoint_gate=curvature.metrics(qc[21:],charge)))
        return dict(levels=levels,delta_poly_c=qp,delta_constitutive_c=qc,bridge_c=bridge,
            duration_s=cv(prepared['h']*(right-left)),partition=plan,
            mean_branch_v=[cv(balance.integral(v,left,right)/(right-left)) for v in prepared['equations']])
