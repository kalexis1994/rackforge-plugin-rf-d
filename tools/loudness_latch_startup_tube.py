"""First affine right-limit reconstruction and nonlinear mean-descriptor tube."""
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
import loudness_latch_dense_charge as poly
import loudness_latch_constitutive_enclosure as iv
import loudness_latch_weighted_descriptor as weighted
import loudness_latch_cell_propagation as cells
import loudness_latch_key_projection as event
import loudness_latch_post_key_origin as origin
from loudness_latch_bdf_probes import pack
from circuit66_decimal_static import evaluate

def prepare(network,initial,endpoint):
    h=F(endpoint.time_s)-F(initial.time_s)
    if initial.time_s!=0 or initial.previous is not None or initial.key_v!=10 or endpoint.key_v!=10 or h<=0:
        raise ValueError('two real post-KEY endpoints with explicit t=0+ origin required')
    if event.dc.digest(pack(initial)['current'])!=event.dc.digest(pack(endpoint)['previous']):raise ValueError('first interval lineage mismatch')
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
    return dict(x=x,q=q,y_linear=y,equations=equations,junctions=junctions,h=h,
        support_sha256=[event.dc.digest(pack(v)) for v in (initial,endpoint)],
        junction_charge_policy='Q(v_affine); four zero polynomial placeholders carry no physical charge',
        fabricated_history=False)

def initial_memory(network,prepared,dc,weights):
    out=[];w=list(map(F,weights));p=network.network.latch.device.parameters
    for row in dc['memory_enclosure']['rows']:
        k=row['index'];scale=F(row['scale_c_per_v']);actual=tuple(map(F,row['ideal_charge_interval_c']))
        if k<21:reconstructed=(poly.evaluate(prepared['q'][k],F(0)),)*2
        else:
            v,dep,t,em=prepared['junctions'][k-21]
            reconstructed=iv.junction_bounds(dep,t,p.saturation_a,em,poly.evaluate(v,F(0)))[0]
        diff=iv.sub(actual,reconstructed);bound=iv.magnitude(diff)/scale
        out.append(dict(index=k,actual_charge_interval_c=list(map(str,actual)),reconstructed_initial_charge_interval_c=list(map(str,reconstructed)),
            charge_error_interval_c=list(map(str,diff)),coordinate_error_upper_v=str(bound),weight=str(w[k]),weighted_error_upper_v=str(w[k]*bound)))
    if len(out)!=25 or len(w)!=25 or any(v<=0 for v in w):raise ValueError('25 positive memory weights required')
    return dict(rows=out,weights=list(map(str,w)),error_upper_v=str(max(F(r['weighted_error_upper_v']) for r in out)),
        same_dc_norm=True,norm_conversion_factor='1',constitutive_initial_mismatch_included=True)

def query(network,g,prepared,u,precision=100):
    with localcontext() as ctx:
        ctx.prec=precision;cv=event.decimal;h=prepared['h'];x=[cv(poly.evaluate(v,F(u))) for v in prepared['x']]
        r,_=evaluate(g,x,precision,False);rates=[cv(poly.evaluate(poly.differentiate(q),F(u))/h) for q in prepared['q'][:21]]
        p=network.network.latch.device.parameters
        for v,dep,t,em in prepared['junctions']:
            _,cap,_=event.junction_values(dep,t,p.saturation_a,em,cv(poly.evaluate(v,F(u))))
            rates.append(cap*cv(poly.evaluate(poly.differentiate(v),F(u))/h))
        boundary=D(0);dynamic=[D(0)]*94
        for port,current in zip(event.ports(network),rates):
            for i,a in port['a'].items():dynamic[i]+=cv(a)*current
            boundary-=cv(sum(port['a'].values(),F(0)))*current
        return dict(kcl_a=list(map(str,[a+b for a,b in zip(r,dynamic)])),
            constraint_v=[str(cv(poly.evaluate(v,F(u)))) for v in prepared['equations']]+['0']*4,
            charge_rate_a=list(map(str,rates)),dynamic_conservation_error_a=str(sum(dynamic,D(0))+boundary))

def gains(network,g):
    out={}
    def gain(a,b):return sum(map(abs,event.dc.incidence(a,b).values()),F(0))
    for q in g['bjts']:
        out[q['ref']+'/BE']=gain(q['base'],q['emitter'])/F(q['vt'])
        out[q['ref']+'/BC']=gain(q['base'],q['collector'])/F(q['vt'])
    for d in g['diodes']:out[d['ref']]=gain(d['anode'],d['cathode'])/(F(d['ideality'])*F(d['vt']))
    for p in event.ports(network)[21:]:out['junction-constraint/'+str(p['index'])]=sum(map(abs,p['a'].values()),F(0))
    return out

def inflated_cover(constant,terms,power_gains,left,right,radius):
    radius=F(radius)
    if radius<=0:raise ValueError('positive potential tube radius required')
    n=len(constant);product=[list(row) for row in constant];diagnostics=[]
    for t in terms:
        b=poly.bernstein(t['power'],F(left),F(right));padding=radius*power_gains[t['ref']];lo,hi=min(b)-padding,max(b)+padding
        if t['kind']=='exponential':
            if hi>45:raise ValueError('whole nonlinear tube exponential domain exceeded')
            value=iv.scale(iv.exp_interval((lo,hi)),t['factor'])
        elif t['kind']=='capacitance':
            args=(t['depletion'],t['transit'],t['saturation'],t['emission'])
            value=(iv.junction_bounds(*args,lo)[1][0],iv.junction_bounds(*args,hi)[1][1])
            if value[0]<=0:raise ValueError('positive whole tube junction capacitance required')
        else:raise ValueError('registered variable coefficient required')
        diagnostics.append(dict(ref=t['ref'],kind=t['kind'],lower=str(lo),upper=str(hi),padding=str(padding),
            coefficient_interval=list(map(str,value))))
        for i,j,c in t['coefficients']:product[i][j]=iv.add(product[i][j],iv.scale(value,c))
    defect=[[iv.sub((F(i==j),)*2,v) for j,v in enumerate(row)] for i,row in enumerate(product)]
    sums=[sum(map(iv.magnitude,row),F(0)) for row in defect];q=max(sums)
    return dict(left=str(left),right=str(right),potential_radius_v=str(radius),coefficient_domains=diagnostics,
        preconditioned_defect_intervals=cells.packed_matrix(defect),defect_row_upper=list(map(str,sums)),
        contraction_upper=str(q),strict_contraction=q<1,includes_mean_descriptors=True)

def forcing(network,g,prepared,left,right):
    result=iv.residual_bounds(network,g,prepared,F(left),F(right));duration=prepared['h']*(F(right)-F(left))
    dpoint=[max(map(abs,poly.bernstein(v,F(left),F(right)))) for v in prepared['equations']]+[F(0)]*4
    return result,dict(left=str(left),right=str(right),duration_s=str(duration),
        nodal_point_a=list(map(str,result['constitutive_pointwise_upper_a'])),nodal_l1_c=list(map(str,result['constitutive_l1_upper_c'])),
        constraint_point_v=list(map(str,dpoint)),constraint_l1_v_s=list(map(str,[duration*v for v in dpoint])))

def close(cases,anchor,radius,initial_node_error):
    anchor=F(anchor);radius=F(radius);initial_node_error=F(initial_node_error)
    if anchor<0 or initial_node_error<0 or radius<=0:raise ValueError('nonnegative initial errors and positive tube required')
    if not cases or any(not c.get('inverse_certified',False) for c in cases):
        return dict(accepted=False,reason='descriptor cover not invertible',actual_dae_error_bound=False)
    try:propagation=cells.propagate(cases)
    except ValueError as error:return dict(accepted=False,reason=str(error),actual_dae_error_bound=False)
    node=F(propagation['peak_node_from_weighted_anchor_gain_upper'])*anchor+F(propagation['peak_zero_anchor_node_upper_v'])
    memory=F(propagation['endpoint_weighted_anchor_gain_upper'])*anchor+F(propagation['endpoint_zero_anchor_memory_upper_v'])
    self_contained=initial_node_error<radius and node<radius
    return dict(accepted=self_contained,reason=None if self_contained else 'comparison bound escapes assumed potential tube',
        potential_radius_v=str(radius),initial_node_error_upper_v=str(initial_node_error),initial_memory_error_upper_v=str(anchor),
        peak_node_error_upper_v=str(node),endpoint_weighted_memory_error_upper_v=str(memory),propagation=propagation,
        mean_descriptor_comparison=True,nonlinear_tube_self_consistent=self_contained,
        actual_dae_error_bound=self_contained,global_1mv_gate_closed=False)
