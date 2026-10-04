"""Frozen outgoing coordinate refinement and second-interval fine comparison."""
from pathlib import Path
from fractions import Fraction as F
import json
import loudness_latch_bdf_static_precision_certified_prefix as prior
import loudness_latch_bdf_static_precision_startup_blocks as startup_blocks
import loudness_latch_bdf_static_precision_startup_tube as startup_tube
import loudness_latch_coordinate_memory as law
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_coordinate_memory.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_coordinate_memory_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_MEMORIA_COORDENADA_PROTOCOLO.md'
MODES=('coarse_anchor','refined_anchor')
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
read=prior.read

def inverse(base,row,scales):
    if not row['inverse_certified']:raise ValueError('certified mean inverse required')
    x,cert=prior.law.tube.cells.structured_inverse(base['inverse_binary'],scales,row['cover'],F(row['cover']['contraction_upper']))
    if cert!=row['inverse_certificate']:raise ValueError('reused inverse certificate differs')
    return x,prior.law.event.dc.digest(prior.law.tube.cells.packed_matrix(x))

def generate():
    before=hashes(PATHS);env=environment();first=read(startup_blocks.OUTPUT);tube=read(startup_tube.OUTPUT);prefix=read(prior.OUTPUT)
    selection=first['primary_trial_mode']
    if selection is None:raise ValueError('first actual interval certificate required')
    chosen=first['trials'][selection[0]];old=chosen['modes'][selection[1]];metric=chosen['metric'];previous=old['result']
    if not previous['accepted'] or not previous['actual_dae_error_bound']:raise ValueError('known first interval required')
    weights=list(map(F,first['weights']));scales=list(map(F,tube['descriptor_scales']));first_cells=[];reused=0
    for base,cover,row in zip(tube['base_cells'],tube['trials'][selection[0]]['cells'],old['cells']):
        x,digest=inverse(base,cover,scales);reused+=1;mu=row['rate_certificate']['balanced']['mu_metric_upper_per_s']
        first_cells.append(dict(index=base['index'],forcing_inputs=base['forcing_inputs'],metrics=law.fine_metrics(x,weights,base['forcing_inputs'],metric,mu),
            inverse_intervals_sha256=digest,source_rate_sha256=prior.law.event.dc.digest(row['rate_certificate'])))
    initial=[row['weighted_error_upper_v'] for row in first['initial_memory']['rows'][:21]]
    refinement=law.refine(initial,previous,first_cells);rec=prefix['records'][0]
    if rec['interval_index']!=1 or rec['incoming_certified_result_sha256']!=prior.law.event.dc.digest(previous):raise ValueError('same second-interval source and first certificate required')
    trials=[];origin=F(previous['peak_node_error_upper_v'])
    for t in rec['trials']:
        radius=F(t['radius_v'])
        if origin>=radius:
            trials.append(dict(radius_v=t['radius_v'],cells=[],modes=[dict(mode=m,initial_block_error_upper_v=None,result=dict(accepted=False,reason='incoming nodal bound not strictly inside candidate tube',actual_dae_error_bound=False)) for m in MODES]));continue
        retained=next(m for m in t['modes'] if m['mode']=='retained_quadratic')
        if retained.get('metric')!=metric or not retained['bridge']['identical_norm']:raise ValueError('fixed metric retained without conversion required')
        cells=[]
        for base,cover,row in zip(rec['base_cells'],t['covers'],retained['cells']):
            x,digest=inverse(base,cover,scales);reused+=1
            if digest!=cover['inverse_intervals_sha256']:raise ValueError('second inverse identity mismatch')
            mu=row['rate_certificate']['balanced']['mu_metric_upper_per_s']
            cells.append(dict(index=base['index'],inverse_certified=True,forcing_inputs=base['forcing_inputs'],metrics=law.fine_metrics(x,weights,base['forcing_inputs'],metric,mu),
                inverse_intervals_sha256=digest,source_rate_sha256=prior.law.event.dc.digest(row['rate_certificate'])))
        modes=[]
        for mode,incoming in zip(MODES,(refinement['coarse_outgoing_v'],refinement['refined_outgoing_v'])):
            result=law.prior.close(cells,incoming,radius,origin);modes.append(dict(mode=mode,initial_block_error_upper_v=incoming,result=result))
            print(json.dumps(dict(radius_v=float(radius),mode=mode,accepted=result['accepted'],node_bound_v=float(F(result['peak_node_error_upper_v'])) if 'peak_node_error_upper_v' in result else None,reason=result['reason'])),flush=True)
        trials.append(dict(radius_v=t['radius_v'],cells=cells,modes=modes,prior_six_group_result=retained['result']))
    chosen=next(([i,j] for i,t in enumerate(trials) for j,m in enumerate(t['modes']) if m['result']['accepted']),None)
    if hashes(PATHS)!=before:raise ValueError('coordinate memory inputs changed')
    return dict(schema='rf-d/bdf-static-coordinate-memory/v1',environment=env,source_sha256=before,
        first_interval_selection=selection,fixed_metric=metric,metric_sha256=prior.law.event.dc.digest(metric),weights=first['weights'],groups=[list(g) for g in law.GROUPS],
        first_cells=first_cells,refinement=refinement,second_interface=rec['interface'],second_start_s=rec['start_s'],second_end_s=rec['end_s'],trials=trials,mode_order=list(MODES),primary_trial_mode=chosen,
        outgoing_memory_refinement_proven=True,second_interval_nonlinear_error_proven=chosen is not None,
        accepted_intervals_total=2 if chosen else 1,continuous_actual_error_certified_duration_s=rec['end_s'] if chosen else first['duration_s'],
        first_gap_index=None if chosen else 1,reused_inverse_enclosures=reused,new_nonlinear_solves=0,new_preconditioners=0,new_metric_systems=0,new_rate_ldlt_queries=0,
        reconstruction_changed=False,junction_norm_changed=False,dc_anchor_reset=False,original_integrator_modified=False,prior_reports_modified=False,numerical_gates_changed=False,
        full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('first_cells','refinement','trials','fixed_metric')}
    summary.update(storage=storage,refinement={k:v for k,v in report['refinement'].items() if k!='trace'},trials=[dict(radius_v=t['radius_v'],
        modes=[dict(mode=m['mode'],result={k:v for k,v in m['result'].items() if k!='propagation'}) for m in t['modes']]) for t in report['trials']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
