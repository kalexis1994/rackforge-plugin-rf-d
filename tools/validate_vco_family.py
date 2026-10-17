"""Scope and source admission for the stationary CV/BUS laboratory family."""
import base64,hashlib,json,subprocess,traceback,shutil
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from prepare_vco_family import ORACLE,DATA,image
from vco_family_failure_archive import restore_bytes
from vco_family_receipts import read as receipt_read,logical_sha
from validate_joint_charge_seed import local_links
OUT='evidence/vco_family_tests01.json'
def read(n):return receipt_read(n)
def audit():
    before=read('evidence/vco_family_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(b) for n,b in before['mutable_original_b64'].items()}
    policy=read('evidence/vco_family_checkout_policy01.json');original=base64.b64decode(policy['original_b64']);assert policy['passed'] and policy['append_only'] and hashlib.sha256(original).hexdigest()==policy['original_sha256']==old['source_sha256']['.gitattributes'] and(ROOT/'.gitattributes').read_bytes()==original+policy['addition'].encode() and sha(ROOT/'.gitattributes')==policy['selected_sha256'];saved['.gitattributes']=original
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    assert len(old['private_input_sha256'])==8769 and all((ROOT/n).is_file() for n in old['private_input_sha256'])
    pre=read('evidence/vco_family_preflight_failure01.json');assert not pre['passed'] and not pre['numerical_work_started'] and pre['unchanged_replay']['exit_code']!=0 and b'ImportError' in unpack(pre['unchanged_replay']['stderr']);recover(pre)
    failed=read('evidence/vco_family_oracle01.json');assert not failed['passed'] and 'AssertionError' in failed['failure'] and 'AssertionError' in failed['unchanged_replay'] and failed['temporary_area_empty']
    storage=read('evidence/vco_family_failure_storage01.json');assert storage['passed'] and storage['all_original_pack_bytes_restored'] and hashlib.sha256(restore_bytes()).hexdigest()==failed['pack_sha256'] and not storage['sample_removal'] and not storage['quantization']
    for n,b in recover(storage).items():assert(ROOT/n).read_bytes()==b,n
    cor=read('evidence/vco_family_column_correction01.json');assert cor['gates_unchanged'] and cor['physical_equations_unchanged'] and cor['failure_sha256']==logical_sha(cor['failure'])
    for n,b in recover(failed).items():
        if n not in ['tools/check_vco_family.py','tools/vco_family.py']:assert(ROOT/n).read_bytes()==b,n
    r=read(ORACLE);assert r['passed'] and r['temporary_area_empty'] and len(r['training'])==8 and len(r['reserved'])==3 and len(r['method'])==2 and sha(ROOT/r['pack'])==r['pack_sha256']
    failed_export=read('evidence/vco_family_oracle02.json');assert not failed_export['passed'] and '256*1024**2' in failed_export['failure'] and '256*1024**2' in failed_export['unchanged_replay'] and len(failed_export['training'])==6
    assert sha(ROOT/failed_export['pack'])==failed_export['pack_sha256']
    reused=r['reused_training_reference'];assert reused['sha256']==logical_sha(reused['path']) and reused['count']==6
    for x,y in zip(r['training'][:6],failed_export['training']):assert json.dumps({k:v for k,v in x.items() if k!='window_pack'},sort_keys=True)==json.dumps(y,sort_keys=True)
    control=read('evidence/vco_family_binary_control01.json');assert control['passed'] and control['comparison']['passed'] and control['comparison']['bit_mismatches']==0
    for n,b in recover(control).items():assert(ROOT/n).read_bytes()==b,n
    binary=read('evidence/vco_family_binary_decision01.json');assert binary['export_budget_unchanged'] and binary['gates_unchanged'] and not binary['failure_export_exact_size_and_digest_retained']
    origin=(ROOT/binary['reader_origin']).read_text(encoding='utf8');derived=origin.replace("else 'current' if n.startswith('@') else None","else 'current' if n.startswith(('@','i(')) else None",1);assert(ROOT/binary['reader']).read_bytes()==derived.encode() and sha(ROOT/binary['reader_origin'])==binary['reader_origin_sha256']
    # The rejected high-CV ASCII deck and completed binary deck differ only in output commands.
    strip=lambda text:'\n'.join(line for line in text.splitlines() if not line.startswith(('wrdata ','write ','set filetype=')))
    assert strip(unpack(failed_export['failed_process']['deck']).decode())==strip(unpack(r['training'][6]['deck']).decode())
    for n,b in recover(r).items():assert(ROOT/n).read_bytes()==b,n
    for n,h in r['private_used_sha256'].items():assert sha(ROOT/n)==old['private_input_sha256'][n]==h
    for x in [*r['training'],*r['reserved'],*r['method']]:assert x['exit_code']==0 and x['elapsed_s']<=180 and x['export_bytes']<256*1024**2
    generation=read('evidence/vco_family_generation01.json');assert generation['passed'] and not generation['reserved_data_used'] and generation['reserved_sections_absent_identical_data'] and generation['data_sha256']==sha(ROOT/DATA) and generation['oracle_sha256']==logical_sha(ORACLE) and(ROOT/DATA).read_bytes()==image(r).encode()
    model=read('evidence/vco_family_model01.json');assert model['passed'] and model['rust_queries']==245 and model['invalid_domains_checked']==9 and model['heap_allocations_in_measured_queries']==0 and not model['reserved_data_used_for_fit'] and model['temporary_area_empty']
    assert model['oracle_sha256']==logical_sha(ORACLE) and len(model['held_out_bus_zero'])==4 and len(model['held_out_new'])==5 and len(model['held_out_archived'])==4
    assert all(x['panel_admitted'] for x in [*model['held_out_bus_zero'],*model['held_out_new']]) and not any(x['panel_admitted'] for x in model['held_out_archived'])
    assert len(model['negative_controls_rejected'])==3
    derivative=read('evidence/vco_family_derivative_diagnostic01.json');assert derivative['passed'] and derivative['gates_unchanged'] and derivative['candidate_unchanged'] and derivative['failure_sha256']==sha(ROOT/derivative['failure']) and derivative['step_convergence'][0]['max_scaled_error']>1 and derivative['step_convergence'][-1]['max_scaled_error']<1
    dense=read('evidence/vco_family_dense01.json');assert dense['passed'] and len(dense['cases'])==4 and sha(ROOT/dense['pack'])==dense['pack_sha256'] and dense['family_data_sha256']==sha(ROOT/DATA) and dense['temporary_area_empty']
    for n,b in recover(dense).items():assert(ROOT/n).read_bytes()==b,n
    for n,h in dense['private_used_sha256'].items():assert sha(ROOT/n)==old['private_input_sha256'][n]==h
    assert all(x['elapsed_s']<=180 and x['export_bytes']<256*1024**2 for x in dense['cases'])
    json_storage=read('evidence/vco_family_receipt_storage01.json');assert json_storage['passed'] and json_storage['lossless'] and not json_storage['numeric_changes']
    for name,x in json_storage['items'].items():assert logical_sha(name)==x['original_sha256'] and sha(ROOT/x['archive'])==x['archive_sha256']
    for n,b in recover(model).items():assert(ROOT/n).read_bytes()==b,n
    for p in sorted((ROOT/'evidence').glob('vco_family_model_failure*.json')):
        f=read(p.relative_to(ROOT).as_posix());assert not f['passed'] and 'failure' in f and 'unchanged_replay' in f;recover(f)
    assert not list((ROOT/'tmp/lab-current').iterdir()) and sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256']==r['current_listening_sha256']
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('vco_family*') if p.is_file() and p!=ROOT/OUT);assert size<=32*1024**2,size
    assert shutil.disk_usage(ROOT).free>1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and DATA in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    # Preserve active/inherited domains by identity, without repeating their long campaign.
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and (not k.startswith('new_') or k=='new_listening')}
    result.update(schema='rf-d/stationary-calibrated-cv-bus-family/v1',passed=True,base_commit=before['base_commit'],previous_qa=before['previous_qa'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),inherited_test_count=old['covered_test_count'],covered_test_count=old['covered_test_count'],inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,new_spice_trajectories=17,failed_spice_processes_with_replay=4,new_spice_export_controls=1,new_native_circuit_trajectories=0,new_rust_queries=245,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,physical_cv_general=False,experimental_vco_cv_load_origin_commit=before['base_commit'],experimental_vco_cv_load_origin_commit_pending_self_commit=False,experimental_stationary_family_origin_commit=None,experimental_stationary_family_origin_commit_pending_self_commit=True,experimental_stationary_family_data=DATA,experimental_stationary_family_kernel='tools/vco_family_kernel.rs',experimental_stationary_family_admitted=True,experimental_stationary_family_scope='Stationary calibrated CA3046 CV/BUS spectral family on declared fixed topology; seven held-out electrical locations; nine full spectral comparisons including method/refinement; no continuous-domain error certificate, dynamic CV or audible integration',experimental_stationary_family_training_count=8,experimental_stationary_family_reserved_locations=7,experimental_stationary_family_reserved_new_locations=3,experimental_stationary_family_reserved_comparisons=9,experimental_stationary_family_harmonics=64,experimental_stationary_family_worst_frequency_cents=max(x['frequency_error_cents'] for x in [*model['held_out_new'],*model['held_out_bus_zero']]),experimental_stationary_family_worst_panel_dc_a=max(x['panel_dc_error_a'] for x in [*model['held_out_new'],*model['held_out_bus_zero']]),experimental_stationary_family_worst_panel_ac_a=max(x['panel_harmonics_1_8_error_a'] for x in [*model['held_out_new'],*model['held_out_bus_zero']]),experimental_stationary_family_receipt_bytes=size,experimental_stationary_family_reference={n:sha(ROOT/n) for n in [ORACLE+'.gz',r['pack'],'evidence/vco_family_dense01.json','evidence/vco_family_dense_windows01.xz','evidence/vco_family_model01.json','evidence/vco_family_generation01.json']},experimental_stationary_family_heap_scope='245 valid and 9 invalid Rust queries instrumented; laboratory kernel not active voice',dynamic_cv_admitted=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['active_voice','active_voice_implementation','active_solver','active_initializer','active_readout','active_antialias','active_antialias_coefficients','active_output_pipeline','active_offline_producer','active_nominal_renderer','active_nominal_render_tool','experimental_pitch_producer','experimental_pitch_renderer','experimental_pitch_render_tool','new_listening','private_input_sha256']:assert result[key]==old[key],key
    return result
def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_vco_family.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/vco_family_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/vco_family_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('FAMILY_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_stationary_family_receipt_bytes'])
if __name__=='__main__':main()
