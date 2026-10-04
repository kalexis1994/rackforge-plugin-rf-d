"""Explicit offline event-to-BDF adapter; conserve charge, publish voltages."""
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from loudness_latch_increment_reference import IncrementState,pair
from loudness_chain94_reference import State as JointState
from loudness_contour_reference import State as ContourState
from loudness_latch_bdf_reference import History,coefficients
from loudness_latch_bdf_probes import pack,unpack
import loudness_latch_key_projection as law
iv=law.iv

def publish_pair(value):
    value=F(value);high=float(value);low=float(value-F(high))
    high,low=pair((high,low))
    return (high,low),abs(F(high)+F(low)-value)

def state_values(state):
    return [F(a)+F(b) for a,b in zip(state.joint.node_v,state.node_low_v)]

def charge_coordinates(network,state):
    values=[F(a)+F(b) for a,b in state.capacitor_pairs_v]
    values.extend(F(q)/law.SCALE for d in state.latch.devices for q in (d.be_c,d.bc_c))
    if len(values)!=25:raise ValueError('complete charge memory required')
    return values

def mirrors(network,state,key):
    expected=network.network.joint.state(state.joint.node_v,key).contour.node_v
    if state.joint.contour.node_v!=expected:raise ValueError('contour nodes, aliases and rails must mirror authoritative high nodes')
    network.validate(History(state,None,None,0.,key,None))
    return True

def publish(network,pre,event):
    network.validate(pre)
    if (event.get('schema')!='rf-d/clock-free-key-event/v1' or event.get('time_s')!=0 or
        event.get('key_before_v')!=pre.key_v or pre.time_s!=0 or pre.previous is not None or
        event.get('previous_history') is not None or event.get('previous_dt_s') is not None or event.get('dc_state') is not False):
        raise ValueError('explicit clock-free right-limit event and preceding DC origin required')
    if event.get('pre_history_sha256')!=law.dc.digest(pack(pre)):raise ValueError('preceding history identity mismatch')
    if len(event['node_v'])!=94 or len(event['charge_coordinate_rates_v_per_s'])!=25:raise ValueError('complete event voltages and auxiliary rates required')
    targets=charge_coordinates(network.network,pre.current)
    if targets!=list(map(F,event['charge_coordinates_v'])):raise ValueError('event target must preserve all published preceding charges')
    node_pairs=[];node_errors=[];rate_pairs=[];rate_errors=[]
    for value in event['node_v']:
        p,e=publish_pair(value);node_pairs.append(p);node_errors.append(e)
    for value in event['charge_coordinate_rates_v_per_s']:
        p,e=publish_pair(value);rate_pairs.append(p);rate_errors.append(e)
    key=float(event['key_after_v']);old=pre.current;high=tuple(v[0] for v in node_pairs)
    contour=network.network.joint.state(high,key).contour
    # Rebuild node/rail/alias mirrors, retain every authoritative capacitor memory.
    joint=JointState(high,old.joint.audio_capacitor_v,old.joint.c10_v,
                     ContourState(contour.node_v,dict(old.joint.contour.capacitor_v)))
    state=IncrementState(joint,old.latch,tuple(v[1] for v in node_pairs),old.capacitor_pairs_v,old.circuit_signature)
    history=History(state,None,None,0.,key,None);network.validate(history);mirrors(network,state,key)
    origin=dict(schema='rf-d/post-key-bdf-origin/v1',role='right-limit-event',time_s=0,
        pre_history_sha256=law.dc.digest(pack(pre)),event_sha256=law.dc.digest(event),
        key_before_v=pre.key_v,key_after_v=key,history=pack(history),
        auxiliary_rate_pairs_v_per_s=rate_pairs,first_step_method='backward-euler-startup',
        fabricated_previous_history=False,dc_state=False)
    errors=dict(node_error_v=list(map(str,node_errors)),rate_error_v_per_s=list(map(str,rate_errors)),
                max_node_error_v=str(max(node_errors)),max_rate_error_v_per_s=str(max(rate_errors)))
    return origin,errors

def restore(network,origin):
    if (origin.get('schema')!='rf-d/post-key-bdf-origin/v1' or origin.get('role')!='right-limit-event' or
        origin.get('time_s')!=0 or origin.get('dc_state') is not False or origin.get('fabricated_previous_history') is not False or
        origin.get('first_step_method')!='backward-euler-startup'):
        raise ValueError('explicit post-event BDF origin required')
    history=unpack(network,origin['history'])
    if history.time_s!=0 or history.key_v!=origin['key_after_v'] or history.previous is not None:raise ValueError('event origin clock, source or history mismatch')
    rates=origin['auxiliary_rate_pairs_v_per_s']
    if len(rates)!=25 or any(len(p)!=2 or tuple(p)!=pair(p) for p in rates):raise ValueError('25 normalized auxiliary rate pairs required')
    mirrors(network,history.current,history.key_v)
    return history

def event_check(network,g,origin):
    history=restore(network,origin);x=state_values(history.current);y=charge_coordinates(network.network,history.current)
    rates=[sum(map(F,p),F(0)) for p in origin['auxiliary_rate_pairs_v_per_s']]
    r=law.dc.static_point(g,x);constraints=[]
    for port in law.ports(network):
        k=port['index'];rate=rates[k];v=sum((a*x[i] for i,a in port['a'].items()),F(0))
        v+=port['fixed'] if port['kind']=='junction' else -port['fixed']
        for i,a in port['a'].items():r[i]=iv.add(r[i],(a*port['scale']*rate,)*2)
        if port['kind']=='linear':constraint=(y[k]-v+port['tau']*rate,)*2
        else:
            q,_=iv.junction_bounds(port['dep'],port['transit'],port['sat'],port['emission'],v)
            constraint=iv.sub((y[k],)*2,iv.scale(q,1/port['scale']))
        constraints.append(constraint)
    with localcontext() as ctx:
        ctx.prec=100;decimal,_=law.residual(network,g,x+rates,y,100,False)
    kcl=max(map(iv.magnitude,r));branch=max(map(iv.magnitude,constraints));domains=[]
    def voltage(k):return x[k] if isinstance(k,int) else F(g['fixed'][k])
    for q in g['bjts']:
        for other in ('emitter','collector'):domains.append(F(q['polarity'])*(voltage(q['base'])-voltage(q[other]))/F(q['vt']))
    for d in g['diodes']:domains.append((voltage(d['anode'])-voltage(d['cathode']))/(F(d['ideality'])*F(d['vt'])))
    for p in law.ports(network)[21:]:domains.append((sum((a*x[i] for i,a in p['a'].items()),F(0))+p['fixed'])/F(p['emission']))
    return dict(kcl_intervals_a=[list(map(str,v)) for v in r],constraint_intervals_v=[list(map(str,v)) for v in constraints],
        decimal100_residual=list(map(str,decimal)),kcl_upper_a=str(kcl),constraint_upper_v=str(branch),
        max_exponent=str(max(domains)),domain_passed=max(domains)<=45,
        gates_passed=kcl<F(1,10**11) and branch<F(1,10**14) and max(domains)<=45)

def discrete_check(network,g,old,new,h):
    """Independent Decimal100 charge BDF residual; includes linear RC constraints."""
    with localcontext() as ctx:
        ctx.prec=100;x=state_values(new.current);y=charge_coordinates(network.network,new.current)
        old_y=charge_coordinates(network.network,old.current);older_y=old_y if old.previous is None else charge_coordinates(network.network,old.previous)
        if old.previous is None:a0,a2=law.decimal(1),law.decimal(0)
        else:
            c=coefficients(h,old.previous_dt_s);a0,a2=law.decimal(c['a0']),law.decimal(c['a2'])
        rates=[(a0*(law.decimal(a)-law.decimal(b))-a2*(law.decimal(b)-law.decimal(c)))/law.decimal(h) for a,b,c in zip(y,old_y,older_y)]
        residual,_=law.residual(network,g,x+list(map(F,rates)),y,100,False)
        # residual() is the event system: lower rows are constitutive error,
        # while the rates above provide the actual accepted discrete derivative.
        return dict(decimal100_kcl_upper_a=str(max(map(abs,residual[:94]))),
            decimal100_linear_constraint_upper_v=str(max(map(abs,residual[94:115]))),
            decimal100_junction_coordinate_mismatch_upper_v=str(max(map(abs,residual[115:]))),
            kcl_passed=max(map(abs,residual[:94]))<D('1e-11'),linear_constraint_passed=max(map(abs,residual[94:115]))<D('1e-14'),
            method='backward-euler-startup' if old.previous is None else 'variable-bdf2-charge/v1',
            ideal_temporal_error_proven=False)
