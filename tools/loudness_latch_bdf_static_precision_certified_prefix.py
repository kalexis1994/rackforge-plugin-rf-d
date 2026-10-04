"""Bounded contiguous extension from the certified startup interval."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
import json
import numpy as np
import loudness_latch_bdf_static_precision_startup_blocks as prior
import loudness_latch_certified_prefix as law
from loudness_latch_continuous_descriptor import descriptor
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_PREFIJO_CERTIFICADO_PROTOCOLO.md'
ADDITIONAL_LIMIT=8
RADII=prior.prior.RADII
MODES=('retained_quadratic','new_quadratic')
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_blocks_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_blocks_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_blocks_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_blocks_inputs_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_certified_prefix_launch_attempt.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
read=prior.read

def serial(value):
    if isinstance(value,F):return str(value)
    if isinstance(value,dict):return {k:serial(v) for k,v in value.items() if k!='junctions'}
    if isinstance(value,(tuple,list)):return [serial(v) for v in value]
    return value

def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);first=read(prior.prior.OUTPUT);startup=read(prior.prior.prior.OUTPUT)
    constructor=prior.prior.prior.prior.prior.prior
    network=constructor.CompensatedBdfNetwork(200,constructor.model_parameters(1,'finite_transit'))
    g=read(prior.prior.prior.prior.prior.OUTPUT)['graph']
    chosen=source['primary_trial_mode']
    if chosen is None:raise ValueError('certified first interval required')
    oldtrial=source['trials'][chosen[0]];oldmode=oldtrial['modes'][chosen[1]];previous=oldmode['result'];metric=oldtrial['metric']
    if not previous['accepted'] or not previous['actual_dae_error_bound']:raise ValueError('actual first interval proof required')
    previous_prepared=first['prepared'];certified_end=F(source['duration_s']);records=[];new_preconditioners=0;metric_systems=0;accepted_extra=0
    weights=list(map(F,source['weights']));scales=list(map(F,first['descriptor_scales']))
    for interval_index in range(1,ADDITIONAL_LIMIT+1):
        initial=prior.prior.prior.unpack(network,startup['rows'][interval_index-1]['history']);endpoint=prior.prior.prior.unpack(network,startup['rows'][interval_index]['history'])
        prepared=law.prepare(network,initial,endpoint)
        if F(initial.time_s)!=certified_end:raise ValueError('proof lineage gap')
        join=law.continuity(network,previous_prepared,prepared,certified_end,F(initial.time_s));base=[];compiled=[]
        for k in range(8):
            left,right=F(k,8),F(k+1,8);mid=(left+right)/2;x=[law.poly.evaluate(v,mid) for v in prepared['x']]
            with localcontext() as ctx:
                ctx.prec=100;h,_=descriptor(network,g,[law.event.decimal(v) for v in x],100)
            inverse=np.linalg.inv(np.array(h,dtype=float)).tolist()
            if not np.isfinite(inverse).all():raise ValueError('finite candidate preconditioner required')
            new_preconditioners+=1;constant,terms=law.tube.weighted.compile_terms(network,g,prepared,inverse,scales);compiled.append((constant,terms))
            residual,forcing=law.tube.forcing(network,g,prepared,left,right)
            base.append(dict(index=k,left=str(left),right=str(right),inverse_binary=inverse,descriptor_binary_sha256=law.event.dc.digest(np.array(h,dtype=float).tolist()),residual_bounds=residual,forcing_inputs=forcing))
        trials=[];origin=F(previous['peak_node_error_upper_v']);gains=law.tube.gains(network,g)
        for radius in RADII:
            if origin>=radius:
                trials.append(dict(radius_v=str(radius),covers=[],new_metric=None,modes=[dict(mode=mode,cells=[],bridge=None,initial_block_error_upper_v=None,
                    result=dict(accepted=False,reason='incoming nodal bound not strictly inside candidate tube',actual_dae_error_bound=False)) for mode in MODES]));continue
            covers=[];inverses=[]
            for item,(constant,terms) in zip(base,compiled):
                cover=law.tube.inflated_cover(constant,terms,gains,F(item['left']),F(item['right']),radius);row=dict(index=item['index'],cover=cover,inverse_certified=cover['strict_contraction'])
                if row['inverse_certified']:
                    inverse,cert=law.tube.cells.structured_inverse(item['inverse_binary'],scales,cover,F(cover['contraction_upper']));row['inverse_certificate']=cert
                    row['inverse_intervals_sha256']=law.event.dc.digest(law.tube.cells.packed_matrix(inverse));inverses.append(inverse)
                covers.append(row)
            if len(inverses)!=8:
                trials.append(dict(radius_v=str(radius),covers=covers,new_metric=None,modes=[dict(mode=mode,cells=[],bridge=None,initial_block_error_upper_v=None,
                    result=dict(accepted=False,reason='mean descriptor cover rejected',actual_dae_error_bound=False)) for mode in MODES]));continue
            candidate=law.blocks.quadratic.candidate([law.blocks.generator(v,weights) for v in inverses]);metric_systems+=1;modes=[]
            for mode,m in zip(MODES,(metric,candidate)):
                if not m['accepted']:
                    modes.append(dict(mode=mode,cells=[],bridge=None,initial_block_error_upper_v=None,result=dict(accepted=False,reason=m['rejection'],actual_dae_error_bound=False)));continue
                bridge=law.bridge(metric,m);incoming=law.transfer(previous,bridge);basis=law.blocks.directed.basis(m);balance=law.blocks.balanced.balance(basis);rows=[]
                for item,inverse in zip(base,inverses):
                    metrics,rate=law.blocks.cell_metrics(inverse,weights,item['forcing_inputs'],'quadratic_balanced',m,basis,balance)
                    rows.append(dict(index=item['index'],inverse_certified=True,forcing_inputs=item['forcing_inputs'],metrics=metrics,rate_certificate=rate))
                result=law.blocks.close(rows,incoming,radius,origin)
                modes.append(dict(mode=mode,metric=m,congruence=basis,balance=balance,bridge=bridge,initial_block_error_upper_v=incoming,cells=rows,result=result))
                print(json.dumps(dict(interval=interval_index,radius_v=float(radius),mode=mode,accepted=result['accepted'],node_bound_v=float(F(result['peak_node_error_upper_v'])) if 'peak_node_error_upper_v' in result else None,reason=result['reason'])),flush=True)
            trials.append(dict(radius_v=str(radius),covers=covers,new_metric=candidate,modes=modes))
        selected=next(([i,j] for i,t in enumerate(trials) for j,m in enumerate(t['modes']) if m['result']['accepted']),None)
        queries=[dict(u=str(u),decimal100=law.tube.query(network,g,prepared,u,100)) for u in (F(0),F(1,2),F(1))]
        record=dict(interval_index=interval_index,start_s=str(F(initial.time_s)),end_s=str(F(endpoint.time_s)),prepared=serial(prepared),interface=join,
            incoming_certified_result_sha256=law.event.dc.digest(previous),incoming_metric_sha256=law.event.dc.digest(metric),incoming_node_error_upper_v=str(origin),base_cells=serial(base),trials=trials,selected_trial_mode=selected,queries=queries)
        records.append(record)
        if selected is None:break
        chosenmode=trials[selected[0]]['modes'][selected[1]];previous=chosenmode['result'];metric=chosenmode['metric'];previous_prepared=prepared;certified_end=F(endpoint.time_s);accepted_extra+=1
    if hashes(PATHS)!=before:raise ValueError('prefix inputs changed')
    return dict(schema='rf-d/bdf-static-certified-prefix/v1',environment=env,source_sha256=before,first_interval_selection=chosen,additional_limit=ADDITIONAL_LIMIT,
        radius_order=list(map(str,RADII)),mode_order=list(MODES),weights=source['weights'],descriptor_scales=first['descriptor_scales'],records=records,
        accepted_additional_intervals=accepted_extra,accepted_intervals_total=1+accepted_extra,attempted_additional_intervals=len(records),
        continuous_actual_error_certified_duration_s=str(certified_end),attempted_end_s=records[-1]['end_s'],
        final_certified_result=previous,final_certified_metric=metric,new_nonlinear_solves=0,new_preconditioners=new_preconditioners,metric_systems_attempted=metric_systems,
        first_gap_index=records[-1]['interval_index'] if records[-1]['selected_trial_mode'] is None else None,
        real_history_only=True,clock_translation=False,dc_anchor_reset=False,metric_bridges_paid=True,original_integrator_modified=False,prior_reports_modified=False,numerical_gates_changed=False,
        full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('records','final_certified_result','final_certified_metric')}
    summary.update(storage=storage,records=[dict(interval_index=r['interval_index'],start_s=r['start_s'],end_s=r['end_s'],selected_trial_mode=r['selected_trial_mode'],
        trials=[dict(radius_v=t['radius_v'],inverse_certified_cells=sum(c['inverse_certified'] for c in t['covers']),
            modes=[dict(mode=m['mode'],result={k:v for k,v in m['result'].items() if k!='propagation'}) for m in t['modes']]) for t in r['trials']]) for r in report['records']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
