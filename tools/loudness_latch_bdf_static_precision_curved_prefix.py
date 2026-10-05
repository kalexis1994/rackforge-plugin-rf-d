"""Contiguous curved-reference extension with immutable per-support evidence."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
import gzip,hashlib,json,sys
import numpy as np
import loudness_latch_bdf_static_precision_curved_reference as ancestor
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
ROOT=ancestor.ROOT
law=ancestor.law;curve=ancestor.curve;constructor=ancestor.constructor
startup_source=ancestor.startup_source;graph_source=ancestor.graph_source
descriptor=ancestor.descriptor;read=ancestor.read;serial=ancestor.serial
diagnostic_bound=ancestor.diagnostic_bound
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_curved_prefix.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_curved_prefix_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_PREFIJO_CURVO_PROTOCOLO.md'
START_INDEX=8
ADDITIONAL_LIMIT=8
VARIANT='c7_bubble'
MODE='direct_and_memory'
RADII=ancestor.RADII[:2]
PATHS=tuple(dict.fromkeys((*ancestor.PATHS,ancestor.OUTPUT,ancestor.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_curved_reference_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_curved_reference_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_curved_reference_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_curved_reference_inputs_validation.json',
    Path(__file__).resolve(),PROTOCOL)))


def interval_output(index):
    if type(index) is not int or not START_INDEX<=index<START_INDEX+ADDITIONAL_LIMIT:
        raise ValueError('declared support index required')
    return ROOT/f'evidence/loudness_latch_bdf_static_precision_curved_prefix_interval_{index:03d}.json.gz'


def source(report):
    previous=report['final_certified_result'];law.transfer(previous)
    metric=report['fixed_metric']
    if report['accepted_intervals_total']!=8 or report['first_gap_index'] is not None or report['selected_variant_trial']!=[1,1]:
        raise ValueError('known eighth curved certificate required')
    rec=report['records'][1]
    if rec['variant']!=VARIANT or rec['interval_index']!=7 or rec['selected_trial_index']!=1 or rec['trials'][1]['result']!=previous:
        raise ValueError('same selected curved reference and actual result required')
    if F(report['continuous_actual_error_certified_duration_s'])!=F(rec['end_s']) or report['metric_sha256']!=law.digest(metric) or not metric['accepted'] or report['groups']!=[list(g) for g in law.fine.GROUPS]:
        raise ValueError('same certified real clock, fixed metric and 22 groups required')
    if rec['incoming_metric_sha256']!=report['metric_sha256']:
        raise ValueError('same norm lineage required')
    return previous,metric,rec['prepared']


def measure(network,graph,startup,interval_index,previous,metric,left_prepared,certified_end,weights,scales,basis,balance,source_hashes):
    variant=VARIANT;preconditioners=1;inverse_count=rate_queries=action_count=0
    initial=startup_source.unpack(network,startup['rows'][interval_index-1]['history'])
    endpoint=startup_source.unpack(network,startup['rows'][interval_index]['history'])
    affine=law.real.prepare(network,initial,endpoint)
    with localcontext() as ctx:
        ctx.prec=100;hm,_=descriptor(network,graph,[law.real.event.decimal(law.real.poly.evaluate(v,F(1,2))) for v in affine['x']],100)
    candidate_inverse=np.linalg.inv(np.array(hm,dtype=float)).tolist()
    if not np.isfinite(candidate_inverse).all():raise ValueError('finite bubble direction required')
    candidate_rhs=law.action.rhs(network,graph,affine,F(0),F(1))
    curved,bubble=curve.candidate(network,affine,candidate_inverse,candidate_rhs['polynomials'])
    prepared=curved
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
    record=dict(schema='rf-d/bdf-static-curved-prefix-interval/v1',source_sha256=source_hashes,variant=variant,interval_index=interval_index,start_s=str(F(initial.time_s)),end_s=str(F(endpoint.time_s)),prepared=serial(prepared),interface=join,
        incoming_certified_result_sha256=law.digest(previous),incoming_metric_sha256=law.digest(metric),incoming_node_error_upper_v=str(origin),
        incoming_block_error_upper_v=incoming,base_cells=serial(base),rhs=rhs,trials=trials,selected_trial_index=selection,
        candidate_inverse_binary=candidate_inverse,candidate_rhs=candidate_rhs,bubble=bubble,
        queries=[dict(u=str(u),decimal100=law.real.tube.query(network,graph,prepared,u,100)) for u in (F(0),F(1,2),F(1))])
    return record,dict(preconditioners=preconditioners,inverses=inverse_count,rate_queries=rate_queries,actions=action_count)


def load_record(row):
    storage=row['storage'];path=interval_output(row['interval_index'])
    if storage['path']!=path.relative_to(ROOT).as_posix():raise ValueError('identified support destination required')
    raw=path.read_bytes()
    if len(raw)!=storage['bytes'] or hashlib.sha256(raw).hexdigest()!=storage['compressed_sha256']:
        raise ValueError('support compressed byte identity mismatch')
    plain=gzip.decompress(raw);record=json.loads(plain)
    if plain!=canonical(record) or hashlib.sha256(plain).hexdigest()!=storage['canonical_json_sha256']:
        raise ValueError('support canonical identity mismatch')
    if record['schema']!='rf-d/bdf-static-curved-prefix-interval/v1' or record['interval_index']!=row['interval_index'] or record['start_s']!=row['start_s'] or record['end_s']!=row['end_s'] or record['selected_trial_index']!=row['selected_trial_index']:
        raise ValueError('same complete support identity required')
    return record


def generate():
    old_limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
    destinations=(OUTPUT,SUMMARY,*(interval_output(k) for k in range(START_INDEX,START_INDEX+ADDITIONAL_LIMIT)))
    if any(p in PATHS or p.exists() for p in destinations) or len(set(destinations))!=len(destinations):
        raise ValueError('fresh distinct evidence destinations required; preserve prior attempts')
    before=hashes(PATHS);env=environment();support=read(ancestor.OUTPUT)
    previous,metric,left_prepared=source(support);initial_previous=previous
    startup=read(startup_source.OUTPUT);graph=read(graph_source.OUTPUT)['graph']
    network=constructor.CompensatedBdfNetwork(200,constructor.model_parameters(1,'finite_transit'))
    certified_end=F(support['continuous_actual_error_certified_duration_s']);initial_end=certified_end
    weights=list(map(F,support['weights']));scales=list(map(F,support['descriptor_scales']))
    basis=law.blocks.directed.basis(metric);balance=law.blocks.balanced.balance(basis)
    records=[];accepted=0;counts=dict(preconditioners=0,inverses=0,rate_queries=0,actions=0);storage_hashes={}
    for index in range(START_INDEX,START_INDEX+ADDITIONAL_LIMIT):
        record,cost=measure(network,graph,startup,index,previous,metric,left_prepared,certified_end,weights,scales,basis,balance,before)
        if hashes(PATHS)!=before:raise ValueError('curved prefix inputs changed before archival')
        storage=store(record,interval_output(index));storage_hashes[storage['path']]=storage['compressed_sha256']
        row=dict(interval_index=index,start_s=record['start_s'],end_s=record['end_s'],selected_trial_index=record['selected_trial_index'],storage=storage,
            incoming_certified_result_sha256=record['incoming_certified_result_sha256'],incoming_node_error_upper_v=record['incoming_node_error_upper_v'],
            trials=[dict(radius_v=t['radius_v'],inverse_certified_cells=sum(c['inverse_certified'] for c in t['covers']),result={k:v for k,v in t['result'].items() if k!='propagation'}) for t in record['trials']],cost=cost)
        records.append(row)
        for k in counts:counts[k]+=cost[k]
        admitted=law.admit(previous,certified_end,record)
        if admitted is None:break
        previous,certified_end=admitted;left_prepared=record['prepared'];accepted+=1
    if hashes(PATHS)!=before:raise ValueError('curved prefix inputs changed')
    return dict(schema='rf-d/bdf-static-curved-prefix/v1',environment=env,source_sha256=before|storage_hashes,producer_source_sha256=before,
        integer_text_limit_before=old_limit,integer_text_limit_during=0,source_selected_variant_trial=support['selected_variant_trial'],source_certified_result_sha256=law.digest(initial_previous),
        initial_certified_end_s=str(initial_end),start_interval_index=START_INDEX,additional_limit=ADDITIONAL_LIMIT,variant=VARIANT,mode=MODE,radius_order=list(map(str,RADII)),
        fixed_metric=metric,metric_sha256=law.digest(metric),congruence=basis,balance=balance,weights=support['weights'],descriptor_scales=list(map(str,scales)),groups=support['groups'],records=records,
        accepted_additional_intervals=accepted,accepted_intervals_total=START_INDEX+accepted,attempted_additional_intervals=len(records),continuous_actual_error_certified_duration_s=str(certified_end),
        attempted_end_s=records[-1]['end_s'],final_certified_result=previous,first_gap_index=records[-1]['interval_index'] if records[-1]['selected_trial_index'] is None else None,
        new_nonlinear_solves=0,new_preconditioners=counts['preconditioners'],new_inverse_enclosures=counts['inverses'],new_metric_systems=0,new_rate_ldlt_queries=counts['rate_queries'],new_action_subcell_certificates=counts['actions'],
        stop_reason='first_gap' if records[-1]['selected_trial_index'] is None else 'declared_limit',complete_prefix_manifest=True,partial_supports_admitted=False,endpoint_preserving_references=True,real_history_only=True,individual_memory_transport=True,
        small_currents_dropped=False,circuit_regularized=False,independent_remainders_cancelled=False,junction_norm_changed=False,clock_translation=False,dc_anchor_reset=False,
        original_integrator_modified=False,prior_reports_modified=False,numerical_gates_changed=False,full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT in PATHS or SUMMARY in PATHS or OUTPUT.exists() or SUMMARY.exists():raise ValueError('fresh manifest destinations required')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ('final_certified_result','fixed_metric','congruence','balance')}
    summary.update(storage=storage,final_certified_result={k:v for k,v in report['final_certified_result'].items() if k!='propagation'})
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return summary
if __name__=='__main__':save(generate())
