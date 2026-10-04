"""Endpoint-preserving C7 bubble; candidate reconstruction, never a solution proof."""
from fractions import Fraction as F
import loudness_latch_directed_prefix as law
poly=law.real.poly
TARGET=20
ROW=114


def rebuild(network,source,x,y):
    h=F(source['h'])
    if h<=0 or len(x)!=94 or len(y)!=21:raise ValueError('complete positive support required')
    q=[poly.scale(p,F(b[3])) for p,b in zip(y,network.network.branches)]+[(F(0),)]*4
    equations=[];junctions=[]
    for port,yp in zip(law.real.event.ports(network)[:21],y):
        v=(-port['fixed'],)
        for i,a in port['a'].items():v=poly.add(v,poly.scale(x[i],a))
        equations.append(poly.add(poly.add(yp,poly.scale(v,-1)),poly.scale(poly.differentiate(yp),port['tau']/h)))
    for port in law.real.event.ports(network)[21:]:
        v=(port['fixed'],)
        for i,a in port['a'].items():v=poly.add(v,poly.scale(x[i],a))
        junctions.append((v,port['dep'],port['transit'],port['emission']))
    return source|dict(x=x,y_linear=y,q=q,equations=equations,junctions=junctions,
        junction_charge_policy='Q(v_quadratic); four zero polynomial placeholders carry no physical charge')


def candidate(network,affine,inverse,rhs):
    if len(inverse)!=119 or any(len(row)!=119 for row in inverse) or len(rhs)!=119:
        raise ValueError('complete candidate inverse and 119 signed RHS polynomials required')
    h=F(affine['h'])
    if h<=0:raise ValueError('positive physical duration required')
    force=(F(0),)
    for coefficient,p in zip(inverse[ROW],rhs):
        force=poly.add(force,poly.scale(tuple(map(F,p)),-F(coefficient)))
    amplitude=(poly.evaluate(force,F(0))-poly.evaluate(force,F(1)))/2
    bubble=(F(0),amplitude*h,-amplitude*h)
    direction=[-F(row[ROW]) for row in inverse[:94]]
    x=[poly.add(tuple(map(F,p)),poly.scale(bubble,d)) for p,d in zip(affine['x'],direction)]
    y=[tuple(map(F,p)) for p in affine['y_linear']]
    y[TARGET]=poly.add(y[TARGET],bubble)
    curved=rebuild(network,affine,x,y)
    for u in (F(0),F(1)):
        for field in ('x','y_linear','q','equations'):
            # RC equations include derivatives; only the three state fields are endpoint interfaces.
            if field=='equations':continue
            if any(poly.evaluate(a,u)!=poly.evaluate(tuple(map(F,b)),u) for a,b in zip(curved[field],affine[field])):
                raise ValueError('published endpoint changed')
    return curved,dict(target_memory_index=TARGET,target_descriptor_row=ROW,
        force_candidate_v_s=list(map(str,force)),amplitude_v_s=str(amplitude),
        bubble_v=list(map(str,bubble)),potential_direction=list(map(str,direction)),
        physical_duration_s=str(h),candidate_inverse_sha256=law.digest(inverse),
        rhs_polynomials_sha256=law.digest(rhs),endpoint_bubble_v=['0','0'],
        derivation='A=(f0(0)-f0(1))/2; p=A*h*u*(1-u); x=x_affine-X_v,C7*p; y_C7=y_affine+p',
        true_solution_claimed=False,all_constraints_rebuilt=True)
