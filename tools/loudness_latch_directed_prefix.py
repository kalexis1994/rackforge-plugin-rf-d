"""Frozen fourth-certificate source and unchanged 22-coordinate prefix laws."""
from fractions import Fraction as F
import loudness_latch_residual_action as action
prior=action.prior
fine=prior.fine
real=prior.real
blocks=prior.blocks
digest=prior.digest
transfer=prior.transfer
select=prior.select
admit=prior.admit
cell_metrics=prior.cell_metrics


def source(report,history,selection):
    if selection!=[1,1] or report['source_interval_index']!=3 or report['accepted_intervals_total']!=4 or report['first_gap_index'] is not None:
        raise ValueError('known fourth interval and declared secondary [1,1] required')
    if history['groups']!=[list(g) for g in fine.GROUPS]:
        raise ValueError('same 22-coordinate partition required')
    t=report['trials'][1];m=t['modes'][1];metric=history['fixed_metric']
    if F(t['radius_v'])!=F(1,10**6) or m['mode']!='direct_and_memory':
        raise ValueError('same radius and directed memory variant required')
    if not metric['accepted'] or digest(metric)!=history['metric_sha256'] or digest(metric)!=report['fixed_metric_sha256']:
        raise ValueError('same accepted fixed metric identity required')
    if report['weights']!=history['weights'] or report['descriptor_scales']!=history['descriptor_scales']:
        raise ValueError('same coordinate weights and descriptor scales required')
    rec=history['records'][-1]
    if rec['interval_index']!=3 or F(rec['start_s'])!=F(report['start_s']) or F(rec['end_s'])!=F(report['end_s']) or rec['interface']!=report['interface']:
        raise ValueError('same archived fourth reconstruction and clocks required')
    if F(report['continuous_actual_error_certified_duration_s'])!=F(report['end_s']):
        raise ValueError('known certified right endpoint required')
    if report['source_certified_result_sha256']!=rec['incoming_certified_result_sha256'] or report['source_certified_result_sha256']!=digest(history['final_certified_result']):
        raise ValueError('same incoming certified prefix lineage required')
    transfer(m['result'])
    return m['result'],metric
