"""Pair L2 load/solve records; evaluate its row with exact binary64 inputs."""
import csv,math
from decimal import Decimal,localcontext

LOAD_FIELDS=('time_s','step_s','device','order','mode','branch','inductance_h','flux0_wb',
             'flux1_wb','flux2_wb','a0_per_s','a1_per_s','a2_per_s','stored_voltage_v',
             'req_ohm','veq_v','old_current_a','old_pos_v','old_neg_v')
SOLVE_FIELDS=('time_s','step_s','iteration','branch','old_current_a','new_current_a','pos_v','neg_v')


def decode(line):
    r=next(csv.reader([line]));kind=r[1]
    fields=LOAD_FIELDS if kind=='load' else SOLVE_FIELDS if kind=='solve' else None
    if fields is None or len(r)!=len(fields)+2:raise ValueError('L2 trace record shape')
    result={}
    for name,value in zip(fields,r[2:]):
        if name=='device':result[name]=value;continue
        number=float(value)
        if not math.isfinite(number):raise ValueError('finite L2 trace required')
        if name in ('order','mode','branch','iteration'):
            if not number.is_integer():raise ValueError('integral trace index required')
            number=int(number)
        result[name]=number
    if result['step_s']<=0:raise ValueError('positive attempted step')
    if kind=='load' and (result['order'] not in (1,2) or result['inductance_h']<=0 or result['req_ohm']<=0):raise ValueError('frozen Gear1/2 and positive L/stamp required')
    return kind,result


def pairs(text):
    pending=None;result=[];attempt=0
    for line in text.splitlines():
        if not line.startswith('RFLTRACE,'):continue
        kind,r=decode(line)
        if kind=='load':
            if pending is not None:raise ValueError('unpaired inductor load')
            pending=r
        else:
            if pending is None:raise ValueError('solve without a load')
            for key in ('time_s','step_s','branch','old_current_a'):
                if pending[key]!=r[key]:raise ValueError('load/solve association mismatch: '+key)
            if r['iteration']==1:attempt+=1
            result.append(dict(load=pending,solve=r,attempt=attempt));pending=None
    if pending is not None or not result:raise ValueError('incomplete L2 trace')
    return result


def evaluate(pair):
    load=pair['load'];solve=pair['solve'];D=Decimal.from_float
    with localcontext() as ctx:
        ctx.prec=80
        history=D(load['a1_per_s'])*D(load['flux1_wb'])
        if load['order']==2:history+=D(load['a2_per_s'])*D(load['flux2_wb'])
        voltage=D(solve['pos_v'])-D(solve['neg_v'])
        row=voltage-D(load['req_ohm'])*D(solve['new_current_a'])-D(load['veq_v'])
        # Flux that INDload would publish on its next floating Newton load.
        flux_new=load['inductance_h']*solve['new_current_a']
        discrete=voltage-D(load['a0_per_s'])*D(flux_new)-history
        stamp_error=D(load['veq_v'])-history
        direct=load['a1_per_s']*load['flux1_wb']
        if load['order']==2:direct=load['a2_per_s']*load['flux2_wb']+direct
        target=(voltage-D(load['veq_v']))/D(load['req_ohm'])
        nearest=float(target)
        candidates=(math.nextafter(nearest,-math.inf),nearest,math.nextafter(nearest,math.inf))
        best=min(abs(voltage-D(load['req_ohm'])*D(i)-D(load['veq_v'])) for i in candidates)
        quantum=D(load['req_ohm'])*D(math.ulp(solve['new_current_a']))
        return dict(history_v=str(history),history_stamp_error_v=float(stamp_error),
                    direct_history_rounding_error_v=float(D(direct)-history),direct_history_veq_v=direct,
                    stamped_row_residual_v=float(row),published_flux_row_residual_v=float(discrete),
                    terminal_voltage_v=float(voltage),new_flux_wb=flux_new,
                    branch_current_ulp_a=math.ulp(solve['new_current_a']),
                    stamp_voltage_per_current_ulp_v=float(quantum),best_binary64_row_residual_v=float(best))


def summarize(ps):
    evaluated=[dict(**p,measurements=evaluate(p)) for p in ps]
    tail=[p for p in evaluated if p['attempt']==evaluated[-1]['attempt']]
    keys={(p['load']['order'],p['load']['step_s'],p['load']['a0_per_s'],p['load']['a1_per_s'],
           p['load']['a2_per_s'] if p['load']['order']==2 else 0,
           p['load']['flux1_wb'],p['load']['flux2_wb'] if p['load']['order']==2 else 0) for p in tail}
    if len(keys)!=1:raise ValueError('final attempt changed coefficients or history')
    def peaks(records):
        return {name:max(abs(p['measurements'][name]) for p in records) for name in
                ('history_stamp_error_v','direct_history_rounding_error_v','stamped_row_residual_v','published_flux_row_residual_v',
                 'stamp_voltage_per_current_ulp_v','best_binary64_row_residual_v')}
    values=[p['load']['veq_v'] for p in tail]
    groups={}
    for p in evaluated:
        l=p['load'];key=(p['attempt'],l['order'],l['a0_per_s'],l['a1_per_s'],l['a2_per_s'] if l['order']==2 else 0,
                         l['flux1_wb'],l['flux2_wb'] if l['order']==2 else 0)
        groups.setdefault(key,[]).append(l['veq_v'])
    spans=[max(v)-min(v) for v in groups.values() if len(v)>1]
    return dict(paired_iterations=len(ps),final_attempt_iterations=len(tail),all_window_peaks_v=peaks(evaluated),
                repeated_history_groups=len(spans),varying_history_stamps=sum(x!=0 for x in spans),
                max_same_history_stamp_span_v=max(spans,default=0),
                final_attempt_peaks_v=peaks(tail),final_history_constant=True,
                final_stamp_distinct_values=len(set(values)),final_stamp_span_v=max(values)-min(values),
                final_flux_distinct_values=len({p['load']['flux0_wb'] for p in tail}),
                final_direct_history_distinct_values=len({p['measurements']['direct_history_veq_v'] for p in tail}),
                final_attempt_tail=tail[-12:],decimal_precision=80,full_nonlinear_kcl_residual_observed=False)
