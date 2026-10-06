"""Decode observations without treating predictor errors as a full KCL residual."""
import csv,math
from collections import Counter

SIZES=dict(iteration=12,jfet=14,node=8,step=6,trunc=6)


def parse(text):
    records=[]
    for line in text.splitlines():
        if not line.startswith('RFTRACE,'):continue
        r=next(csv.reader([line]));kind=r[1]
        if kind not in SIZES or len(r)!=SIZES[kind]:raise ValueError('trace record shape')
        nonnumeric={'iteration':{7},'jfet':{4},'node':{4},'step':set(),'trunc':set()}[kind]
        values=[float(value) for i,value in enumerate(r) if i>=2 and i not in nonnumeric]
        if not all(math.isfinite(v) for v in values) or float(r[3])<=0:raise ValueError('finite trace and positive attempted step required')
        item=dict(kind=kind,time_s=float(r[2]),step_s=float(r[3]))
        if kind=='iteration':
            item.update(iteration=int(r[4]),mode=int(r[5]),load_noncon=int(r[6]),node=r[7],
                        correction_ratio=float(r[8]),old=float(r[9]),new=float(r[10]),tol=float(r[11]))
            if item['tol']<=0 or item['correction_ratio']<0:raise ValueError('positive correction tolerance required')
            ratio=abs(item['new']-item['old'])/item['tol']
            if not math.isclose(ratio,item['correction_ratio'],rel_tol=1e-12,abs_tol=1e-12):raise ValueError('correction ratio mismatch')
        elif kind=='jfet':
            gt,dt=float(r[8]),float(r[11])
            if gt<=0 or dt<=0:raise ValueError('positive current tolerances required')
            item.update(device=r[4],limiter=int(r[5]),gate_predicted_a=float(r[6]),gate_new_a=float(r[7]),gate_tol_a=gt,
                        drain_predicted_a=float(r[9]),drain_new_a=float(r[10]),drain_tol_a=dt,
                        gate_ratio=abs(float(r[6])-float(r[7]))/gt,drain_ratio=abs(float(r[9])-float(r[10]))/dt,
                        vgs_v=float(r[12]),vgd_v=float(r[13]))
        elif kind=='node':
            item.update(node=r[4],old=float(r[5]),new=float(r[6]),tol=float(r[7]))
            if item['tol']<=0:raise ValueError('positive node tolerance required')
        elif kind=='step':item.update(return_code=int(r[4]),order=int(r[5]))
        elif kind=='trunc':item.update(proposed_step_s=float(r[4]),return_code=int(r[5]))
        records.append(item)
    if not records:raise ValueError('trace is empty')
    return records


def summarize(records):
    iterations=[r for r in records if r['kind']=='iteration'];jfets=[r for r in records if r['kind']=='jfet']
    steps=[r for r in records if r['kind']=='step'];trunc=[r for r in records if r['kind']=='trunc']
    if not iterations or not steps:raise ValueError('solver iteration and return observations required')
    # Trailing records belong to the last attempt, which can reuse the same clock in binary64.
    last=steps[-1];stop=records.index(last);start=max((i for i in range(stop) if records[i]['kind']=='step'),default=-1)+1
    tail=records[start:stop];last_iterations=[r for r in tail if r['kind']=='iteration']
    last_jfets=[r for r in tail if r['kind']=='jfet']
    return dict(record_counts=dict(Counter(r['kind'] for r in records)),
                attempted_steps=len(steps),newton_nonzero_returns=sum(r['return_code']!=0 for r in steps),
                truncation_reductions=sum(r['proposed_step_s']<=.9*r['step_s'] for r in trunc),
                largest_correction=max(iterations,key=lambda r:r['correction_ratio']),last_attempt=last,
                last_attempt_iterations=len(last_iterations),last_attempt_last_iterations=last_iterations[-12:],
                last_attempt_rejected_devices=dict(Counter(r['device'] for r in last_jfets)),
                last_attempt_limiter_events=sum(r['limiter']!=0 for r in last_jfets),
                last_attempt_jfet_tail=last_jfets[-12:],
                observed_rejected_devices=dict(Counter(r['device'] for r in jfets)),
                full_nonlinear_kcl_residual_observed=False)
