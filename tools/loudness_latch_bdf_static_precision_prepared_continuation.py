"""New-history curved continuation with shared certificates and full archives."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
import gzip,hashlib,json,sys,io,traceback
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
import numpy as np
import loudness_latch_bdf_static_precision_shared_continuation as ancestor
import loudness_latch_prepared_action as prepared_action
shared=ancestor.shared
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
ROOT=shared.ROOT;prior=shared.prior;law=shared.law;serial=shared.serial;read=shared.read
START_INDEX=24;ADDITIONAL_LIMIT=8;WIDTHS=shared.WIDTHS;RADII=shared.RADII
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_prepared_continuation.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_prepared_continuation_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_CONTINUACION_PREPARADA_PROTOCOLO.md'
LAUNCH=ROOT/'evidence/loudness_latch_bdf_static_precision_prepared_continuation_launch.json'
ANCESTOR_REPORT=read(ancestor.OUTPUT)
PATHS=tuple(dict.fromkeys((*(ROOT/name for name in ANCESTOR_REPORT['source_sha256']),ancestor.OUTPUT,ancestor.SUMMARY,
    *(ROOT/'evidence'/name for name in (
        'loudness_latch_bdf_static_precision_shared_continuation_validation.json',
        'loudness_latch_prepared_action_benchmark.json.gz','loudness_latch_prepared_action_benchmark_summary.json',
        'loudness_latch_prepared_action_validation.json','loudness_latch_prepared_action_inputs.json.gz',
        'loudness_latch_prepared_action_inputs_summary.json','loudness_latch_prepared_action_inputs_validation.json')),
    ROOT/'tools/loudness_latch_prepared_action.py',ROOT/'tools/loudness_latch_prepared_action_benchmark.py',
    Path(__file__).resolve(),PROTOCOL)))


def artifact_path(kind,index,width=None):
    if kind=='template' and type(index) is int and START_INDEX<=index<START_INDEX+ADDITIONAL_LIMIT and width is None:
        tail=f'template_{index:03d}'
    elif kind in ('block','interval') and type(width) is int and width in WIDTHS and type(index) is int:
        if kind=='interval' and START_INDEX<=index<START_INDEX+ADDITIONAL_LIMIT:tail=f'w{width}_{kind}_{index:03d}'
        elif kind=='block' and 0<=index<ADDITIONAL_LIMIT//width:tail=f'w{width}_{kind}_{index:03d}'
        else:raise ValueError('declared artifact index required')
    else:raise ValueError('typed declared artifact destination required')
    return ROOT/f'evidence/loudness_latch_bdf_static_precision_prepared_continuation_{tail}.json.gz'


def source(report,left_record,left_template):
    if report['schema']!='rf-d/bdf-static-shared-continuation/v1' or report['selected_variant_index']!=0:
        raise ValueError('identified complete shared continuation source required')
    v=report['variants'][0];previous=v['final_certified_result'];metric=report['fixed_metric']
    law.transfer(previous)
    if v['width']!=8 or not v['complete_new_bank'] or v['accepted_intervals_total']!=START_INDEX or v['first_gap_index'] is not None:
        raise ValueError('complete twenty-four-support source required')
    if law.digest(metric)!=report['metric_sha256'] or not metric['accepted'] or report['groups']!=[list(g) for g in law.fine.GROUPS]:
        raise ValueError('same accepted norm and groups required')
    if left_record['interval_index']!=23 or left_template['interval_index']!=23 or left_record['source_storage']!=report['templates'][-1]['storage']:
        raise ValueError('same identified source curve and support required')
    if left_template['prepared_sha256']!=law.digest(left_template['prepared']) or v['records'][-1]['prepared_sha256']!=left_template['prepared_sha256'] or left_record['prepared_sha256']!=left_template['prepared_sha256']:
        raise ValueError('same complete source reference required')
    if F(v['continuous_actual_error_certified_duration_s'])!=F(left_record['end_s']) or F(left_template['end_s'])!=F(left_record['end_s']):
        raise ValueError('same actual source endpoint required')
    if left_record['selected_trial_index']!=1 or canonical(left_record['trials'][1]['result'])!=canonical(previous):
        raise ValueError('same selected outgoing real result required')
    return previous,metric,left_template['prepared'],F(v['continuous_actual_error_certified_duration_s'])


def build_template(network,graph,startup,index,source_hashes):
    artifact_path('template',index)
    a,b=[prior.startup_source.unpack(network,startup['rows'][j]['history']) for j in (index-1,index)]
    affine=law.real.prepare(network,a,b)
    with localcontext() as ctx:
        ctx.prec=100
        hm,_=prior.descriptor(network,graph,[law.real.event.decimal(law.real.poly.evaluate(v,F(1,2))) for v in affine['x']],100)
    x=np.linalg.inv(np.array(hm,dtype=float)).tolist()
    if not np.isfinite(x).all():raise ValueError('finite new bubble direction required')
    initial_rhs=law.action.rhs(network,graph,affine,F(0),F(1))
    prepared,bubble=prior.curve.candidate(network,affine,x,initial_rhs['polynomials'])
    rhs=[];forcing=[];residuals=[]
    for k in range(8):
        lo,hi=F(k,8),F(k+1,8)
        residual,f=law.real.tube.forcing(network,graph,prepared,lo,hi)
        residuals.append(serial(residual));forcing.append(f);rhs.append(law.action.rhs(network,graph,prepared,lo,hi))
    template=dict(schema='rf-d/bdf-static-prepared-continuation-template/v1',source_sha256=source_hashes,
        interval_index=index,start_s=str(F(a.time_s)),end_s=str(F(b.time_s)),prepared=serial(prepared),prepared_sha256=law.digest(serial(prepared)),
        candidate_inverse_binary=x,candidate_rhs=initial_rhs,bubble=bubble,rhs=rhs,forcing=forcing,residual_bounds=residuals,
        queries=[dict(u=str(u),decimal100=law.real.tube.query(network,graph,prepared,u,100)) for u in (F(0),F(1,2),F(1))],
        conditional_reference_only=True,actual_dae_error_bound=False)
    return template,prepared


def unpack_template(network,startup,template,storage):
    k=template['interval_index'];a,b=[prior.startup_source.unpack(network,startup['rows'][j]['history']) for j in (k-1,k)]
    affine=law.real.prepare(network,a,b)
    prepared,bubble=prior.curve.candidate(network,affine,template['candidate_inverse_binary'],template['candidate_rhs']['polynomials'])
    if serial(prepared)!=template['prepared'] or bubble!=template['bubble'] or law.digest(template['prepared'])!=template['prepared_sha256']:
        raise ValueError('same complete template reference required')
    if F(a.time_s)!=F(template['start_s']) or F(b.time_s)!=F(template['end_s']):raise ValueError('same real history clock required')
    return dict(interval_index=k,start_s=template['start_s'],end_s=template['end_s'],prepared=prepared,
        prepared_sha256=template['prepared_sha256'],rhs=template['rhs'],forcing=template['forcing'],source_storage=storage)


def measure_variant(network,graph,items,source,metric,left_reference,end,weights,scales,basis,balance,width,action_provider):
    if width not in WIDTHS:raise ValueError('predeclared width required')
    if not callable(getattr(action_provider,'prepare',None)) or not callable(getattr(action_provider,'budgets',None)):
        raise ValueError('explicit complete action provider required')
    if not items:raise ValueError('nonempty future reference bank required')
    for item in items:
        if len(item['forcing'])!=8 or len(item['rhs'])!=8:raise ValueError('complete eight-cell forcing and RHS required')
        if any(F(v['duration_s'])!=item['prepared']['h']/8 for group in ('forcing','rhs') for v in item[group]):
            raise ValueError('same physical duration required')
    previous=source;initial_end=end;records=[];blocks=[];accepted=0
    cost=dict(preconditioners=0,inverses=0,rate_queries=0,actions=0,prepared_contexts=0,budget_calls=0)
    active=None;inverse=None;context=None
    for offset,item in enumerate(items):
        origin=F(previous['peak_node_error_upper_v']);incoming=law.transfer(previous);trials=[]
        for radius in RADII:
            cells=[];block_index=None
            if origin>=radius:
                result=dict(accepted=False,reason='incoming nodal bound not strictly inside candidate tube',actual_dae_error_bound=False)
            else:
                if offset%width==0:
                    active,inverse=shared.make_block(network,graph,items[offset:offset+width],scales,weights,metric,basis,balance,radius)
                    active.update(radius_v=str(radius),block_index=len(blocks));blocks.append(active);cost['preconditioners']+=1
                    if inverse is not None:
                        cost['inverses']+=1;cost['rate_queries']+=sum(len(v['probes']) for v in active['rate_certificate'].values())
                        context=action_provider.prepare(active['candidate_inverse_binary'],scales,active['cover'])
                        active['action_preparation']=dict(input_sha256=context.input_sha256,state_sha256=context.state_sha256,n=context.n)
                        cost['prepared_contexts']+=1
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
                        action=action_provider.budgets(context,active['candidate_inverse_binary'],scales,active['cover'],rhs,weights,metric)
                        cost['budget_calls']+=1
                        cost['actions']+=len(action['subcells'])
                        cells.append(dict(index=k,inverse_certified=True,forcing_inputs=forcing,original_metrics=original,
                            action=action,metrics=law.action.refine_metrics(original,action,True),rhs_sha256=law.digest(rhs),block_index=block_index,
                            action_context_sha256=context.input_sha256,action_state_sha256=context.state_sha256))
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
        accepted_additional_intervals=accepted,accepted_intervals_total=START_INDEX+accepted,
        continuous_actual_error_certified_duration_s=str(end),final_certified_result=previous,
        first_gap_index=records[-1]['interval_index'] if records[-1]['selected_trial_index'] is None else None,
        complete_new_bank=accepted==len(items),stop_reason='declared_limit' if accepted==len(items) else 'first_gap')


def load_artifact(storage,kind,index,width=None):
    path=artifact_path(kind,index,width)
    if storage['path']!=path.relative_to(ROOT).as_posix():raise ValueError('same identified artifact path required')
    raw=path.read_bytes()
    if len(raw)!=storage['bytes'] or hashlib.sha256(raw).hexdigest()!=storage['compressed_sha256']:raise ValueError('artifact compressed identity mismatch')
    plain=gzip.decompress(raw);data=json.loads(plain)
    if plain!=canonical(data) or hashlib.sha256(plain).hexdigest()!=storage['canonical_json_sha256']:raise ValueError('artifact canonical identity mismatch')
    if data['schema']!=f'rf-d/bdf-static-prepared-continuation-{kind}/v1':raise ValueError('same typed artifact schema required')
    if kind=='template':valid=data['interval_index']==index
    elif kind=='block':valid=data['width']==width and data['block']['block_index']==index
    else:valid=data['width']==width and data['record']['interval_index']==index
    if not valid:raise ValueError('same typed artifact identity required')
    return data


def archive_variant(v,source_hashes):
    blocks=[];records=[];derived={}
    for b in v['blocks']:
        data=dict(schema='rf-d/bdf-static-prepared-continuation-block/v1',source_sha256=source_hashes,width=v['width'],block=b)
        storage=store(data,artifact_path('block',b['block_index'],v['width']));derived[storage['path']]=storage['compressed_sha256']
        blocks.append(dict(block_index=b['block_index'],support_indices=b['support_indices'],inverse_certified=b['inverse_certified'],storage=storage))
    for rec in v['records']:
        data=dict(schema='rf-d/bdf-static-prepared-continuation-interval/v1',source_sha256=source_hashes|derived,width=v['width'],record=rec)
        storage=store(data,artifact_path('interval',rec['interval_index'],v['width']));derived[storage['path']]=storage['compressed_sha256']
        records.append(dict(interval_index=rec['interval_index'],start_s=rec['start_s'],end_s=rec['end_s'],selected_trial_index=rec['selected_trial_index'],
            prepared_sha256=rec['prepared_sha256'],storage=storage,trials=[dict(radius_v=t['radius_v'],block_index=t['block_index'],
                result={k:value for k,value in t['result'].items() if k!='propagation'}) for t in rec['trials']]))
    return {k:value for k,value in v.items() if k not in ('blocks','records')}|dict(blocks=blocks,records=records),derived


def generate():
    old=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
    destinations=[OUTPUT,SUMMARY,LAUNCH,*[artifact_path('template',k) for k in range(24,32)]]
    for w in WIDTHS:
        destinations.extend(artifact_path('block',k,w) for k in range(ADDITIONAL_LIMIT//w))
        destinations.extend(artifact_path('interval',k,w) for k in range(24,32))
    if len(set(destinations))!=len(destinations) or any(p.exists() or p in PATHS for p in destinations):raise ValueError('fresh distinct destinations required; preserve attempts')
    before=hashes(PATHS);env=environment();old_report=read(ancestor.OUTPUT)
    left_record=ancestor.load_artifact(old_report['variants'][0]['records'][-1]['storage'],'interval',23,8)['record']
    left_template=ancestor.load_artifact(old_report['templates'][-1]['storage'],'template',23)
    previous,metric,left,end=source(old_report,left_record,left_template)
    network=prior.constructor.CompensatedBdfNetwork(200,prior.constructor.model_parameters(1,'finite_transit'))
    graph=read(prior.graph_source.OUTPUT)['graph'];startup=read(prior.startup_source.OUTPUT)
    items=[];templates=[];derived={};last=end
    for k in range(START_INDEX,START_INDEX+ADDITIONAL_LIMIT):
        template,prepared=build_template(network,graph,startup,k,before)
        if F(template['start_s'])!=last:raise ValueError('contiguous real template histories required')
        last=F(template['end_s'])
        if hashes(PATHS)!=before:raise ValueError('inputs changed before template archival')
        storage=store(template,artifact_path('template',k));derived[storage['path']]=storage['compressed_sha256']
        templates.append(dict(interval_index=k,start_s=template['start_s'],end_s=template['end_s'],prepared_sha256=template['prepared_sha256'],storage=storage))
        items.append(dict(interval_index=k,start_s=template['start_s'],end_s=template['end_s'],prepared=prepared,
            prepared_sha256=template['prepared_sha256'],rhs=template['rhs'],forcing=template['forcing'],source_storage=storage))
        print(json.dumps(dict(template=k,end_s=float(last),conditional_reference_only=True)),flush=True)
    weights=list(map(F,old_report['weights']));scales=list(map(F,old_report['descriptor_scales']))
    basis=law.blocks.directed.basis(metric);balance=law.blocks.balanced.balance(basis);variants=[]
    for width in WIDTHS:
        variant=measure_variant(network,graph,items,previous,metric,left,end,weights,scales,basis,balance,width,prepared_action)
        if hashes(PATHS)!=before:raise ValueError('inputs changed before variant archival')
        archived,new_hashes=archive_variant(variant,before|derived);derived.update(new_hashes);variants.append(archived)
        if variant['complete_new_bank']:break
    selected=max(range(len(variants)),key=lambda n:variants[n]['accepted_additional_intervals']);v=variants[selected]
    if hashes(PATHS)!=before:raise ValueError('continuation inputs changed')
    return dict(schema='rf-d/bdf-static-prepared-continuation/v1',environment=env,source_sha256=before|derived,producer_source_sha256=before,
        integer_text_limit_before=old,integer_text_limit_during=0,source_selected_variant_index=0,source_selected_trial_index=1,source_certified_result_sha256=law.digest(previous),
        initial_certified_end_s=str(end),source_accepted_intervals=START_INDEX,start_interval_index=START_INDEX,additional_limit=ADDITIONAL_LIMIT,
        width_order=list(WIDTHS),radius_order=list(map(str,RADII)),fixed_metric=metric,metric_sha256=law.digest(metric),weights=old_report['weights'],
        descriptor_scales=old_report['descriptor_scales'],groups=old_report['groups'],congruence=basis,balance=balance,templates=templates,variants=variants,
        selected_variant_index=selected,accepted_additional_intervals=v['accepted_additional_intervals'],accepted_intervals_total=v['accepted_intervals_total'],
        continuous_actual_error_certified_duration_s=v['continuous_actual_error_certified_duration_s'],final_certified_result=v['final_certified_result'],
        first_gap_index=v['first_gap_index'],stop_reason=v['stop_reason'],new_reference_preconditioners=len(templates),
        total_cost={k:sum(v['cost'][k] for v in variants) for k in variants[0]['cost']},new_nonlinear_solves=0,new_metric_systems=0,
        explicit_action_provider=True,prepared_action_contexts_verified=True,conditional_templates_do_not_admit_time=True,complete_artifact_manifest=True,real_history_only=True,actual_individual_memory_transport=True,
        source_bound_reset=False,clock_translation=False,junction_norm_changed=False,prior_reports_modified=False,original_integrator_modified=False,
        numerical_gates_changed=False,independent_remainders_cancelled=False,partial_artifacts_admitted=False,
        global_1mv_gate_closed=False,full_path_coverage=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT.exists() or SUMMARY.exists():raise ValueError('fresh manifest destinations required')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ('fixed_metric','congruence','balance','final_certified_result','variants')}
    summary['variants']=[{k:v for k,v in branch.items() if k!='final_certified_result'}|dict(final_certified_result={k:v for k,v in branch['final_certified_result'].items() if k!='propagation'}) for branch in report['variants']]
    summary.update(storage=storage,final_certified_result={k:v for k,v in report['final_certified_result'].items() if k!='propagation'})
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return summary
class AuditStream(io.StringIO):
    def __init__(self,target):super().__init__();self.target=target
    def write(self,value):self.target.write(value);return super().write(value)
    def flush(self):self.target.flush()


def run():
    sys.set_int_max_str_digits(0)
    if LAUNCH.exists():raise ValueError('fresh launch receipt required')
    before=hashes(PATHS);env=environment();out=AuditStream(sys.stdout);err=AuditStream(sys.stderr);code=0
    with redirect_stdout(out),redirect_stderr(err):
        try:save(generate())
        except BaseException as failure:
            traceback.print_exc();code=130 if isinstance(failure,KeyboardInterrupt) else 1
    after=hashes(PATHS)
    if before!=after:code=1
    receipt=dict(schema='rf-d/bdf-static-prepared-continuation-launch/v1',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        environment=env,command=[sys.executable,'-B',str(Path(__file__).resolve())],exit_code=code,
        stdout=out.getvalue(),stderr=err.getvalue(),producer_source_utf8=Path(__file__).read_text(encoding='utf-8'),
        source_sha256=before,source_sha256_before=before,source_sha256_after=after,inputs_unchanged=before==after,
        measurement_published=code==0 and OUTPUT.exists() and SUMMARY.exists())
    LAUNCH.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return code


if __name__=='__main__':sys.exit(run())
