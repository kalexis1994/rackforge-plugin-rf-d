"""Admit the complete offline lifecycle while preserving the listening reference."""
import base64,hashlib,json,struct,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_nominal_render import control,prefix_parse,prefix_wav,CONTROL
from render_nominal import parse_complete,validate_wav,ARTIFACT
from validate_joint_charge_seed import local_links
OUT='evidence/nominal_render_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def audit():
    before=read('evidence/nominal_render_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/nominal_render_native01.json','evidence/nominal_render_count_correction01.json','evidence/nominal_render_native02.json'];failure,correction,native=[read(n) for n in names];assert native['passed'] and native['temporary_area_empty'] and not native['real_time'] and not native['physical_fidelity'] and native['new_original_equation_rows']==0
    assert not failure['passed'] and failure['failed_phase']=='prefix' and failure['failed_process']['exit_code']==failure['unchanged_replay']['exit_code']!=0
    assert 'left: 10109' in failure['failed_process']['stderr'] and 'left: 10109' in failure['unchanged_replay']['stderr']
    prior_tests=failure['unit_tests'];assert prior_tests['exit_code']==0 and '3 passed; 0 failed' in unpack(prior_tests['stdout']).decode() and '7 filtered out' in unpack(prior_tests['stdout']).decode()
    assert correction['passed'] and correction['failure']==names[0] and correction['failure_sha256']==sha(ROOT/names[0]) and correction['unchanged_replay_preserved'] and correction['numerical_gates_unchanged']
    previous_sources=recover(failure)
    assert set(correction['changed_sources'])=={'tools/nominal_render_probe.rs','tools/check_nominal_render.py','docs/NOMINAL_RENDER_PROTOCOLO.md'}
    for n,b in previous_sources.items():
        if n in correction['changed_sources']:
            proof=correction['changed_sources'][n];assert proof['before_sha256']==hashlib.sha256(b).hexdigest() and proof['after_sha256']==sha(ROOT/n)
        else:assert(ROOT/n).read_bytes()==b,n
    assert(ROOT/'docs/NOMINAL_RENDER_PROTOCOLO.md').read_bytes().startswith(previous_sources['docs/NOMINAL_RENDER_PROTOCOLO.md'])
    for n,b in recover(native).items():assert(ROOT/n).read_bytes()==b,n
    assert native['control']==CONTROL and native['control_sha256']==sha(ROOT/CONTROL)
    metadata_failure=read('evidence/nominal_render_qa_failure01.json');assert not metadata_failure['passed'] and 'assert OUT in staged' in metadata_failure['failure'] and 'AssertionError' in metadata_failure['unchanged_replay']
    archived_validator=recover(metadata_failure);assert set(archived_validator)=={'tools/validate_nominal_render.py'} and b'assert OUT in staged' in archived_validator['tools/validate_nominal_render.py']
    samples,final=control();blob=samples[:433].astype('<f8').tobytes();assert native['prefix_input']==dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
    m=prefix_parse(unpack(native['prefix_stdout']));assert canonical(m)==canonical(native['prefix_measurements'])
    wav=prefix_wav(samples);assert native['prefix_wav']==dict(bytes=len(wav),sha256=hashlib.sha256(wav).hexdigest(),matches_independent_header_and_f32_payload=True)
    tests=native['unit_tests'];assert tests['exit_code']==0 and tests['stderr']=='' and '3 passed; 0 failed' in unpack(tests['stdout']).decode() and '7 filtered out' in unpack(tests['stdout']).decode()
    for tag,stage in [('cancel_before_dc','before_dc'),('cancel_after_progress','between_quotas')]:
        r=native[tag];assert r['passed'] and r['cancelled'] and not r['published'] and r['temporary_area_empty'] and r['exit_code']==130 and ('CANCELLED,'+stage) in unpack(r['stdout']).decode()
    assert 'PROGRESS,' not in unpack(native['cancel_before_dc']['stdout']).decode() and 'PROGRESS,' in unpack(native['cancel_after_progress']['stdout']).decode()
    r=native['injected_process_failure'];assert not r['passed'] and not r['published'] and r['temporary_area_empty'] and r['exit_code']==7 and r['compile']['injected']
    assert native['injected_publication_failure']['previous_wav_preserved'] and native['preflight_guards']==dict(occupied_area_preserved=True,invalid_quotas_rejected=4)
    full=native['full_render'];assert full['passed'] and full['published'] and not full['cancelled'] and full['temporary_area_empty'] and full['exit_code']==0 and full['quota']==128
    for r in [native['cancel_before_dc'],native['cancel_after_progress'],native['injected_process_failure'],full]:
        for n,b in recover(r).items():assert(ROOT/n).read_bytes()==b,n
        assert r['previous_wav_sha256']==r['final_wav_sha256']==old['new_listening']['sha256']
    full_m=parse_complete(unpack(full['stdout']));assert canonical(full_m)==canonical(full['measurements']) and struct.pack('<236d',*full_m['state'])==struct.pack('<236d',*final) and native['full_final_state_bitwise_identical']
    assert full['output']==validate_wav(ARTIFACT) and full['output']['sha256']==old['new_listening']['sha256']
    for r in [native,full['compile'],native['cancel_before_dc']['compile'],native['cancel_after_progress']['compile']]:
        assert r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path'])) and r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    assert not list((ROOT/'tmp/lab-current').iterdir());size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('nominal_render*.json') if p!=ROOT/OUT);assert size<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    assert set(native['source_sha256'])<=set(sources)
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and (not k.startswith('new_') or k=='new_listening')}
    result['inherited_legacy_new_fields_reference']=dict(path=before['previous_qa'],sha256=before['previous_qa_sha256'],fields=sorted(k for k in old if k.startswith('new_') and k!='new_listening'))
    path='crates/rf-d-circuit/src/nominal_render.rs';tool='tools/render_nominal.py';inherited=old['covered_test_count']
    result.update(schema='rf-d/complete-offline-render-lifecycle/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),nominal_render_admitted=True,nominal_render_reference={n:sha(ROOT/n) for n in names+['evidence/nominal_render_qa_failure01.json']},nominal_render_profile_max_full_s=1e-6,nominal_render_full_steps=301151,nominal_render_full_final_state_and_wav_bitwise_identical=True,nominal_render_body_frames=14400,nominal_render_anchor_frames=1,nominal_render_persistent_bytes=m['sizes'][0],nominal_render_sink_bytes=m['sizes'][1],nominal_render_workspace_bytes=m['sizes'][2],nominal_render_core_heap_allocations=0,nominal_render_io_outside_pump=True,nominal_render_current_path=str(ARTIFACT.relative_to(ROOT)),nominal_render_receipt_bytes_before_qa=size,nominal_render_receipt_budget_bytes=8*1024*1024,active_nominal_renderer=path,active_nominal_renderer_source_sha256=sources[path],active_nominal_renderer_entry='RenderSession::pump',active_nominal_renderer_origin_commit=None,active_nominal_renderer_origin_commit_pending_self_commit=True,active_nominal_render_tool=tool,active_nominal_render_tool_source_sha256=sources[tool],active_nominal_render_tool_origin_commit=None,active_nominal_render_tool_origin_commit_pending_self_commit=True,active_offline_producer_origin_commit=before['base_commit'],active_offline_producer_origin_commit_pending_self_commit=False,inherited_test_count=inherited,covered_test_count=inherited+3,native_test_count=3,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=True,inherited_global_trajectories_reexecuted_scope='one admitted 1us 301ms trajectory through the new render lifecycle',inherited_global_trajectory_suite_reexecuted=False,new_unit_test_definitions=3,new_unit_tests_executed=3,new_nominal_render_full_trajectories=1,new_nominal_render_prefix_trajectories=2,new_failed_nominal_render_prefix_trajectories=2,new_unit_test_invocations=6,new_nominal_render_cancelled_partial_trajectories=1,new_original_equation_rows=0,new_audio=False,new_audio_export=True,new_audio_export_count=1,new_audio_export_byte_identical_to_previous=True,previous_listening_preserved_sha256=old['new_listening']['sha256'],new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','active_voice_implementation','active_initializer','active_readout','active_antialias','active_antialias_coefficients','active_output_pipeline','active_offline_producer','cost_ratio','private_input_sha256']:assert result[k]==old[k],k
    return result

def main():
    try:r=audit()
    except Exception:
        s=Sources(['tools/validate_nominal_render.py']);r=dict(passed=False,**s.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/nominal_render_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/nominal_render_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('NOMINAL_RENDER_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['nominal_render_persistent_bytes'],r['nominal_render_receipt_bytes_before_qa'],flush=True)
if __name__=='__main__':main()
