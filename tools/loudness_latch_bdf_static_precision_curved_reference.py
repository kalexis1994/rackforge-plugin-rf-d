"""Frozen eighth-support comparison of affine and C7 quadratic references."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
import json,sys
import loudness_latch_curved_reference as curve
import loudness_latch_bdf_static_precision_signed_memory as signed
import numpy as np
import loudness_latch_bdf_static_precision_residual_action as prior
import loudness_latch_bdf_static_precision_post_key_startup as startup_source
import loudness_latch_bdf_static_precision_dc_anchor as constructor
import loudness_latch_bdf_static_precision_key_projection as graph_source
import loudness_latch_directed_prefix as law
from loudness_latch_continuous_descriptor import descriptor
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_curved_reference.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_curved_reference_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_REFERENCIA_CURVA_PROTOCOLO.md'
SOURCE_SELECTION=[1,1]
ADDITIONAL_LIMIT=1
VARIANTS=('affine','c7_bubble')
RADII=prior.prior.RADII
MODE='direct_and_memory'
START_INDEX=7
PATHS=tuple(dict.fromkeys((*signed.PATHS,signed.OUTPUT,signed.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_signed_memory_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_signed_memory_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_signed_memory_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_signed_memory_inputs_validation.json',
    Path(curve.__file__).resolve(),
    ROOT/'evidence/loudness_latch_bdf_static_precision_residual_action_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_residual_action_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_residual_action_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_residual_action_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
read=prior.read
serial=prior.prior.serial


def diagnostic_bound(result):
    if 'peak_node_error_upper_v' not in result:return None
    try:return float(F(result['peak_node_error_upper_v']))
    except OverflowError:return 'outside binary64 display range; exact rational retained'


def support(source,history):
    previous=source['final_certified_result'];law.transfer(previous)
    if source['accepted_intervals_total']!=7 or source['first_gap_index'] is not None or source['primary_trial_mode']!=[1,1] or not previous.get('actual_outgoing_memory_restored'):
        raise ValueError('known seven-interval source with actual restored memories required')
    metric=history['fixed_metric'];left=history['records'][-1]
    if not metric['accepted'] or law.digest(metric)!=source['metric_sha256'] or source['metric_sha256']!=history['metric_sha256'] or left['interval_index']!=6:
        raise ValueError('same accepted metric and seventh physical reference required')
    if F(left['end_s'])!=F(source['end_s']) or F(source['continuous_actual_error_certified_duration_s'])!=F(source['end_s']) or history['groups']!=[list(g) for g in law.fine.GROUPS] or source['weights']!=history['weights'] or source['descriptor_scales']!=history['descriptor_scales']:
        raise ValueError('same clock, norms and partition required')
    return previous,metric,left['prepared']


def generate():
    old_limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
    before=hashes(PATHS);env=environment();source=read(signed.OUTPUT);history=read(signed.prior.prior.OUTPUT);startup=read(startup_source.OUTPUT)
    network=constructor.CompensatedBdfNetwork(200,constructor.model_parameters(1,'finite_transit'))
    graph=read(graph_source.OUTPUT)['graph'];previous,metric,left_prepared=support(source,history)
    certified_end=F(source['end_s']);initial_end=certified_end;records=[];preconditioners=1;rate_queries=0;inverse_count=0;action_count=0
    weights=list(map(F,source['weights']));scales=list(map(F,source['descriptor_scales']))
    basis=law.blocks.directed.basis(metric);balance=law.blocks.balanced.balance(basis)
    interval_index=START_INDEX
    initial=startup_source.unpack(network,startup['rows'][interval_index-1]['history'])
    endpoint=startup_source.unpack(network,startup['rows'][interval_index]['history'])
    affine=law.real.prepare(network,initial,endpoint)
    with localcontext() as ctx:
        ctx.prec=100;hm,_=descriptor(network,graph,[law.real.event.decimal(law.real.poly.evaluate(v,F(1,2))) for v in affine['x']],100)
    candidate_inverse=np.linalg.inv(np.array(hm,dtype=float)).tolist()
    if not np.isfinite(candidate_inverse).all():raise ValueError('finite bubble direction required')
    candidate_rhs=law.action.rhs(network,graph,affine,F(0),F(1))
    curved,bubble=curve.candidate(network,affine,candidate_inverse,candidate_rhs['polynomials'])
    for variant,prepared in zip(VARIANTS,(affine,curved)):
        join=law.real.continuity(network,left_prepared,prepared,certified_end,F(initial.time_s))
        incoming=law.transfer(previous);origin=F(previous['peak_node_error_upper_v']);base=[];compiled=[];rhs=[]
        for k in range(8):
            left,right=F(k,8),F(k+1,8);mid=(left+right)/2;x=[law.real.poly.evaluate(v,mid) for v in prepared['x']]
            with localcontext() as ctx:
                ctx.prec=100;h,_=descriptor(network,graph,[law.real.event.decimal(v) for v in x],100)
            inverse=np.linalg.inv(np.array(h,dtype=float)).tolist()
            if not np.isfinite(inverse).all():raise ValueError('finite candidate preconditioner required')
            preconditioners+=1;constant,terms=law.real.tube.weighted.compile_terms(network,graph,prepared,inverse,scales);compiled.append((constant,terms))
            residual,forcing=law.real.tube.forcing(network,graph,prepared,left,right)
            rhs.append(law.action.rhs(network,graph,prepared,left,right))
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
                    for item,inverse,cover,r in zip(base,inverses,covers,rhs):
                        metrics,rate=law.cell_metrics(inverse,weights,item['forcing_inputs'],metric,basis,balance)
                        rate_queries+=sum(len(v['probes']) for v in rate.values())
                        action=law.action.budgets(item['inverse_binary'],scales,cover['cover'],r,weights,metric)
                        action_count+=len(action['subcells'])
                        original=metrics;metrics=law.action.refine_metrics(original,action,True)
                        cells.append(dict(index=item['index'],inverse_certified=True,forcing_inputs=item['forcing_inputs'],metrics=metrics,original_metrics=original,rate_certificate=rate,action=action))
                    result=law.blocks.close(cells,incoming,radius,origin)
            trials.append(dict(radius_v=str(radius),covers=covers,cells=cells,result=result))
            print(json.dumps(dict(variant=variant,interval=interval_index,start_s=float(F(initial.time_s)),end_s=float(F(endpoint.time_s)),radius_v=float(radius),
                inverse_cells=len(inverses),accepted=result['accepted'],node_bound_v=diagnostic_bound(result),reason=result['reason'])),flush=True)
        selection=law.select(trials)
        record=dict(variant=variant,interval_index=interval_index,start_s=str(F(initial.time_s)),end_s=str(F(endpoint.time_s)),prepared=serial(prepared),interface=join,
            incoming_certified_result_sha256=law.digest(previous),incoming_metric_sha256=law.digest(metric),incoming_node_error_upper_v=str(origin),
            incoming_block_error_upper_v=incoming,base_cells=serial(base),rhs=rhs,trials=trials,selected_trial_index=selection,
            queries=[dict(u=str(u),decimal100=law.real.tube.query(network,graph,prepared,u,100)) for u in (F(0),F(1,2),F(1))])
        records.append(record)
        # Evaluate both references on the same known incoming state; no branch transports into the other.
    selected=next(([i,r['selected_trial_index']] for i,r in enumerate(records) if r['selected_trial_index'] is not None),None)
    if selected is not None:
        previous,certified_end=law.admit(previous,certified_end,records[selected[0]])
    if hashes(PATHS)!=before:raise ValueError('curved reference inputs changed')
    return dict(schema='rf-d/bdf-static-curved-reference/v1',environment=env,source_sha256=before,integer_text_limit_before=old_limit,integer_text_limit_during=0,
        source_primary_trial_mode=source['primary_trial_mode'],source_certified_result_sha256=law.digest(source['final_certified_result']),
        initial_certified_end_s=str(initial_end),start_interval_index=START_INDEX,additional_limit=ADDITIONAL_LIMIT,variant_order=list(VARIANTS),radius_order=list(map(str,RADII)),
        candidate_inverse_binary=candidate_inverse,candidate_rhs=candidate_rhs,bubble=bubble,selected_variant_trial=selected,
        fixed_metric=metric,metric_sha256=law.digest(metric),congruence=basis,balance=balance,weights=source['weights'],descriptor_scales=list(map(str,scales)),
        groups=[list(g) for g in law.fine.GROUPS],records=records,accepted_intervals_total=START_INDEX+int(selected is not None),
        continuous_actual_error_certified_duration_s=str(certified_end),attempted_end_s=str(F(endpoint.time_s)),final_certified_result=previous,first_gap_index=START_INDEX if selected is None else None,
        new_nonlinear_solves=0,new_preconditioners=preconditioners,new_inverse_enclosures=inverse_count,new_metric_systems=0,new_rate_ldlt_queries=rate_queries,new_action_subcell_certificates=action_count,
        small_currents_dropped=False,circuit_regularized=False,independent_remainders_cancelled=False,real_history_only=True,individual_memory_transport=True,
        reference_changed=True,junction_norm_changed=False,clock_translation=False,dc_anchor_reset=False,original_integrator_modified=False,prior_reports_modified=False,numerical_gates_changed=False,
        full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)



def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('records','final_certified_result','fixed_metric','congruence','balance','candidate_inverse_binary','candidate_rhs')}
    summary.update(storage=storage,final_certified_result={k:v for k,v in report['final_certified_result'].items() if k!='propagation'},
        records=[dict(variant=r['variant'],interval_index=r['interval_index'],start_s=r['start_s'],end_s=r['end_s'],selected_trial_index=r['selected_trial_index'],
            trials=[dict(radius_v=t['radius_v'],inverse_certified_cells=sum(c['inverse_certified'] for c in t['covers']),
                result={k:v for k,v in t['result'].items() if k!='propagation'}) for t in r['trials']]) for r in report['records']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
