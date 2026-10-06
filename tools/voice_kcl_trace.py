"""Associate actual linear stamps with L2 solves; reconstruct selected KCL rows."""
import csv,math
from decimal import Decimal,localcontext
import voice_inductor_trace as inductor

FIELDS=('time_s','step_s','iteration','branch','old_current_a','new_current_a',
        'old_98_v','new_98_v','old_17_v','new_17_v','old_16_v','new_16_v',
        'old_3_v','new_3_v','old_49_v','new_49_v','old_7_v','new_7_v','old_1_v','new_1_v')


def pairs(text):
    previous=inductor.pairs(text);result=[];pending={}
    for line in text.splitlines():
        if not line.startswith('RFKTRACE,'):continue
        r=next(csv.reader([line]));kind=r[1]
        if kind in ('res','gm'):
            if len(r)!=6 or kind in pending:raise ValueError('duplicate or malformed coefficient')
            time,step,coeff=map(float,(r[2],r[3],r[5]))
            if not all(math.isfinite(x) for x in (time,step,coeff)) or step<=0 or coeff<=0:raise ValueError('finite positive stamp')
            if r[4]!=('r.xic3.r13' if kind=='res' else 'g.xic3.g4'):raise ValueError('coefficient device')
            pending[kind]=dict(time_s=time,step_s=step,coefficient=coeff)
        elif kind=='solve':
            if len(r)!=len(FIELDS)+2 or set(pending)!= {'res','gm'}:raise ValueError('missing coefficient or solve shape')
            solve={name:float(value) for name,value in zip(FIELDS,r[2:])}
            if not all(math.isfinite(x) for x in solve.values()):raise ValueError('finite solve required')
            for name in ('iteration','branch'):
                if not solve[name].is_integer() or solve[name]<1:raise ValueError('positive integer index')
                solve[name]=int(solve[name])
            if len(result)>=len(previous):raise ValueError('extra KCL solve')
            p=previous[len(result)]
            for name in ('time_s','step_s','iteration','branch','old_current_a','new_current_a'):
                if solve[name]!=p['solve'][name]:raise ValueError('KCL/L2 association: '+name)
            if solve['new_98_v']!=p['solve']['pos_v'] or solve['new_17_v']!=p['solve']['neg_v']:raise ValueError('KCL/L2 terminals')
            for stamp in pending.values():
                if any(stamp[k]!=solve[k] for k in ('time_s','step_s')):raise ValueError('stamp clock association')
            if pending['res']['coefficient']!=float(1/1000) or pending['gm']['coefficient']!=3.1623e-8:raise ValueError('frozen stamp coefficient')
            result.append(dict(inductor=p,solve=solve,conductance_s=pending['res']['coefficient'],
                               transconductance_s=pending['gm']['coefficient'],attempt=p['attempt']))
            pending={}
        else:raise ValueError('invalid KCL record')
    if pending or len(result)!=len(previous):raise ValueError('incomplete KCL observations')
    return result


def evaluate(p):
    s=p['solve'];D=Decimal.from_float
    with localcontext() as ctx:
        ctx.prec=80;g=D(p['conductance_s']);gm=D(p['transconductance_s'])
        req=D(p['inductor']['load']['req_ohm']);out={}
        for stage in ('old','new'):
            V=lambda n:D(s[stage+'_'+str(n)+'_v'])
            current=D(s[stage+'_current_a']);ir=g*(V(17)-V(16));ig=gm*(V(3)-V(49))
            eos_control=V(16)-V(49);eos_out=V(7)-V(1)
            out.update({stage+'_r13_current_a':float(ir),stage+'_g4_current_a':float(ig),
                        stage+'_kcl17_a':float(ir-current),stage+'_kcl16_a':float(-ir-ig),
                        stage+'_eos_row_v':float(eos_out-(D(.001)+eos_control)),
                        stage+'_g4_control_v':float(V(3)-V(49)),stage+'_eos_control_v':float(eos_control),
                        stage+'_eos_output_v':float(eos_out),
                        stage+'_branch_source_mismatch_a':float(current+ig)})
        out.update({f'correction_{n}_v':float(D(s['new_'+str(n)+'_v'])-D(s['old_'+str(n)+'_v'])) for n in (98,17,16,3,49,7,1)})
        for name,positive,negative in (('g4',3,49),('eos_control',16,49),('eos_output',7,1)):
            out[name+'_correction_v']=float((D(s['new_'+str(positive)+'_v'])-D(s['new_'+str(negative)+'_v']))-(D(s['old_'+str(positive)+'_v'])-D(s['old_'+str(negative)+'_v'])))
        out['branch_correction_a']=float(D(s['new_current_a'])-D(s['old_current_a']))
        out['req_times_branch_source_mismatch_v']=float(req*(D(s['new_current_a'])+gm*(D(s['new_3_v'])-D(s['new_49_v']))))
        out['req_gm_times_control_node3_ulp_v']=float(req*gm*D(math.ulp(s['new_3_v'])))
        out['req_gm_times_control_node49_ulp_v']=float(req*gm*D(math.ulp(s['new_49_v'])))
        out['l2_row_residual_v']=inductor.evaluate(p['inductor'])['stamped_row_residual_v']
        return out


def summarize(ps):
    es=[dict(**p,measurements=evaluate(p)) for p in ps]
    tail=[p for p in es if p['attempt']==es[-1]['attempt']]
    keys=('new_kcl17_a','new_kcl16_a','new_eos_row_v','new_branch_source_mismatch_a',
          'correction_17_v','correction_16_v','correction_3_v','correction_7_v','correction_1_v',
          'branch_correction_a','g4_correction_v','eos_control_correction_v','eos_output_correction_v','req_times_branch_source_mismatch_v',
          'req_gm_times_control_node3_ulp_v','req_gm_times_control_node49_ulp_v','l2_row_residual_v')
    def peaks(records):return {k:max(abs(p['measurements'][k]) for p in records) for k in keys}
    return dict(paired_iterations=len(es),final_attempt_iterations=len(tail),
                all_window_absolute_peaks=peaks(es),final_attempt_absolute_peaks=peaks(tail),
                final_attempt_tail=tail[-12:],decimal_precision=80,
                complete_kcl_observed_nodes=[16,17],full_nonlinear_kcl_residual_observed=False)
