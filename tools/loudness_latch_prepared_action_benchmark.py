"""Frozen, balanced full-certificate offline preparation experiment."""
from datetime import datetime,timezone
from pathlib import Path
from time import perf_counter_ns,process_time_ns
import hashlib,json,platform,statistics,sys,traceback
import loudness_latch_bdf_static_precision_shared_continuation as source
import loudness_latch_prepared_action as prepared
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
ROOT=source.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_prepared_action_benchmark.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_prepared_action_benchmark_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_ACCIONES_PREPARADAS_PROTOCOLO.md'


def paths(manifest):
    return tuple(dict.fromkeys((*(ROOT/p for p in manifest['source_sha256']),source.OUTPUT,source.SUMMARY,
        *(ROOT/'evidence'/p for p in ('loudness_latch_bdf_static_precision_shared_continuation_validation.json',
        'loudness_latch_bdf_static_precision_shared_continuation_inputs.json.gz',
        'loudness_latch_bdf_static_precision_shared_continuation_inputs_summary.json',
        'loudness_latch_bdf_static_precision_shared_continuation_inputs_validation.json')),
        ROOT/'tools/loudness_latch_prepared_action.py',Path(__file__).resolve(),PROTOCOL)))


def bank(manifest):
    if manifest['schema']!='rf-d/bdf-static-shared-continuation/v1' or manifest['selected_variant_index']!=0 or manifest['accepted_intervals_total']!=24:
        raise ValueError('same twenty-four-support source required')
    v=manifest['variants'][0]
    if v['width']!=8 or v['first_gap_index'] is not None or len(v['blocks'])!=1 or len(v['records'])!=8:
        raise ValueError('complete width-eight source required')
    block=source.load_artifact(v['blocks'][0]['storage'],'block',0,8)['block']
    if block['support_indices']!=list(range(16,24)) or not block['inverse_certified']:raise ValueError('same certified block required')
    return v,block


def cases(manifest):
    v,block=bank(manifest)
    for k,row in enumerate(v['records'],16):
        if row['interval_index']!=k or row['selected_trial_index']!=1:raise ValueError('same accepted selected trial required')
        record=source.load_artifact(row['storage'],'interval',k,8)['record']
        template_row=manifest['templates'][k-16]
        template=source.load_artifact(template_row['storage'],'template',k)
        if template['prepared_sha256']!=record['prepared_sha256'] or not record['trials'][1]['result']['accepted']:
            raise ValueError('same complete accepted curve required')
        cells=record['trials'][1]['cells']
        if len(cells)!=8 or len(template['rhs'])!=8:raise ValueError('eight complete macro cells required')
        for j,(cell,rhs) in enumerate(zip(cells,template['rhs'])):
            if cell['rhs_sha256']!=source.law.digest(rhs):raise ValueError('same signed RHS identity required')
            yield k,j,row['storage'],template_row['storage'],rhs,cell['action']


def timed(call):
    wall=perf_counter_ns();cpu=process_time_ns();value=call()
    return value,dict(wall_ns=perf_counter_ns()-wall,cpu_ns=process_time_ns()-cpu)


def aggregates(rows,setup):
    result={}
    for label in ('reference','prepared'):
        w=[r['timings'][label]['wall_ns'] for r in rows];c=[r['timings'][label]['cpu_ns'] for r in rows]
        result[label]=dict(calls=len(w),wall_total_ns=sum(w),cpu_total_ns=sum(c),wall_median_ns=statistics.median(w) if w else None,
            by_order={order:dict(calls=sum(r['order']==order for r in rows),
                wall_total_ns=sum(r['timings'][label]['wall_ns'] for r in rows if r['order']==order)) for order in ('AB','BA')})
    total=result['prepared']['wall_total_ns']+setup.get('wall_ns',0)
    result['prepared_including_setup_wall_ns']=total
    result['reference_over_prepared_including_setup']=result['reference']['wall_total_ns']/total if total else None
    return result


def generate():
    sys.set_int_max_str_digits(0)
    if OUTPUT.exists() or SUMMARY.exists():raise ValueError('fresh outputs required; preserve prior attempts')
    manifest=source.read(source.OUTPUT);inputs=paths(manifest);before=hashes(inputs);v,block=bank(manifest)
    env=environment()|dict(processor=platform.processor(),clock='perf_counter_ns; process_time_ns',arithmetic='exact Fraction; directed 256-bit dyadic endpoints')
    rows=[];setup={};failures=[];mismatch=[];derived={};state=None
    try:
        state,setup=timed(lambda:prepared.prepare(block['candidate_inverse_binary'],manifest['descriptor_scales'],block['cover']))
        for index,(k,j,record_storage,template_storage,rhs,golden) in enumerate(cases(manifest)):
            order='AB' if index%2==0 else 'BA';values={};timings={}
            calls=dict(reference=lambda:prepared.reference.budgets(block['candidate_inverse_binary'],manifest['descriptor_scales'],block['cover'],rhs,manifest['weights'],manifest['fixed_metric']),
                prepared=lambda:prepared.budgets(state,block['candidate_inverse_binary'],manifest['descriptor_scales'],block['cover'],rhs,manifest['weights'],manifest['fixed_metric']))
            for label in (('reference','prepared') if order=='AB' else ('prepared','reference')):
                values[label],timings[label]=timed(calls[label])
            raw={label:canonical(value) for label,value in values.items()};raw['archived']=canonical(golden)
            equal=raw['reference']==raw['prepared']==raw['archived']
            row=dict(interval_index=k,cell_index=j,order=order,record_storage=record_storage,template_storage=template_storage,
                rhs_sha256=source.law.digest(rhs),timings=timings,canonical_bytes={label:len(value) for label,value in raw.items()},
                certificate_sha256={label:hashlib.sha256(value).hexdigest() for label,value in raw.items()},complete_bytes_identical=equal)
            rows.append(row)
            print(json.dumps(dict(interval=k,cell=j,order=order,equal=equal,wall_s={label:t['wall_ns']/1e9 for label,t in timings.items()})),flush=True)
            if not equal:
                target=ROOT/f'evidence/loudness_latch_prepared_action_mismatch_{k:03d}_{j:02d}.json.gz'
                if target.exists():raise ValueError('fresh mismatch destination required')
                storage=store(dict(schema='rf-d/prepared-action-mismatch/v1',source_sha256=before,case=row,certificates=values|dict(archived=golden)),target)
                mismatch.append(storage);derived[storage['path']]=storage['compressed_sha256']
                raise ValueError('complete canonical certificate mismatch')
    except Exception:
        failures.append(dict(traceback=traceback.format_exc(),producer_source_utf8=Path(__file__).read_text(encoding='utf-8'),
            helper_source_utf8=(ROOT/'tools/loudness_latch_prepared_action.py').read_text(encoding='utf-8')))
    after=hashes(inputs);accepted=not failures and before==after and len(rows)==64 and all(r['complete_bytes_identical'] for r in rows)
    return dict(schema='rf-d/prepared-action-benchmark/v1',timestamp_utc=datetime.now(timezone.utc).isoformat(),environment=env,
        source_sha256=before|derived,source_sha256_before=before,source_sha256_after=after,inputs_unchanged=before==after,
        source_selected_variant_index=0,source_selected_trial_index=1,width=8,interval_indices=list(range(16,24)),rounds=1,
        order_policy='AB-even-flat-index; BA-odd-flat-index',setup=setup,prepared_input_sha256=state.input_sha256 if state else None,
        prepared_state_sha256=state.state_sha256 if state else None,rows=rows,aggregates=aggregates(rows,setup),
        preparation_count=int(state is not None),reference_budget_calls=len(rows),prepared_budget_calls=len(rows),
        reference_action_subcells=8*len(rows),prepared_action_subcells=8*len(rows),failures=failures,mismatch_artifacts=mismatch,
        accepted=accepted,integer_text_limit_during=0,accepted_intervals_total=manifest['accepted_intervals_total'],
        continuous_actual_error_certified_duration_s=manifest['continuous_actual_error_certified_duration_s'],
        time_coverage_extended=False,prior_reports_modified=False,numerical_gates_changed=False,reference_helper_changed=False,
        new_nonlinear_solves=0,new_inverse_enclosures=0,new_rate_ldlt_queries=0,global_1mv_gate_closed=False,audio_admitted=False,
        native_implementation_admitted=False,deadline_proven=False)


def save(report):
    storage=store(report,OUTPUT)
    SUMMARY.write_text(json.dumps(report|dict(storage=storage),indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return report


if __name__=='__main__':
    result=save(generate());print(json.dumps(dict(accepted=result['accepted'],cells=len(result['rows']),aggregates=result['aggregates'])),flush=True)
    sys.exit(0 if result['accepted'] else 1)
