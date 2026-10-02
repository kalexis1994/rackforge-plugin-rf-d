"""Offline integrated charge balance on a declared rational reconstruction."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import loudness_latch_dense_charge as poly
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift,evaluate as static_values

COUNTS=(8,16,32,64)


def integral(p,left,right):
    if left>=right:raise ValueError('positive integration interval required')
    return sum((v*(right**(i+1)-left**(i+1))/F(i+1) for i,v in enumerate(p)),F(0))


def decimal_polynomial(p,u):
    out=D(0)
    for v in reversed(p):out=out*u+v
    return out


def simpson(values,left,right,count,h=F(1)):
    maximum=len(values)-1
    if count<2 or count%2 or maximum%count or left>=right:raise ValueError('nested even Simpson grid required')
    step=maximum//count;factor=law.decimal_fraction(h*(right-left)/F(3*count))
    return [factor*sum(((1 if i in (0,count) else 4 if i%2 else 2)*values[i*step][j]
                       for i in range(count+1)),D(0)) for j in range(len(values[0]))]


def constitutive(prepared,u,parameters):
    out=[]
    for voltage,dep,transit,scale in prepared['junctions']:
        v=law.decimal_fraction(poly.evaluate(voltage,u))
        out.append(curvature.junction_values(dep,transit,parameters.saturation_a,scale,v)[0])
    return out


def partition(prepared,left,right,depth=40):
    if left>=right:raise ValueError('positive piece partition required')
    covers=[poly.isolate_zero(p,left,right,depth) for p in prepared['knees']]
    if any(c['coincident'] for c in covers):raise ValueError('coincident knee requires another declared policy')
    bridges=sorted((b['left'],b['right']) for c in covers for b in c['brackets']);merged=[]
    for a,b in bridges:
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    points=sorted(set((left,right,*(t for c in covers for t in c['exact_points']),
                       *(t for ab in merged for t in ab))))
    smooth=[]
    for a,b in zip(points,points[1:]):
        if any(l<=a and b<=r for l,r in merged):continue
        smooth.append(dict(left=a,right=b,below=[poly.evaluate(p,(a+b)/2)<0 for p in prepared['knees']]))
    return dict(covers=covers,smooth=smooth,bridges=merged,exact_points=sorted(set(t for c in covers for t in c['exact_points'])))


def domain_certificate(network,g,prepared,left,right):
    xp=prepared['x'];items=[]
    def node(i):return xp[i] if isinstance(i,int) else (F(g['fixed'][i]),)
    def voltage(a,b,scale,polarity=1):return poly.scale(poly.add(node(a),poly.scale(node(b),-1)),F(polarity)/F(scale))
    for q in g['bjts']:
        for other in ('emitter','collector'):items.append((q['ref']+'/'+other,voltage(q['base'],q[other],q['vt'],q['polarity'])))
    for q in g['diodes']:items.append((q['ref'],voltage(q['anode'],q['cathode'],F(q['ideality'])*F(q['vt']))))
    for i,(v,_,_,scale) in enumerate(prepared['junctions']):items.append(('charge/'+str(i),poly.scale(v,1/F(scale))))
    bounds=[(name,max(poly.bernstein(p,left,right))) for name,p in items]
    name,value=max(bounds,key=lambda pair:pair[1])
    return dict(count=len(bounds),maximum_upper=value,maximum_ref=name,passed=all(v<=45 for _,v in bounds))


def integrate(network,g,prepared,left,right,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision;cv=law.decimal_fraction;p=network.network.latch.device.parameters
        plan=partition(prepared,left,right);maximum=max(COUNTS);xp=[tuple(map(cv,v)) for v in prepared['x']]
        values=[]
        for i in range(maximum+1):
            u=cv(left+(right-left)*F(i,maximum));x=[decimal_polynomial(v,u) for v in xp]
            r,_=static_values(g,x,precision,jacobian=False);values.append(r)
        chain_grids=[]
        for piece in plan['smooth']:
            a,b=piece['left'],piece['right'];grid=[]
            for i in range(maximum+1):
                u=a+(b-a)*F(i,maximum);rates=[]
                for voltage,dep,transit,scale in prepared['junctions']:
                    v=cv(poly.evaluate(voltage,u));slope=cv(poly.evaluate(poly.differentiate(voltage),u))
                    _,c,_=curvature.junction_values(dep,transit,p.saturation_a,scale,v);rates.append(c*slope)
                grid.append(rates)
            chain_grids.append((a,b,grid))
        bridge=[D(0)]*4
        for a,b in plan['bridges']:
            q0=constitutive(prepared,a,p);q1=constitutive(prepared,b,p)
            bridge=[v+y-x for v,x,y in zip(bridge,q0,q1)]
        delta_poly=[cv(poly.evaluate(q,right)-poly.evaluate(q,left)) for q in prepared['q']]
        q0=constitutive(prepared,left,p);q1=constitutive(prepared,right,p);delta_law=[b-a for a,b in zip(q0,q1)]
        delta_const=delta_poly[:21]+delta_law;duration=cv(prepared['h']*(right-left))
        rows=[]
        for count in COUNTS:
            static=simpson(values,left,right,count,prepared['h']);chain=list(bridge)
            for a,b,grid in chain_grids:chain=[v+w for v,w in zip(chain,simpson(grid,a,b,count))]
            rows.append(dict(count=count,static_integral_c=static,chain_integral_c=chain,
                             chain_endpoint_gate=curvature.metrics(delta_law,chain)))
        return dict(levels=rows,delta_poly_c=delta_poly,delta_constitutive_c=delta_const,bridge_c=bridge,
            duration_s=duration,partition=plan,static_samples=maximum+1,
            chain_samples=(maximum+1)*len(chain_grids),
            mean_branch_v=[cv(integral(e,left,right)/(right-left)) for e in prepared['equations']])
