"""Bounded real-clock extension using known fine outgoing errors and fixed P."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
import json
import numpy as np
import loudness_latch_bdf_static_precision_coordinate_memory as prior
import loudness_latch_bdf_static_precision_post_key_startup as startup_source
import loudness_latch_bdf_static_precision_dc_anchor as constructor
import loudness_latch_bdf_static_precision_key_projection as graph_source
import loudness_latch_fine_prefix as law
from loudness_latch_continuous_descriptor import descriptor
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_PREFIJO_22_PROTOCOLO.md'
SOURCE_SELECTION=[1,1]
ADDITIONAL_LIMIT=8
RADII=prior.startup_tube.RADII
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_coordinate_memory_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_coordinate_memory_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_coordinate_memory_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_coordinate_memory_inputs_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_fine_prefix_measurement_attempt.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
read=prior.read
serial=prior.prior.serial


def diagnostic_bound(result):
    if 'peak_node_error_upper_v' not in result:return None
    try:return float(F(result['peak_node_error_upper_v']))
    except OverflowError:return 'outside binary64 display range; exact rational retained'


def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);startup=read(startup_source.OUTPUT)
    network=constructor.CompensatedBdfNetwork(200,constructor.model_parameters(1,'finite_transit'))
    graph=read(graph_source.OUTPUT)['graph'];previous,metric=law.source(source,SOURCE_SELECTION)
    left_prepared=read(prior.prior.OUTPUT)['records'][0]['prepared']
    certified_end=F(source['second_end_s']);initial_end=certified_end;records=[];accepted=0;preconditioners=0;rate_queries=0;inverse_count=0
    weights=list(map(F,source['weights']));scales=list(map(F,read(prior.startup_tube.OUTPUT)['descriptor_scales']))
    basis=law.blocks.directed.basis(metric);balance=law.blocks.balanced.balance(basis)
    for interval_index in range(2,2+ADDITIONAL_LIMIT):
        initial=startup_source.unpack(network,startup['rows'][interval_index-1]['history'])
        endpoint=startup_source.unpack(network,startup['rows'][interval_index]['history'])
        prepared=law.real.prepare(network,initial,endpoint)
        join=law.real.continuity(network,left_prepared,prepared,certified_end,F(initial.time_s))
        incoming=law.transfer(previous);origin=F(previous['peak_node_error_upper_v']);base=[];compiled=[]
        for k in range(8):
            left,right=F(k,8),F(k+1,8);mid=(left+right)/2;x=[law.real.poly.evaluate(v,mid) for v in prepared['x']]
            with localcontext() as ctx:
                ctx.prec=100;h,_=descriptor(network,graph,[law.real.event.decimal(v) for v in x],100)
            inverse=np.linalg.inv(np.array(h,dtype=float)).tolist()
            if not np.isfinite(inverse).all():raise ValueError('finite candidate preconditioner required')
            preconditioners+=1;constant,terms=law.real.tube.weighted.compile_terms(network,graph,prepared,inverse,scales);compiled.append((constant,terms))
            residual,forcing=law.real.tube.forcing(network,graph,prepared,left,right)
            base.append(dict(index=k,left=str(left),right=str(right),inverse_binary=inverse,
                descriptor_binary_sha256=law.digest(np.array(h,dtype=float).tolist()),residual_bounds=residual,forcing_inputs=forcing))
        trials=[];gains=law.real.tube.gains(network,graph)
        for radius in RADII:
            covers=[];inverses=[];cells=[]
            if origin>=radius:
                result=dict(accepted=False,reason='incoming nodal bound not strictly inside candidate tube',actual_dae_error_bound=False)
            else:
                for item,(constant,terms) in zip(base,compiled):
                    cover=law.real.tube.inflated_cover(constant,terms,gains,F(item['left']),F(item['right']),radius)
                    row=dict(index=item['index'],cover=cover,inverse_certified=cover['strict_contraction'])
                    if row['inverse_certified']:
                        inverse,cert=law.real.tube.cells.structured_inverse(item['inverse_binary'],scales,cover,F(cover['contraction_upper']))
                        row.update(inverse_certificate=cert,inverse_intervals_sha256=law.digest(law.real.tube.cells.packed_matrix(inverse)))
                        inverses.append(inverse);inverse_count+=1
                    covers.append(row)
                if len(inverses)!=8:
                    result=dict(accepted=False,reason='mean descriptor cover rejected',actual_dae_error_bound=False)
                else:
                    for item,inverse in zip(base,inverses):
                        metrics,rate=law.cell_metrics(inverse,weights,item['forcing_inputs'],metric,basis,balance)
                        rate_queries+=sum(len(v['probes']) for v in rate.values())
                        cells.append(dict(index=item['index'],inverse_certified=True,forcing_inputs=item['forcing_inputs'],metrics=metrics,rate_certificate=rate))
                    result=law.blocks.close(cells,incoming,radius,origin)
            trials.append(dict(radius_v=str(radius),covers=covers,cells=cells,result=result))
            print(json.dumps(dict(interval=interval_index,start_s=float(F(initial.time_s)),end_s=float(F(endpoint.time_s)),radius_v=float(radius),
                inverse_cells=len(inverses),accepted=result['accepted'],node_bound_v=diagnostic_bound(result),reason=result['reason'])),flush=True)
        selection=law.select(trials)
        record=dict(interval_index=interval_index,start_s=str(F(initial.time_s)),end_s=str(F(endpoint.time_s)),prepared=serial(prepared),interface=join,
            incoming_certified_result_sha256=law.digest(previous),incoming_metric_sha256=law.digest(metric),incoming_node_error_upper_v=str(origin),
            incoming_block_error_upper_v=incoming,base_cells=serial(base),trials=trials,selected_trial_index=selection,
            queries=[dict(u=str(u),decimal100=law.real.tube.query(network,graph,prepared,u,100)) for u in (F(0),F(1,2),F(1))])
        records.append(record);admitted=law.admit(previous,certified_end,record)
        if admitted is None:break
        previous,certified_end=admitted;left_prepared=prepared;accepted+=1
    if hashes(PATHS)!=before:raise ValueError('fine prefix inputs changed')
    return dict(schema='rf-d/bdf-static-fine-prefix/v1',environment=env,source_sha256=before,source_trial_mode=SOURCE_SELECTION,
        source_primary_trial_mode=source['primary_trial_mode'],source_certified_result_sha256=law.digest(law.source(source,SOURCE_SELECTION)[0]),
        initial_certified_end_s=str(initial_end),additional_limit=ADDITIONAL_LIMIT,radius_order=list(map(str,RADII)),
        fixed_metric=metric,metric_sha256=law.digest(metric),congruence=basis,balance=balance,weights=source['weights'],descriptor_scales=list(map(str,scales)),
        groups=[list(g) for g in law.fine.GROUPS],records=records,accepted_additional_intervals=accepted,accepted_intervals_total=2+accepted,
        attempted_additional_intervals=len(records),continuous_actual_error_certified_duration_s=str(certified_end),attempted_end_s=records[-1]['end_s'],
        final_certified_result=previous,first_gap_index=records[-1]['interval_index'] if records[-1]['selected_trial_index'] is None else None,
        new_nonlinear_solves=0,new_preconditioners=preconditioners,new_inverse_enclosures=inverse_count,new_metric_systems=0,new_rate_ldlt_queries=rate_queries,
        real_history_only=True,individual_memory_transport=True,junction_norm_changed=False,clock_translation=False,dc_anchor_reset=False,
        original_integrator_modified=False,prior_reports_modified=False,numerical_gates_changed=False,source_primary_selection_rewritten=False,
        full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('records','final_certified_result','fixed_metric','congruence','balance')}
    summary.update(storage=storage,final_certified_result={k:v for k,v in report['final_certified_result'].items() if k!='propagation'},
        records=[dict(interval_index=r['interval_index'],start_s=r['start_s'],end_s=r['end_s'],selected_trial_index=r['selected_trial_index'],
            trials=[dict(radius_v=t['radius_v'],inverse_certified_cells=sum(c['inverse_certified'] for c in t['covers']),
                result={k:v for k,v in t['result'].items() if k!='propagation'}) for t in r['trials']]) for r in report['records']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
