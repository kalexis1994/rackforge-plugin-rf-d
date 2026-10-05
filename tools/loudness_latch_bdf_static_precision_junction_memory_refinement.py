"""Frozen partition refinement of the first gap; unchanged curve, norm and radius."""
from pathlib import Path
from fractions import Fraction as F
import gzip,hashlib,json,sys,io,traceback
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
import loudness_latch_bdf_static_precision_prepared_continuation_second as ancestor
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
ROOT=ancestor.ROOT;prior=ancestor.prior;law=ancestor.law;serial=ancestor.serial;read=ancestor.read
PARTITIONS=(8,16,32,64);INDEX=33;RADIUS=F(1,10**6)
PREFIX='loudness_latch_bdf_static_precision_junction_memory_refinement'
SCHEMA='rf-d/bdf-static-junction-memory-refinement'
OUTPUT=ROOT/f'evidence/{PREFIX}.json.gz';SUMMARY=ROOT/f'evidence/{PREFIX}_summary.json'
LAUNCH=ROOT/f'evidence/{PREFIX}_launch.json'
PROTOCOL=ROOT/'docs/BIESTABLE_MEMORIA_JUNTURAS_PROTOCOLO.md'
ANCESTOR_REPORT=read(ancestor.OUTPUT)
PATHS=tuple(dict.fromkeys((*(ROOT/name for name in ANCESTOR_REPORT['source_sha256']),
    ancestor.OUTPUT,ancestor.SUMMARY,ancestor.LAUNCH,
    *(ROOT/'evidence'/name for name in (
      'loudness_latch_bdf_static_precision_prepared_continuation_second_validation.json',
      'loudness_latch_bdf_static_precision_prepared_continuation_second_inputs.json.gz',
      'loudness_latch_bdf_static_precision_prepared_continuation_second_inputs_summary.json',
      'loudness_latch_bdf_static_precision_prepared_continuation_second_inputs_validation.json')),
    Path(__file__).resolve(),PROTOCOL)))


def artifact_path(kind,partition,index=None):
    if type(partition) is not int or partition not in PARTITIONS:raise ValueError('typed declared partition required')
    if kind=='cell' and type(index) is int and 0<=index<partition:tail=f'n{partition}_cell_{index:03d}'
    elif kind=='support' and index is None:tail=f'n{partition}_support_033'
    else:raise ValueError('typed declared artifact identity required')
    return ROOT/f'evidence/{PREFIX}_{tail}.json.gz'


def load_artifact(storage,kind,partition,index=None):
    path=artifact_path(kind,partition,index)
    if storage['path']!=path.relative_to(ROOT).as_posix():raise ValueError('same typed path required')
    raw=path.read_bytes()
    if len(raw)!=storage['bytes'] or hashlib.sha256(raw).hexdigest()!=storage['compressed_sha256']:raise ValueError('same compressed artifact required')
    plain=gzip.decompress(raw);data=json.loads(plain)
    if plain!=canonical(data) or hashlib.sha256(plain).hexdigest()!=storage['canonical_json_sha256']:raise ValueError('same canonical artifact required')
    if data['schema']!=f'{SCHEMA}-{kind}/v1' or data['partition']!=partition or data['interval_index']!=INDEX:raise ValueError('same artifact schema and support required')
    if kind=='cell' and data['cell']['index']!=index:raise ValueError('same cell index required')
    return data


def source(report,record,left_template,template,block):
    if report['schema']!='rf-d/bdf-static-prepared-continuation-second/v1' or report['selected_variant_index']!=0:raise ValueError('identified chosen first-gap source required')
    v=report['variants'][0];previous=v['final_certified_result'];metric=report['fixed_metric']
    if v['width']!=8 or v['accepted_intervals_total']!=33 or v['first_gap_index']!=33 or v['complete_new_bank']:raise ValueError('actual thirty-three-support source required')
    law.transfer(previous)
    if record['interval_index']!=32 or record['selected_trial_index']!=1 or canonical(record['trials'][1]['result'])!=canonical(previous):raise ValueError('chosen outgoing real result required')
    if canonical(report['final_certified_result'])!=canonical(previous) or report['accepted_intervals_total']!=33 or report['first_gap_index']!=33 or F(report['continuous_actual_error_certified_duration_s'])!=F(record['end_s']):raise ValueError('same root certificate and actual clock required')
    if not metric['accepted'] or law.digest(metric)!=report['metric_sha256'] or report['groups']!=[list(g) for g in law.fine.GROUPS]:raise ValueError('same fixed norm and groups required')
    if left_template['interval_index']!=32 or template['interval_index']!=33 or record['source_storage']!=report['templates'][0]['storage']:raise ValueError('same identified curves required')
    for t in (left_template,template):
        if law.digest(t['prepared'])!=t['prepared_sha256']:raise ValueError('same complete reference required')
    if record['prepared_sha256']!=left_template['prepared_sha256'] or F(left_template['end_s'])!=F(record['end_s']) or F(template['start_s'])!=F(record['end_s']):raise ValueError('same contiguous curve clock required')
    if block['support_indices']!=[33] or block['reference_sha256']!=[template['prepared_sha256']] or F(block['radius_v'])!=RADIUS or not block['inverse_certified']:raise ValueError('same certified support and radius required')
    if F(block['cover']['potential_radius_v'])!=RADIUS or block['cover']['left']!='0' or block['cover']['right']!='1':raise ValueError('same full tube domain required')
    return previous,metric,left_template['prepared'],F(record['end_s'])


def reconstruct_inverse(network,graph,item,block,scales):
    compiled=law.real.tube.weighted.compile_terms(network,graph,item['prepared'],block['candidate_inverse_binary'],scales)
    c,t,ledger=ancestor.shared.merge_terms([compiled])
    if ledger!=block['ledger']:raise ValueError('same complete analytic ledger required')
    cover=law.real.tube.inflated_cover(c,t,law.real.tube.gains(network,graph),F(0),F(1),RADIUS)
    if cover!=block['cover'] or not cover['strict_contraction']:raise ValueError('same certified mean domain required')
    inverse,proof=law.real.tube.cells.structured_inverse(block['candidate_inverse_binary'],scales,cover,F(cover['contraction_upper']))
    if proof!=block['inverse_certificate'] or law.digest(law.real.tube.cells.packed_matrix(inverse))!=block['inverse_intervals_sha256']:raise ValueError('same complete inverse certificate required')
    return inverse


def check_duration(forcing,rhs,prepared,partition,index):
    artifact_path('cell',partition,index)
    lo,hi=F(index,partition),F(index+1,partition)
    if F(forcing['left'])!=lo or F(forcing['right'])!=hi or F(forcing['duration_s'])!=prepared['h']/partition or F(rhs['duration_s'])!=prepared['h']/partition:raise ValueError('same physical cell clock required')
    if len(rhs['polynomials'])!=119 or len(rhs['subcells'])!=8:raise ValueError('complete RHS and unchanged inner partition required')


def build_cell(network,graph,prepared,inverse,block,weights,scales,metric,context,provider,partition,index,source_hashes):
    if not callable(getattr(provider,'budgets',None)):raise ValueError('explicit complete action provider required')
    lo,hi=F(index,partition),F(index+1,partition)
    residual,forcing=law.real.tube.forcing(network,graph,prepared,lo,hi)
    rhs=law.action.rhs(network,graph,prepared,lo,hi);check_duration(forcing,rhs,prepared,partition,index)
    original=law.fine.fine_metrics(inverse,weights,forcing,metric,block['rate_certificate']['balanced']['mu_metric_upper_per_s'])
    action=provider.budgets(context,block['candidate_inverse_binary'],scales,block['cover'],rhs,weights,metric)
    cell=dict(index=index,inverse_certified=True,forcing_inputs=forcing,original_metrics=original,
        action=action,metrics=law.action.refine_metrics(original,action,True),rhs_sha256=law.digest(rhs),
        action_context_sha256=context.input_sha256,action_state_sha256=context.state_sha256)
    data=dict(schema=f'{SCHEMA}-cell/v1',source_sha256=source_hashes,interval_index=INDEX,partition=partition,
        prepared_sha256=law.digest(serial(prepared)),left=str(lo),right=str(hi),residual_bounds=serial(residual),rhs=rhs,cell=cell,
        queries=[dict(u=str(u),absolute_u=str(lo+(hi-lo)*u),decimal100=law.real.tube.query(network,graph,prepared,lo+(hi-lo)*u,100)) for u in (F(0),F(1,2),F(1))])
    return data


def diagnostic(record):
    result=record['trials'][0]['result'];rows=[]
    for cell,trace in zip(record['trials'][0]['cells'],result['propagation']['trace']):
        g=list(map(F,cell['metrics']['nodal_block_gains'][66]))
        a=[v*F(x) for v,x in zip(g,trace['peak_anchor_v'])];f=[v*F(x) for v,x in zip(g,trace['peak_forced_v'])];direct=F(cell['metrics']['nodal_direct_v'][66])
        if sum(a,F(0))!=F(trace['node_anchor_v'][66]) or sum(f,F(0))+direct!=F(trace['node_forced_v'][66]):raise ValueError('exact 22-term nodal assembly required')
        bounds=[F(x)+F(y) for x,y in zip(trace['node_anchor_v'],trace['node_forced_v'])];node=max(range(94),key=bounds.__getitem__)
        rows.append(dict(cell_index=cell['index'],left=trace['left'],right=trace['right'],peak_node_index=node,peak_v=str(bounds[node]),
            node66_anchor_terms_v=list(map(str,a)),node66_forced_terms_v=list(map(str,f)),node66_direct_v=str(direct),
            node66_anchor_v=trace['node_anchor_v'][66],node66_forced_v=trace['node_forced_v'][66],dominant_forced_group=max(range(22),key=f.__getitem__)))
    peak=max(range(len(rows)),key=lambda j:F(rows[j]['peak_v']))
    return dict(rows=rows,peak_cell_index=peak,peak_node_index=rows[peak]['peak_node_index'],local_peak_v=rows[peak]['peak_v'],physical_cause_identified=False,independent_remainders_cancelled=False)


def generate():
    sys.set_int_max_str_digits(0)
    destinations=[OUTPUT,SUMMARY,LAUNCH,*[artifact_path('support',n) for n in PARTITIONS],*[artifact_path('cell',n,k) for n in PARTITIONS for k in range(n)]]
    if any(p.exists() or p in PATHS for p in destinations) or len(set(destinations))!=len(destinations):raise ValueError('fresh distinct destinations required; preserve attempts')
    before=hashes(PATHS);env=environment();old=read(ancestor.OUTPUT)
    rec=ancestor.load_artifact(old['variants'][0]['records'][0]['storage'],'interval',32,8)['record']
    left_template=ancestor.load_artifact(old['templates'][0]['storage'],'template',32)
    template=ancestor.load_artifact(old['templates'][1]['storage'],'template',33)
    block_storage=old['variants'][3]['blocks'][1]['storage'];block=ancestor.load_artifact(block_storage,'block',1,1)['block']
    previous,metric,left,end=source(old,rec,left_template,template,block)
    network=prior.constructor.CompensatedBdfNetwork(200,prior.constructor.model_parameters(1,'finite_transit'))
    graph=read(prior.graph_source.OUTPUT)['graph'];startup=read(prior.startup_source.OUTPUT)
    item=ancestor.unpack_template(network,startup,template,old['templates'][1]['storage']);prepared=item['prepared']
    weights=list(map(F,old['weights']));scales=list(map(F,old['descriptor_scales']))
    inverse=reconstruct_inverse(network,graph,item,block,scales)
    provider=ancestor.prepared_action;context=provider.prepare(block['candidate_inverse_binary'],scales,block['cover'])
    if block['action_preparation']!=dict(input_sha256=context.input_sha256,state_sha256=context.state_sha256,n=context.n):raise ValueError('same certified context and seal required')
    interface=law.real.continuity(network,left,prepared,end,F(template['start_s']))
    variants=[];derived={};final=previous;certified_end=end;selected=None;budgets=0;actions=0
    for n in PARTITIONS:
        cells=[];rows=[]
        for k in range(n):
            data=build_cell(network,graph,prepared,inverse,block,weights,scales,metric,context,provider,n,k,before)
            if hashes(PATHS)!=before:raise ValueError('inputs changed before cell archival')
            storage=store(data,artifact_path('cell',n,k));derived[storage['path']]=storage['compressed_sha256']
            rows.append(dict(index=k,left=data['left'],right=data['right'],rhs_sha256=data['cell']['rhs_sha256'],storage=storage));cells.append(data['cell'])
            budgets+=1;actions+=len(data['cell']['action']['subcells'])
            print(json.dumps(dict(partition=n,cell=k,physical_duration_s=data['rhs']['duration_s'],artifact_complete=True)),flush=True)
        result=law.blocks.close(cells,law.transfer(previous),RADIUS,F(previous['peak_node_error_upper_v']))
        record=dict(interval_index=INDEX,start_s=template['start_s'],end_s=template['end_s'],incoming_certified_result_sha256=law.digest(previous),
            incoming_block_error_upper_v=law.transfer(previous),incoming_node_error_upper_v=previous['peak_node_error_upper_v'],incoming_metric_sha256=law.digest(metric),
            prepared_sha256=template['prepared_sha256'],source_storage=old['templates'][1]['storage'],interface=interface,
            trials=[dict(radius_v=str(RADIUS),cells=cells,result=result)],selected_trial_index=0 if result['accepted'] else None)
        admitted=law.admit(previous,end,record);diag=diagnostic(record)
        packed_record=record|dict(trials=[record['trials'][0]|dict(cells=rows)])
        support=dict(schema=f'{SCHEMA}-support/v1',source_sha256=before|derived,partition=n,interval_index=INDEX,
            record=packed_record,diagnostic=diag,full_result_sha256=law.digest(result))
        if hashes(PATHS)!=before:raise ValueError('inputs changed before support archival')
        storage=store(support,artifact_path('support',n));derived[storage['path']]=storage['compressed_sha256']
        variants.append(dict(partition=n,cells=rows,storage=storage,accepted=result['accepted'],local_peak_v=diag['local_peak_v'],
            peak_node_error_upper_v=result['peak_node_error_upper_v'],full_result_sha256=law.digest(result),peak_cell_index=diag['peak_cell_index'],peak_node_index=diag['peak_node_index']))
        print(json.dumps(dict(partition=n,accepted=admitted is not None,local_peak_v=float(F(diag['local_peak_v'])),reason=result['reason'])),flush=True)
        if admitted is not None:selected=len(variants)-1;final,certified_end=admitted;break
    historical=ancestor.load_artifact(old['variants'][3]['records'][1]['storage'],'interval',33,1)['record']
    if hashes(PATHS)!=before:raise ValueError('refinement inputs changed')
    return dict(schema=f'{SCHEMA}/v1',environment=env,source_sha256=before|derived,producer_source_sha256=before,
        source_selected_variant_index=0,source_selected_trial_index=1,source_interval_index=32,source_accepted_intervals=33,
        source_certified_result_sha256=law.digest(previous),historical_control_incoming_sha256=historical['incoming_certified_result_sha256'],
        same_historical_control_incoming=historical['incoming_certified_result_sha256']==law.digest(previous),
        source_block_storage=block_storage,source_template_storage=old['templates'][1]['storage'],source_left_template_storage=old['templates'][0]['storage'],
        prepared_sha256=template['prepared_sha256'],partition_order=list(PARTITIONS),radius_v=str(RADIUS),initial_certified_end_s=str(end),attempted_end_s=template['end_s'],
        fixed_metric=metric,metric_sha256=law.digest(metric),weights=old['weights'],descriptor_scales=old['descriptor_scales'],groups=old['groups'],
        variants=variants,selected_variant_index=selected,accepted_intervals_total=33+(selected is not None),
        continuous_actual_error_certified_duration_s=str(certified_end),final_certified_result=final,first_gap_index=33 if selected is None else None,
        stop_reason='declared_first_closure' if selected is not None else 'all_partitions_rejected',
        new_budget_calls=budgets,new_action_subcell_certificates=actions,new_prepared_contexts=1,
        reused_inverse_enclosures=1,inverse_reconstructions=1,reused_rate_certificates=1,reused_rate_queries=sum(len(v['probes']) for v in block['rate_certificate'].values()),
        new_nonlinear_solves=0,new_preconditioners=0,new_inverse_certificates=0,new_rate_queries=0,new_metric_systems=0,
        integer_text_limit_during=0,reference_changed=False,incoming_reset=False,clock_translation=False,junction_norm_changed=False,
        prior_reports_modified=False,original_integrator_modified=False,numerical_gates_changed=False,independent_remainders_cancelled=False,
        partial_artifacts_admitted=False,global_1mv_gate_closed=False,full_path_coverage=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT.exists() or SUMMARY.exists():raise ValueError('fresh manifest destinations required')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ('fixed_metric','final_certified_result')}
    summary.update(storage=storage,final_certified_result={k:v for k,v in report['final_certified_result'].items() if k!='propagation'})
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


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
        except BaseException as failure:traceback.print_exc();code=130 if isinstance(failure,KeyboardInterrupt) else 1
    after=hashes(PATHS)
    if before!=after:code=1
    receipt=dict(schema=f'{SCHEMA}-launch/v1',timestamp_utc=datetime.now(timezone.utc).isoformat(),environment=env,
        command=[sys.executable,'-B',str(Path(__file__).resolve())],exit_code=code,stdout=out.getvalue(),stderr=err.getvalue(),
        producer_source_utf8=Path(__file__).read_text(encoding='utf-8'),source_sha256=before,
        source_sha256_before=before,source_sha256_after=after,inputs_unchanged=before==after,measurement_published=code==0 and OUTPUT.exists() and SUMMARY.exists())
    LAUNCH.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return code


if __name__=='__main__':sys.exit(run())
