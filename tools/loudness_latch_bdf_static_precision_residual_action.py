"""Frozen directed RHS actions over the archived fourth-interval mean covers."""
from pathlib import Path
from fractions import Fraction as F
import json
import loudness_latch_bdf_static_precision_fine_prefix as prior
import loudness_latch_residual_action as law
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_residual_action.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_residual_action_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_ACCION_RESIDUAL_PROTOCOLO.md'
MODES=('direct_only','direct_and_memory')
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
read=prior.read


def support(report):
    previous=report['final_certified_result'];law.prior.transfer(previous);rec=report['records'][-1]
    if report['accepted_intervals_total']!=3 or rec['interval_index']!=3 or report['first_gap_index']!=3 or rec['selected_trial_index'] is not None:
        raise ValueError('frozen fourth-interval gap and known preceding prefix required')
    if F(rec['start_s'])!=F(report['continuous_actual_error_certified_duration_s']) or law.prior.digest(previous)!=rec['incoming_certified_result_sha256']:
        raise ValueError('same certified incoming clock and result required')
    return previous,rec


def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);previous,rec=support(source)
    network=prior.constructor.CompensatedBdfNetwork(200,prior.constructor.model_parameters(1,'finite_transit'))
    startup=read(prior.startup_source.OUTPUT);graph=read(prior.graph_source.OUTPUT)['graph'];k=rec['interval_index']
    a=prior.startup_source.unpack(network,startup['rows'][k-1]['history']);b=prior.startup_source.unpack(network,startup['rows'][k]['history'])
    prepared=law.prior.real.prepare(network,a,b)
    if prior.serial(prepared)!=rec['prepared']:raise ValueError('same real reconstruction required')
    metric=source['fixed_metric'];weights=source['weights'];scales=list(map(F,source['descriptor_scales']));incoming=law.prior.transfer(previous)
    rhs=[law.rhs(network,graph,prepared,F(base['left']),F(base['right'])) for base in rec['base_cells']]
    trials=[];reused=0
    for trial in rec['trials']:
        radius=F(trial['radius_v']);cells=[]
        if not trial['cells']:
            trials.append(dict(radius_v=trial['radius_v'],cells=[],modes=[dict(mode=m,result=trial['result']) for m in MODES]));continue
        for base,cover,old,r in zip(rec['base_cells'],trial['covers'],trial['cells'],rhs):
            inverse,digest=prior.prior.inverse(base,cover,scales)
            if digest!=cover['inverse_intervals_sha256']:raise ValueError('same archived inverse required')
            action=law.budgets(base['inverse_binary'],scales,cover['cover'],r,weights,metric);reused+=1
            cells.append(dict(index=base['index'],inverse_intervals_sha256=digest,source_cover_sha256=law.prior.digest(cover),
                source_rate_sha256=law.prior.digest(old['rate_certificate']),action=action))
        modes=[]
        for mode in MODES:
            rows=[dict(index=old['index'],inverse_certified=True,forcing_inputs=old['forcing_inputs'],
                metrics=law.refine_metrics(old['metrics'],new['action'],mode=='direct_and_memory')) for old,new in zip(trial['cells'],cells)]
            result=law.prior.blocks.close(rows,incoming,radius,F(previous['peak_node_error_upper_v']))
            modes.append(dict(mode=mode,cells=rows,result=result))
            print(json.dumps(dict(interval=k,radius_v=float(radius),mode=mode,accepted=result['accepted'],node_bound_v=prior.diagnostic_bound(result),reason=result['reason'])),flush=True)
        trials.append(dict(radius_v=trial['radius_v'],cells=cells,modes=modes,original_result=trial['result']))
    selected=next(([i,j] for i,t in enumerate(trials) for j,m in enumerate(t['modes']) if m['result']['accepted']),None)
    final=previous if selected is None else trials[selected[0]]['modes'][selected[1]]['result']
    if hashes(PATHS)!=before:raise ValueError('residual action inputs changed')
    return dict(schema='rf-d/bdf-static-residual-action/v1',environment=env,source_sha256=before,source_interval_index=k,
        source_certified_result_sha256=law.prior.digest(previous),incoming_block_error_upper_v=incoming,incoming_node_error_upper_v=previous['peak_node_error_upper_v'],
        start_s=rec['start_s'],end_s=rec['end_s'],interface=rec['interface'],fixed_metric_sha256=source['metric_sha256'],weights=weights,descriptor_scales=source['descriptor_scales'],
        rhs=rhs,trials=trials,mode_order=list(MODES),radius_order=source['radius_order'],primary_trial_mode=selected,
        accepted_intervals_total=4 if selected is not None else 3,continuous_actual_error_certified_duration_s=rec['end_s'] if selected is not None else rec['start_s'],
        fourth_interval_nonlinear_error_proven=selected is not None,first_gap_index=3 if selected is None else None,final_certified_result=final,
        reused_inverse_enclosures=reused,reused_rate_certificates=reused,action_subcell_certificates=reused*law.SUBCELLS,
        new_nonlinear_solves=0,new_preconditioners=0,new_metric_systems=0,new_rate_ldlt_queries=0,
        trajectory_changed=False,junction_norm_changed=False,dc_anchor_reset=False,original_integrator_modified=False,prior_reports_modified=False,
        numerical_gates_changed=False,small_currents_dropped=False,circuit_regularized=False,independent_remainders_cancelled=False,
        full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('rhs','trials','final_certified_result')}
    summary.update(storage=storage,final_certified_result={k:v for k,v in report['final_certified_result'].items() if k!='propagation'},
        trials=[dict(radius_v=t['radius_v'],modes=[dict(mode=m['mode'],result={k:v for k,v in m['result'].items() if k!='propagation'}) for m in t['modes']]) for t in report['trials']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
