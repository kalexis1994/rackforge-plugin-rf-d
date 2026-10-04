"""Clock-free charge-consistent KEY projection and parameterized Banach proof."""
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from copy import deepcopy
import loudness_latch_dc_anchor as dc
from loudness_latch_continuous_descriptor import descriptor
from circuit66_decimal_static import evaluate
from loudness_latch_directional_curvature import junction_values

iv=dc.iv
NV=94
NM=25
N=119
SCALE=F(1e-12)
RATE_WEIGHT=F(1,10**6)  # seconds; normalized rate coordinate has volts
WEIGHTS=[F(1)]*NV+[RATE_WEIGHT]*NM

def decimal(v):
    v=F(v);return D(v.numerator)/D(v.denominator)

def ports(network):
    net=network.network;p=net.latch.device.parameters;out=[]
    for k,(a,b,fixed,cap,resistance) in enumerate(net.branches):
        out.append(dict(index=k,kind='linear',a=dc.incidence(a,b),fixed=F(fixed) if b is None else F(0),scale=F(cap),tau=F(cap)*F(resistance)))
    for k,terminals in enumerate(net.latch.terminals):
        b,c,e=[i for i,_ in terminals]
        for offset,other,dep,transit,emission in ((0,2,p.depletion_be,p.transit_forward_s,p.emission_be_v),(1,1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
            a={i:F(p.polarity)*v for i,v in dc.incidence(b,e if other==2 else c).items()}
            fixed=F(p.polarity)*sum((F(v)*s for (i,v),s in ((terminals[0],1),(terminals[other],-1)) if i is None),F(0))
            out.append(dict(index=21+2*k+offset,kind='junction',a=a,fixed=fixed,scale=SCALE,tau=F(0),dep=dep,transit=transit,sat=p.saturation_a,emission=emission))
    return out

def residual(network,g,values,targets,precision=80,jacobian=True):
    if len(values)!=N or len(targets)!=NM:raise ValueError('119 unknowns and 25 target coordinates required')
    with localcontext() as ctx:
        ctx.prec=precision;x=[decimal(v) for v in values];y=[decimal(v) for v in targets]
        r,_=evaluate(g,x[:NV],precision,jacobian=False);r+= [D(0)]*NM
        for port in ports(network):
            k=port['index'];voltage=sum((decimal(a)*x[i] for i,a in port['a'].items()),D(0))
            voltage+=decimal(port['fixed']) if port['kind']=='junction' else -decimal(port['fixed'])
            for i,a in port['a'].items():r[i]+=decimal(a*port['scale'])*x[NV+k]
            if port['kind']=='linear':r[NV+k]=y[k]-voltage+decimal(port['tau'])*x[NV+k]
            else:
                q,_,_=junction_values(port['dep'],port['transit'],port['sat'],port['emission'],voltage)
                r[NV+k]=y[k]-q/decimal(port['scale'])
        h=descriptor(network,g,x[:NV],precision)[0] if jacobian else None
        return r,h

def linear_solve(matrix,rhs):
    """Decimal partial pivoting; all arithmetic remains in the caller's context."""
    n=len(rhs)
    if n==0 or len(matrix)!=n or any(len(row)!=n for row in matrix):raise ValueError('complete square linear system required')
    a=[list(row)+[v] for row,v in zip(matrix,rhs)]
    for k in range(n):
        pivot=max(range(k,n),key=lambda i:abs(a[i][k]))
        if not a[pivot][k]:raise ValueError('singular projection Jacobian')
        a[k],a[pivot]=a[pivot],a[k]
        for i in range(k+1,n):
            if not a[i][k]:continue
            f=a[i][k]/a[k][k];a[i][k]=D(0)
            for j in range(k+1,n+1):a[i][j]-=f*a[k][j]
    x=[D(0)]*n
    for i in range(n-1,-1,-1):x[i]=(a[i][n]-sum((a[i][j]*x[j] for j in range(i+1,n)),D(0)))/a[i][i]
    return x

def diagnostics(r,delta=None):
    out=dict(kcl_upper_a=str(max(map(abs,r[:NV]))),coordinate_constraint_upper_v=str(max(map(abs,r[NV:]))))
    if delta is not None:out['weighted_correction_upper_v']=str(max(abs(v)*decimal(w) for v,w in zip(delta,WEIGHTS)))
    return out

def newton(network,g,seed,targets):
    attempts=[]
    with localcontext() as ctx:
        ctx.prec=80;x=[decimal(v) for v in seed];last=D('Infinity')
        for k in range(64):
            r,h=residual(network,g,x,targets);delta=linear_solve(h,[-v for v in r]);info=diagnostics(r,delta)
            correction=D(info['weighted_correction_upper_v'])
            record=dict(iteration=k,values=list(map(str,x)),**info,trials=[])
            attempts.append(record)
            if max(map(abs,r[:NV]))<=D('1e-35') and max(map(abs,r[NV:]))<=D('1e-35') and correction<=D('1e-25'):
                return dict(converged=True,values=list(map(str,x)),iterations=attempts,precision=80,clock_advanced=False)
            merit=max(max(map(abs,r[:NV]))/D('1e-11'),max(map(abs,r[NV:]))/D('1e-14'))
            accepted=False
            for half in range(25):
                alpha=D(1)/D(2)**half;trial=[v+alpha*d for v,d in zip(x,delta)]
                try:
                    rt,_=residual(network,g,trial,targets,jacobian=False)
                    mt=max(max(map(abs,rt[:NV]))/D('1e-11'),max(map(abs,rt[NV:]))/D('1e-14'))
                    good=mt<(1-D('1e-4')*alpha)*merit
                    record['trials'].append(dict(halvings=half,merit=str(mt),accepted=good,domain_rejected=False))
                    if good:x=trial;last=correction;accepted=True;break
                except ValueError as error:record['trials'].append(dict(halvings=half,accepted=False,domain_rejected=True,reason=str(error)))
            if not accepted:return dict(converged=False,values=list(map(str,x)),iterations=attempts,reason='line search exhausted',clock_advanced=False)
    return dict(converged=False,values=list(map(str,x)),iterations=attempts,reason='iteration budget exhausted',clock_advanced=False)

def compile_event(network,g,center,targets,inverse,weights=WEIGHTS):
    x=list(map(F,center));y=list(map(F,targets));w=list(map(F,weights))
    if len(x)!=N or len(y)!=NM or len(w)!=N or any(v<=0 for v in w):raise ValueError('complete projection center, charges and positive weights required')
    z=[[w[i]*F(v) for v in row] for i,row in enumerate(inverse)]
    extended=deepcopy(g);extended['node_count']=N
    # compile_graph lifts currents and preconditions each shared exponential.
    static=dc.compile_graph(extended,x,[[str(v) for v in row] for row in z])
    linear=[[F(i==j)-v[0] for j,v in enumerate(row)] for i,row in enumerate(static['constant_defect'])]
    eta=list(static['preconditioned_residual']);junctions=[]
    for port in ports(network):
        k=port['index'];row=NV+k;voltage=sum((a*x[i] for i,a in port['a'].items()),F(0))
        voltage+=port['fixed'] if port['kind']=='junction' else -port['fixed']
        mass=[sum((z[i][j]*a*port['scale'] for j,a in port['a'].items()),F(0)) for i in range(N)]
        if port['kind']=='linear':value=y[k]-voltage+port['tau']*x[row];constraint=(value,value)
        else:
            charge,cap=iv.junction_bounds(port['dep'],port['transit'],port['sat'],port['emission'],voltage)
            constraint=iv.sub((y[k],y[k]),iv.scale(charge,1/port['scale']))
            junctions.append(dict(port=port,center_voltage=voltage,radius_gain=sum((abs(a)/w[j] for j,a in port['a'].items()),F(0)),
                coefficients=[(i,j,z[i][row]*a/port['scale']/w[j]) for i in range(N) for j,a in port['a'].items() if z[i][row]*a]))
        for i in range(N):
            eta[i]=iv.add(eta[i],iv.add((mass[i]*x[row],mass[i]*x[row]),iv.scale(constraint,z[i][row])))
            linear[i][row]+=mass[i]+z[i][row]*port['tau']
            if port['kind']=='linear':
                for j,a in port['a'].items():linear[i][j]-=z[i][row]*a
    constant=[[(F(i==j)-v/w[j],)*2 for j,v in enumerate(row)] for i,row in enumerate(linear)]
    # All static exponents depend on voltage coordinates, whose weight is one.
    terms=[]
    for term in static['terms']:
        terms.append(term|dict(coefficients=[(i,j,c/w[j]) for i,j,c in term['coefficients']]))
    return dict(constant_defect=constant,terms=terms,junctions=junctions,preconditioned_residual=eta,
        charge_sensitivity=[[z[i][NV+k] for k in range(NM)] for i in range(N)],weights=w)

def certify(compiled,radius,charge_uncertainty=None):
    radius=F(radius)
    if radius<=0:raise ValueError('positive normalized event radius required')
    a=[list(row) for row in compiled['constant_defect']];domains=[]
    for term in compiled['terms']:
        c=F(term['center_exponent']);delta=radius*F(term['radius_gain']);lo,hi=c-delta,c+delta
        if hi>45:raise ValueError('whole event static exponential domain exceeded')
        e=iv.exp_interval((lo,hi));domains.append(dict(ref=term['ref'],range=list(map(str,(lo,hi)))))
        for i,j,c in term['coefficients']:a[i][j]=iv.sub(a[i][j],iv.scale(e,c))
    for term in compiled['junctions']:
        p=term['port'];c=term['center_voltage'];delta=radius*term['radius_gain'];lo,hi=c-delta,c+delta
        low=iv.junction_bounds(p['dep'],p['transit'],p['sat'],p['emission'],lo)[1][0]
        high=iv.junction_bounds(p['dep'],p['transit'],p['sat'],p['emission'],hi)[1][1]
        if low<=0:raise ValueError('positive whole event junction capacitance required')
        domains.append(dict(ref='charge/'+str(p['index']),range=list(map(str,(lo/F(p['emission']),hi/F(p['emission']))))))
        for i,j,c in term['coefficients']:a[i][j]=iv.add(a[i][j],iv.scale((low,high),c))
    eta=list(compiled['preconditioned_residual']);uncertainty=[(F(0),F(0))]*NM if charge_uncertainty is None else [tuple(map(F,v)) for v in charge_uncertainty]
    if len(uncertainty)!=NM or any(lo>hi for lo,hi in uncertainty):raise ValueError('25 ordered charge-coordinate deviations required')
    for i,row in enumerate(compiled['charge_sensitivity']):
        for coefficient,value in zip(row,uncertainty):eta[i]=iv.add(eta[i],iv.scale(value,coefficient))
    proof=dc.prove(a,eta,radius)
    # dc.prove is dimensionless Banach algebra. Rename mixed-unit quantities.
    for old,new in (('radius_v','weighted_radius_v'),('posterior_error_upper_v','weighted_posterior_error_upper_v'),('row_image_radius_v','weighted_row_image_radius_v'),('eta_upper_v','weighted_eta_upper_v')):proof[new]=proof.pop(old)
    return proof|dict(exponent_ranges=domains,weights=list(map(str,compiled['weights'])),parameterized_charge_box=charge_uncertainty is not None,
        charge_coordinate_deviation_intervals_v=[list(map(str,v)) for v in uncertainty])
