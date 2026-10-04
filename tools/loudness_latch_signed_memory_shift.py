"""Certified particular-coordinate shift for C7 forcing, offline only."""
from fractions import Fraction as F
import loudness_latch_residual_action as action
prior=action.prior
iv=action.iv
poly=action.poly
up=action.up
TARGET=20
ROW=94+TARGET


def primitive(forcing,duration,initial):
    h=F(duration)
    if h<=0 or not forcing:raise ValueError('nonempty forcing and positive physical duration required')
    return (F(initial),)+tuple(h*F(v)/F(i+1) for i,v in enumerate(forcing))


def action_difference(cert,row,scale):
    d=F(scale)
    if d<=0 or not cert['mean_descriptor_uncertainty_included'] or cert['independent_remainders_cancelled']:
        raise ValueError('positive scale and complete independent action remainder required')
    err=F(cert['preconditioned_remainder_upper'][row])/d
    correction=iv.magnitude(tuple(map(F,cert['first_correction_intervals'][row])))/d
    tail=F(cert['tail_upper'][row])
    coarse=F(cert['row_defect_upper'][row])/(1-F(cert['contraction_upper']))*F(cert['preconditioned_peak_upper'])/d
    if min(err,correction,tail,coarse)<0:raise ValueError('nonnegative action difference budgets required')
    return up(err+min(correction+tail,coarse))


def shifted_cell(original,inverse,scales,weights,metric,initial):
    n=119;w=list(map(F,weights));d=list(map(F,scales));inv=[[tuple(map(F,v)) for v in row] for row in inverse]
    if len(inv)!=n or any(len(row)!=n for row in inv) or len(w)!=25 or len(d)!=n or min(w+d)<=0:
        raise ValueError('full 119-equation inverse and unchanged positive norms required')
    if any(lo>hi for row in inv for lo,hi in row):raise ValueError('ordered inverse intervals required')
    if not metric['accepted'] or not prior.blocks.quadratic.ldlt(metric['metric'])['positive_definite']:
        raise ValueError('accepted fixed positive metric required')
    action_cert=original['action'];h=F(original['forcing_inputs']['duration_s']);pmetric=[[F(v) for v in row] for row in metric['metric']]
    normal=2*F(metric['anchor_normalization_upper'])
    if normal<=0 or not action_cert['action_enclosed'] or not action_cert['point_and_l1'] or len(action_cert['subcells'])!=action.SUBCELLS:
        raise ValueError('complete archived point/L1 action required')
    f0=tuple(-F(v)/d[ROW] for v in action_cert['compiled_preconditioned_polynomials'][ROW])
    p=primitive(f0,h,initial);coupling=[F(0)]*22;shift_direct=[F(0)]*94;delta=F(0);peak=F(0);subs=[];last=F(0)
    for cert in action_cert['subcells']:
        a,b=F(cert['left']),F(cert['right'])
        if a!=last or b<=a:raise ValueError('contiguous complete action subcells required')
        bb=poly.bernstein(p,a,b);pr=iv.enclosing(min(bb),max(bb));dt=h*(b-a);peak=max(peak,iv.magnitude(pr))
        remainder=action_difference(cert,ROW,d[ROW]);delta+=dt*w[TARGET]*remainder
        vector=[iv.mul(iv.neg(inv[94+i][ROW]),pr) for i in range(25)]
        bounds=[w[i]*iv.magnitude(vector[i]) for i in range(21)]
        bounds.append(prior.blocks.quadratic.quadratic_upper(pmetric,[iv.scale(vector[i],w[i]) for i in range(21,25)])/normal)
        for i,v in enumerate(bounds):coupling[i]+=dt*v
        nodes=[iv.magnitude(iv.mul(inv[i][ROW],pr)) for i in range(94)]
        shift_direct=[max(x,y) for x,y in zip(shift_direct,nodes)]
        subs.append(dict(left=str(a),right=str(b),particular_interval_v=list(map(str,pr)),action_difference_upper_v_s=str(remainder),
            shifted_coupling_point_upper_v_s=list(map(str,bounds)),nodal_particular_upper_v=list(map(str,nodes))))
        last=b
    if last!=1:raise ValueError('complete particular forcing support required')
    m=original['metrics'];budget=list(map(F,m['block_forcing_l1_v']));direct=list(map(F,m['nodal_direct_v']))
    if len(budget)!=22 or len(direct)!=94 or min(budget+direct)<0:raise ValueError('full unchanged nonnegative original budgets required')
    budget[TARGET]=up(delta);budget=[up(a+b) for a,b in zip(budget,coupling)]
    endpoint=poly.evaluate(p,F(1));memory_peak=[F(0)]*22;memory_end=[F(0)]*22
    memory_peak[TARGET]=up(w[TARGET]*peak);memory_end[TARGET]=up(w[TARGET]*abs(endpoint))
    metrics=m|dict(block_forcing_l1_v=list(map(str,budget)),nodal_direct_v=list(map(str,[up(a+b) for a,b in zip(direct,shift_direct)])))
    return dict(index=original['index'],inverse_certified=True,forcing_inputs=original['forcing_inputs'],metrics=metrics,
        shift=dict(target_coordinate=TARGET,forcing_sign='minus inverse RHS',forcing_nominal_polynomial_v_s=list(map(str,f0)),particular_polynomial_v=list(map(str,p)),
            initial_v=str(F(initial)),endpoint_v=str(endpoint),subcells=subs,action_difference_l1_upper_v=str(up(delta)),
            shifted_coupling_l1_upper_v=list(map(lambda v:str(up(v)),coupling)),nodal_particular_upper_v=list(map(str,shift_direct)),
            memory_peak_added_v=list(map(str,memory_peak)),memory_endpoint_added_v=list(map(str,memory_end)),
            particular_is_candidate=True,uncertain_generator_times_particular_included=True,independent_remainders_cancelled=False))


def close(cells,initial,radius,initial_node):
    last=F(0)
    if len(initial)!=22:raise ValueError('22 actual incoming errors required')
    for row in cells:
        s=row['shift']
        if s['target_coordinate']!=TARGET or F(s['initial_v'])!=last or not s['uncertain_generator_times_particular_included']:
            raise ValueError('continuous zero-start particular and compensated generator required')
        p=tuple(map(F,s['particular_polynomial_v']))
        if poly.evaluate(p,0)!=last or poly.evaluate(p,1)!=F(s['endpoint_v']):raise ValueError('same particular endpoints required')
        for key in ('memory_peak_added_v','memory_endpoint_added_v'):
            v=list(map(F,s[key]))
            if len(v)!=22 or min(v)<0 or any(v[i] for i in range(22) if i!=TARGET):raise ValueError('same complete particular memory conversion required')
        last=F(s['endpoint_v'])
    result=prior.blocks.close(cells,initial,radius,initial_node)
    if 'propagation' not in result:return result
    p=result['propagation']
    for row,trace in zip(cells,p['trace']):
        s=row['shift'];trace['kernels_act_on']='z=e-p'
        trace['shifted_peak_forced_v']=trace['peak_forced_v'];trace['shifted_endpoint_forced_v']=trace['endpoint_forced_v']
        trace['peak_forced_v']=list(map(str,[up(F(a)+F(b)) for a,b in zip(trace['peak_forced_v'],s['memory_peak_added_v'])]))
        trace['endpoint_forced_v']=list(map(str,[up(F(a)+F(b)) for a,b in zip(trace['endpoint_forced_v'],s['memory_endpoint_added_v'])]))
    p['shifted_endpoint_forced_v']=p['endpoint_forced_v'];p['endpoint_forced_v']=p['trace'][-1]['endpoint_forced_v']
    p['known_particular_restored']=True;p['particular_endpoint_v']=str(last)
    return result|dict(auxiliary_coordinate_shift=True,actual_outgoing_memory_restored=True,physical_reconstruction_changed=False)
