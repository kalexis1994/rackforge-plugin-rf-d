"""Certified 22-coordinate transport and ordered contiguous admission, offline only."""
from fractions import Fraction as F
import loudness_latch_coordinate_memory as fine
import loudness_latch_certified_prefix as real
blocks=real.blocks
digest=real.event.dc.digest


def transfer(previous):
    if not previous['accepted'] or not previous['actual_dae_error_bound']:
        raise ValueError('actual preceding interval certificate required')
    p=previous['propagation'];a=list(map(F,p['endpoint_anchor_v']));b=list(map(F,p['endpoint_forced_v']))
    if len(a)!=22 or len(b)!=22 or min(a+b)<0:
        raise ValueError('22 nonnegative outgoing errors in unchanged norms required')
    return list(map(str,[x+y for x,y in zip(a,b)]))


def source(report,selection):
    if report['groups']!=[list(g) for g in fine.GROUPS] or selection!=[1,1]:
        raise ValueError('frozen refined secondary source [1,1] required')
    trial=report['trials'][selection[0]];mode=trial['modes'][selection[1]]
    if F(trial['radius_v'])!=F(1,10**6) or mode['mode']!='refined_anchor':
        raise ValueError('identified radius and source mode required')
    metric=report['fixed_metric']
    if not metric['accepted'] or digest(metric)!=report['metric_sha256']:
        raise ValueError('same accepted metric identity required')
    transfer(mode['result'])
    return mode['result'],metric


def select(trials):
    for i,t in enumerate(trials):
        if t['result']['accepted']:
            if not t['result']['actual_dae_error_bound']:
                raise ValueError('accepted conditional result cannot extend actual prefix')
            return i
    return None


def admit(previous,certified_end,record):
    transfer(previous)
    if F(record['start_s'])!=F(certified_end) or F(record['end_s'])<=F(certified_end):
        raise ValueError('contiguous increasing certified clocks required')
    if record['incoming_certified_result_sha256']!=digest(previous):
        raise ValueError('incoming actual certificate identity differs')
    if not all(record['interface'][k] for k in ('potential_continuity','linear_memory_continuity','constitutive_memory_continuity')) or record['interface']['charge_reset']:
        raise ValueError('same reconstructed interface without reset required')
    choice=select(record['trials'])
    if choice!=record['selected_trial_index']:
        raise ValueError('ordered selection differs')
    if choice is None:return None
    result=record['trials'][choice]['result'];transfer(result)
    return result,F(record['end_s'])


def cell_metrics(inverse,weights,forcing,metric,basis,balance):
    generator=blocks.generator(inverse,weights)
    iso=blocks.quadratic.rate(metric,generator)
    direct=blocks.directed.rate(metric,generator,iso,basis)
    balanced=blocks.balanced.rate(basis,direct,balance)
    rates=dict(isotropic=iso,directed=direct,balanced=balanced)
    metrics=fine.fine_metrics(inverse,weights,forcing,metric,balanced['mu_metric_upper_per_s'])
    return metrics,rates
