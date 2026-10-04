"""Real-clock reconstruction and exact quadratic interface bridges, offline only."""
from fractions import Fraction as F
import loudness_latch_startup_tube as tube
import loudness_latch_startup_blocks as blocks
from loudness_latch_bdf_probes import pack
poly=tube.poly;event=tube.event;origin=tube.origin
BISECTIONS=32

def prepare(network,initial,endpoint):
    h=F(endpoint.time_s)-F(initial.time_s)
    if initial.time_s<=0 or initial.key_v!=10 or endpoint.key_v!=10 or h<=0:
        raise ValueError('positive real-clock post-KEY support required')
    if event.dc.digest(pack(initial)['current'])!=event.dc.digest(pack(endpoint)['previous']):raise ValueError('adjacent real history required')
    x0=origin.state_values(initial.current);x1=origin.state_values(endpoint.current)
    y0=origin.charge_coordinates(network.network,initial.current);y1=origin.charge_coordinates(network.network,endpoint.current)
    x=[(a,b-a) for a,b in zip(x0,x1)];y=[(a,b-a) for a,b in zip(y0[:21],y1[:21])]
    q=[poly.scale(v,F(branch[3])) for v,branch in zip(y,network.network.branches)]+[(F(0),)]*4
    equations=[];junctions=[]
    for p,yp in zip(event.ports(network)[:21],y):
        voltage=(-p['fixed'],)
        for i,a in p['a'].items():voltage=poly.add(voltage,poly.scale(x[i],a))
        equations.append(poly.add(poly.add(yp,poly.scale(voltage,-1)),poly.scale(poly.differentiate(yp),p['tau']/h)))
    for p in event.ports(network)[21:]:
        voltage=(p['fixed'],)
        for i,a in p['a'].items():voltage=poly.add(voltage,poly.scale(x[i],a))
        junctions.append((voltage,p['dep'],p['transit'],p['emission']))
    return dict(start_s=str(F(initial.time_s)),end_s=str(F(endpoint.time_s)),x=x,q=q,y_linear=y,equations=equations,junctions=junctions,h=h,
        support_sha256=[event.dc.digest(pack(v)) for v in (initial,endpoint)],
        junction_charge_policy='Q(v_affine); four zero polynomial placeholders carry no physical charge',
        fabricated_history=False)

def continuity(network,left,right,left_end,right_start):
    if F(left_end)!=F(right_start):raise ValueError('contiguous real clocks required')
    def endpoint(prepared,u):
        x=[poly.evaluate(tuple(map(F,p)),u) for p in prepared['x']]
        y=[poly.evaluate(tuple(map(F,p)),u) for p in prepared['y_linear']]
        v=[sum((a*x[i] for i,a in port['a'].items()),F(0))+port['fixed'] for port in event.ports(network)[21:]]
        return dict(potential_v=list(map(str,x)),linear_memory_v=list(map(str,y)),junction_voltage_v=list(map(str,v)))
    a=endpoint(left,F(1));b=endpoint(right,F(0))
    if a!=b:raise ValueError('reconstructed interface is discontinuous')
    return dict(time_s=str(F(left_end)),endpoint_sha256=event.dc.digest(a),start_sha256=event.dc.digest(b),
        potential_continuity=True,linear_memory_continuity=True,constitutive_memory_continuity=True,
        constitutive_reason='same junction voltage, same frozen Q law',charge_reset=False)

def bridge(old,new):
    if not old['accepted'] or not new['accepted']:raise ValueError('two accepted metrics required')
    p=[[F(v) for v in row] for row in old['metric']];q=[[F(v) for v in row] for row in new['metric']]
    for matrix in (p,q):
        if len(matrix)!=4 or any(len(row)!=4 for row in matrix) or not blocks.quadratic.ldlt(matrix)['positive_definite']:raise ValueError('complete positive definite metric required')
    oldnormal=2*F(old['anchor_normalization_upper']);newnormal=2*F(new['anchor_normalization_upper'])
    if oldnormal<=0 or newnormal<=0:raise ValueError('positive norm normalizations required')
    if p==q and oldnormal==newnormal:
        return dict(old_metric_sha256=event.dc.digest(old['metric']),new_metric_sha256=event.dc.digest(new['metric']),
            identical_norm=True,factor_upper='1',alpha_upper='1',bisections=0,probes=[],final_upper_ldlt=None)
    pi=blocks.quadratic.invert(p);product=[[sum((pi[i][k]*q[k][j] for k in range(4)),F(0)) for j in range(4)] for i in range(4)]
    lo=max(q[i][i]/p[i][i] for i in range(4));hi=max(sum(map(abs,row),F(0)) for row in product)+1
    seed_lo=lo;seed_hi=hi;probes=[]
    def query(alpha):return blocks.quadratic.ldlt([[alpha*p[i][j]-q[i][j] for j in range(4)] for i in range(4)])
    def save(alpha,proof):return dict(alpha=str(alpha),positive_definite=proof['positive_definite'],failed_at=proof['failed_at'],pivot_sha256=event.dc.digest(proof['pivots']))
    proof=query(hi)
    if not proof['positive_definite']:raise ValueError('strict generalized bridge seed failed')
    probes.append(save(hi,proof))
    for _ in range(BISECTIONS):
        mid=(lo+hi)/2;candidate=query(mid);probes.append(save(mid,candidate))
        if candidate['positive_definite']:hi=mid;proof=candidate
        else:lo=mid
    root=blocks.quadratic.sqrt_bounds(hi);factor=oldnormal/newnormal*root[1]
    return dict(old_metric_sha256=event.dc.digest(old['metric']),new_metric_sha256=event.dc.digest(new['metric']),
        identical_norm=False,seed_lower=str(seed_lo),seed_upper=str(seed_hi),alpha_lower=str(lo),alpha_upper=str(hi),
        sqrt_alpha_bracket=list(map(str,root)),old_normalization=str(oldnormal),new_normalization=str(newnormal),
        factor_upper=str(factor),bisections=BISECTIONS,probes=probes,final_upper_ldlt=proof)

def transfer(previous,certificate):
    if not previous['accepted'] or not previous['actual_dae_error_bound']:raise ValueError('certified preceding interval required')
    p=previous['propagation'];a=list(map(F,p['endpoint_anchor_v']));b=list(map(F,p['endpoint_forced_v']))
    factor=F(certificate['factor_upper'])
    if len(a)!=6 or len(b)!=6 or min(a+b)<0 or factor<=0:raise ValueError('six known nonnegative outgoing errors required')
    result=[x+y for x,y in zip(a,b)];result[5]*=factor
    return list(map(str,result))
