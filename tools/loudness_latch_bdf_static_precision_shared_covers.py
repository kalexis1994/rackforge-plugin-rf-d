"""Predeclared shared mean-descriptor covers over eight immutable references."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
from dataclasses import asdict,is_dataclass
import json,sys
import numpy as np
import loudness_latch_bdf_static_precision_curved_prefix as prior
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
ROOT=prior.ROOT;law=prior.law;serial=prior.serial;read=prior.read
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_shared_covers.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_shared_covers_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_RECINTOS_COMPARTIDOS_PROTOCOLO.md'
WIDTHS=(8,4,2,1)
RADII=prior.RADII
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    *(prior.interval_output(k) for k in range(8,16)),
    *(ROOT/'evidence'/name for name in (
        'loudness_latch_bdf_static_precision_curved_prefix_validation.json',
        'loudness_latch_bdf_static_precision_curved_prefix_inputs.json.gz',
        'loudness_latch_bdf_static_precision_curved_prefix_inputs_summary.json',
        'loudness_latch_bdf_static_precision_curved_prefix_inputs_validation.json')),
    Path(__file__).resolve(),PROTOCOL)))


def references(network,startup,manifest):
    if manifest['accepted_intervals_total']!=16 or manifest['first_gap_index'] is not None or [r['interval_index'] for r in manifest['records']]!=list(range(8,16)):
        raise ValueError('complete sixteen-support control required')
    out=[]
    for row in manifest['records']:
        record=prior.load_record(row);k=record['interval_index']
        a,b=[prior.startup_source.unpack(network,startup['rows'][j]['history']) for j in (k-1,k)]
        affine=law.real.prepare(network,a,b)
        prepared,bubble=prior.curve.candidate(network,affine,record['candidate_inverse_binary'],record['candidate_rhs']['polynomials'])
        if serial(prepared)!=record['prepared'] or bubble!=record['bubble']:
            raise ValueError('unchanged archived curved reference required')
        out.append(dict(interval_index=k,start_s=record['start_s'],end_s=record['end_s'],prepared=prepared,
            prepared_sha256=law.digest(record['prepared']),rhs=record['rhs'],
            forcing=[b['forcing_inputs'] for b in record['base_cells']],source_storage=row['storage']))
    return out


def analytic_identity(constant,terms):
    return law.digest(serial(dict(constant=constant,terms=[{k:asdict(v) if is_dataclass(v) else v for k,v in t.items() if k!='power'} for t in terms])))


def merge_terms(compiled):
    """Affine powers below encode scalar ranges only, never a physical reference."""
    if not compiled:raise ValueError('nonempty identified references required')
    constant,first=compiled[0];identity=analytic_identity(constant,first);ledger=[]
    for c,terms in compiled:
        if analytic_identity(c,terms)!=identity:raise ValueError('same constant and analytic stamps for fixed X required')
        ledger.append([dict(ref=t['ref'],kind=t['kind'],lower=str(min(law.real.poly.bernstein(t['power'],F(0),F(1)))),
            upper=str(max(law.real.poly.bernstein(t['power'],F(0),F(1))))) for t in terms])
    merged=[]
    for j,t in enumerate(first):
        lo=min(F(row[j]['lower']) for row in ledger);hi=max(F(row[j]['upper']) for row in ledger)
        merged.append(t|dict(power=(lo,hi-lo)))
    return constant,merged,dict(analytic_identity_sha256=identity,reference_ranges=ledger,
        range_encoding='affine scalar interval; not a reference curve',whole_reference_domain=['0','1'])


def make_block(network,graph,items,scales,weights,metric,basis,balance,radius):
    representative=items[(len(items)-1)//2];u=F(1,2)
    with localcontext() as ctx:
        ctx.prec=100
        h,_=prior.descriptor(network,graph,[law.real.event.decimal(law.real.poly.evaluate(v,u)) for v in representative['prepared']['x']],100)
    x=np.linalg.inv(np.array(h,dtype=float)).tolist()
    if not np.isfinite(x).all():raise ValueError('finite shared candidate required')
    compiled=[law.real.tube.weighted.compile_terms(network,graph,item['prepared'],x,scales) for item in items]
    constant,terms,ledger=merge_terms(compiled)
    cover=law.real.tube.inflated_cover(constant,terms,law.real.tube.gains(network,graph),F(0),F(1),radius)
    block=dict(support_indices=[i['interval_index'] for i in items],representative_index=representative['interval_index'],
        representative_u=str(u),candidate_inverse_binary=x,descriptor_binary_sha256=law.digest(np.array(h,dtype=float).tolist()),
        ledger=ledger,cover=cover,inverse_certified=cover['strict_contraction'],reference_sha256=[i['prepared_sha256'] for i in items])
    if not block['inverse_certified']:return block,None
    inverse,proof=law.real.tube.cells.structured_inverse(x,scales,cover,F(cover['contraction_upper']))
    # Rates are independent of forcing; their complete proofs occur once per block.
    _,rates=law.cell_metrics(inverse,weights,items[0]['forcing'][0],metric,basis,balance)
    block.update(inverse_certificate=proof,inverse_intervals_sha256=law.digest(law.real.tube.cells.packed_matrix(inverse)),rate_certificate=rates)
    return block,inverse


def measure_variant(network,graph,items,source,metric,left_reference,end,weights,scales,basis,balance,width):
    if width not in WIDTHS:raise ValueError('predeclared width required')
    previous=source;initial_end=end;records=[];blocks=[];accepted=0
    cost=dict(preconditioners=0,inverses=0,rate_queries=0,actions=0)
    active=None;inverse=None
    for offset,item in enumerate(items):
        origin=F(previous['peak_node_error_upper_v']);incoming=law.transfer(previous);trials=[]
        for radius in RADII:
            cells=[];block_index=None
            if origin>=radius:
                result=dict(accepted=False,reason='incoming nodal bound not strictly inside candidate tube',actual_dae_error_bound=False)
            else:
                if offset%width==0:
                    active,inverse=make_block(network,graph,items[offset:offset+width],scales,weights,metric,basis,balance,radius)
                    active.update(radius_v=str(radius),block_index=len(blocks));blocks.append(active);cost['preconditioners']+=1
                    if inverse is not None:
                        cost['inverses']+=1;cost['rate_queries']+=sum(len(v['probes']) for v in active['rate_certificate'].values())
                if active is None or F(active['radius_v'])!=radius or item['interval_index'] not in active['support_indices']:
                    raise ValueError('same uniform block and radius required')
                block_index=active['block_index']
                if inverse is None:
                    result=dict(accepted=False,reason='shared mean descriptor cover rejected',actual_dae_error_bound=False)
                else:
                    for k,(forcing,rhs) in enumerate(zip(item['forcing'],item['rhs'])):
                        if F(forcing['duration_s'])!=item['prepared']['h']/8 or F(rhs['duration_s'])!=item['prepared']['h']/8:
                            raise ValueError('same physical duration required')
                        original=law.fine.fine_metrics(inverse,weights,forcing,metric,active['rate_certificate']['balanced']['mu_metric_upper_per_s'])
                        action=law.action.budgets(active['candidate_inverse_binary'],scales,active['cover'],rhs,weights,metric)
                        cost['actions']+=len(action['subcells'])
                        cells.append(dict(index=k,inverse_certified=True,forcing_inputs=forcing,original_metrics=original,
                            action=action,metrics=law.action.refine_metrics(original,action,True),rhs_sha256=law.digest(rhs),block_index=block_index))
                    result=law.blocks.close(cells,incoming,radius,origin)
            trials.append(dict(radius_v=str(radius),block_index=block_index,cells=cells,result=result))
        record=dict(interval_index=item['interval_index'],start_s=item['start_s'],end_s=item['end_s'],
            incoming_certified_result_sha256=law.digest(previous),incoming_block_error_upper_v=incoming,incoming_node_error_upper_v=str(origin),
            incoming_metric_sha256=law.digest(metric),prepared_sha256=item['prepared_sha256'],source_storage=item['source_storage'],
            interface=law.real.continuity(network,left_reference,item['prepared'],end,F(item['start_s'])),
            trials=trials,selected_trial_index=law.select(trials))
        records.append(record);admitted=law.admit(previous,end,record)
        print(json.dumps(dict(width=width,interval=item['interval_index'],accepted=admitted is not None,
            local_or_accumulated_node_v=prior.diagnostic_bound(trials[-1]['result']),reason=trials[-1]['result']['reason'])),flush=True)
        if admitted is None:break
        previous,end=admitted;left_reference=item['prepared'];accepted+=1
    return dict(width=width,blocks=blocks,records=records,cost=cost,initial_certified_end_s=str(initial_end),
        accepted_additional_intervals=accepted,accepted_intervals_total=8+accepted,
        continuous_actual_error_certified_duration_s=str(end),final_certified_result=previous,
        first_gap_index=records[-1]['interval_index'] if records[-1]['selected_trial_index'] is None else None,
        complete_known_bank=accepted==len(items),stop_reason='declared_limit' if accepted==len(items) else 'first_gap')


def generate():
    old=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
    if OUTPUT.exists() or SUMMARY.exists() or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('fresh destinations required')
    before=hashes(PATHS);env=environment();control=read(prior.OUTPUT);eighth=read(prior.ancestor.OUTPUT)
    source,metric,left=prior.source(eighth);end=F(eighth['continuous_actual_error_certified_duration_s'])
    if law.digest(metric)!=control['metric_sha256'] or control['weights']!=eighth['weights'] or control['descriptor_scales']!=eighth['descriptor_scales']:
        raise ValueError('unchanged norm, weights and descriptor scales required')
    network=prior.constructor.CompensatedBdfNetwork(200,prior.constructor.model_parameters(1,'finite_transit'))
    startup=read(prior.startup_source.OUTPUT);graph=read(prior.graph_source.OUTPUT)['graph']
    items=references(network,startup,control);weights=list(map(F,control['weights']));scales=list(map(F,control['descriptor_scales']))
    basis=law.blocks.directed.basis(metric);balance=law.blocks.balanced.balance(basis);variants=[];selected=None
    for width in WIDTHS:
        variant=measure_variant(network,graph,items,source,metric,left,end,weights,scales,basis,balance,width);variants.append(variant)
        if variant['complete_known_bank']:selected=len(variants)-1;break
    if hashes(PATHS)!=before:raise ValueError('shared cover inputs changed')
    return dict(schema='rf-d/bdf-static-shared-covers/v1',environment=env,source_sha256=before,
        integer_text_limit_before=old,integer_text_limit_during=0,width_order=list(WIDTHS),radius_order=list(map(str,RADII)),
        candidate_rule='lower ordinal middle support, u=1/2, decimal100 descriptor, binary64 inverse',
        source_certified_result_sha256=law.digest(source),initial_certified_end_s=str(end),fixed_metric=metric,metric_sha256=law.digest(metric),
        congruence=basis,balance=balance,weights=control['weights'],descriptor_scales=control['descriptor_scales'],groups=control['groups'],
        control_manifest_sha256=before[prior.OUTPUT.relative_to(ROOT).as_posix()],control_accepted_intervals=16,
        control_end_s=control['continuous_actual_error_certified_duration_s'],control_peak_node_error_upper_v=control['final_certified_result']['peak_node_error_upper_v'],
        control_cost=dict(preconditioners=control['new_preconditioners'],inverses=control['new_inverse_enclosures'],rate_queries=control['new_rate_ldlt_queries'],actions=control['new_action_subcell_certificates']),
        control_record_storage_bytes=sum(row['storage']['bytes'] for row in control['records']),variants=variants,selected_variant_index=selected,
        total_cost={k:sum(v['cost'][k] for v in variants) for k in variants[0]['cost']},
        new_nonlinear_solves=0,new_metric_systems=0,conditional_block_covers_include_unreached_supports=True,
        full_reference_ranges=True,whole_future_potential_tube=True,actual_individual_memory_transport=True,
        prior_reports_modified=False,reference_changed=False,rhs_changed=False,junction_norm_changed=False,clock_translation=False,
        independent_remainders_cancelled=False,numerical_gates_changed=False,original_integrator_modified=False,
        time_coverage_extended=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT.exists() or SUMMARY.exists():raise ValueError('fresh destinations required')
    storage=store(report,OUTPUT)
    variants=[]
    for v in report['variants']:
        variants.append({k:value for k,value in v.items() if k not in ('records','blocks','final_certified_result')}|dict(
            final_certified_result={k:value for k,value in v['final_certified_result'].items() if k!='propagation'},
            blocks=[{k:b[k] for k in ('block_index','support_indices','representative_index','radius_v','inverse_certified')}|dict(contraction_upper=b['cover']['contraction_upper']) for b in v['blocks']],
            records=[{k:r[k] for k in ('interval_index','start_s','end_s','selected_trial_index','incoming_node_error_upper_v')}|dict(
                results=[{k:value for k,value in t['result'].items() if k!='propagation'} for t in r['trials']]) for r in v['records']]))
    summary={k:value for k,value in report.items() if k not in ('variants','fixed_metric','congruence','balance')}|dict(variants=variants,storage=storage)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return summary
if __name__=='__main__':save(generate())
