"""Admit the long experimental scene and explicitly migrate its regenerable view."""
import ast,base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_pitch_render import analyse
from prepare_pitch_render import images
from prepare_pitch_render_tool import image
from export_pitch_render import prepare,REFERENCE
from validate_joint_charge_seed import local_links
OUT='evidence/pitch_render_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))

def audit():
    before=read('evidence/pitch_render_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    for n,s in images().items():assert(ROOT/n).read_bytes()==s.encode(),n
    assert(ROOT/'tools/render_pitch.py').read_bytes()==image().encode()
    # Exact inheritance of IO bytes and body/anchor collection, not a duplicate test claim.
    nominal=(ROOT/'crates/rf-d-circuit/src/nominal_render.rs').read_text(encoding='utf8');derived=(ROOT/'crates/rf-d-circuit/src/pitch_program_render.rs').read_text(encoding='utf8')
    assert nominal[nominal.index('fn invalid()'):nominal.index('#[cfg(test)]')]==derived[derived.index('fn invalid()'):]
    assert nominal[nominal.index('    fn collect('):nominal.index('    /// No IO')]==derived[derived.index('    fn collect('):derived.index('    /// No IO')]
    names=sorted(p.relative_to(ROOT).as_posix() for p in(ROOT/'evidence').glob('pitch_render_native*.json'));assert len(names)==2
    failed,native=[read(n) for n in names];assert not failed['passed'] and failed['failed_phase']=='compile' and failed['failed_process']['exit_code']==failed['unchanged_replay']['exit_code']!=0 and failed['temporary_area_empty']
    correction=read('evidence/pitch_render_api_correction01.json');assert correction['passed'] and correction['numerical_gates_unchanged'] and correction['unchanged_compile_replay_preserved'] and correction['failure_sha256']==sha(ROOT/correction['failure'])
    archived=recover(failed);path=correction['changed_path'];b=archived[path];assert hashlib.sha256(b).hexdigest()==correction['before_sha256'] and sha(ROOT/path)==correction['after_sha256'];assert b.count(correction['replace_before'].encode())==1 and b.replace(correction['replace_before'].encode(),correction['replace_after'].encode(),1)==(ROOT/path).read_bytes()
    for name in ['parse_complete','parse','windows','analyse']:
        def function(source):return next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert ast.dump(function(archived['tools/check_pitch_render.py']))==ast.dump(function((ROOT/'tools/check_pitch_render.py').read_bytes())),name
    prep=read('evidence/pitch_render_wrapper_preparation_failure01.json');raw=base64.b64decode(prep['source_base64']);assert not prep['passed'] and hashlib.sha256(raw).hexdigest()==prep['source_sha256'] and prep['unchanged_replay']['exit_code']!=0 and 'AssertionError: tools/nominal_render_main.rs' in prep['unchanged_replay']['stderr']
    full=base64.b64decode(prep['original_invocation_base64']);assert full.startswith(raw) and hashlib.sha256(full).hexdigest()==prep['original_invocation_sha256'] and prep['original_invocation_unchanged_replay']['exit_code']!=0 and 'AssertionError: tools/nominal_render_main.rs' in prep['original_invocation_unchanged_replay']['stderr']
    assert native['passed'] and native['temporary_area_empty'] and not native['real_time'] and not native['physical_fidelity'] and not native['physical_cv_model'] and native['new_original_equation_rows']==0
    for n,b in recover(native).items():assert(ROOT/n).read_bytes()==b,n
    a=analyse(native['profiles']);assert canonical(a)==canonical(native['analysis'])
    tests=native['unit_tests'];assert tests['exit_code']==0 and tests['stderr']=='' and '1 passed; 0 failed' in unpack(tests['stdout']).decode()
    assert native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path'])) and native['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    listening=read(REFERENCE);data,expected=prepare(listening['native']);assert canonical(expected)==canonical(listening) and listening['previous_sha256']==old['new_listening']['sha256']
    assert(ROOT/listening['path']).read_bytes()==data and sha(ROOT/listening['path'])==listening['sha256'] and listening['path'] not in private
    publication=read('evidence/pitch_render_publication01.json');assert publication['passed'] and publication['published'] and publication['temporary_area_empty'] and publication['artifact_replaced_atomically'] and publication['previous_wav_sha256']==old['new_listening']['sha256'] and publication['output']['sha256']==listening['sha256'] and not publication['admitted_private_input_retired'] and not publication['third_long_history']
    for n,b in recover(publication).items():assert(ROOT/n).read_bytes()==b,n
    assert publication['negative_publication_controls']==['header','payload']
    for r in [publication['cancel_before_dc'],publication['cancel_after_progress']]:
        assert r['passed'] and r['cancelled'] and not r['published'] and r['temporary_area_empty'] and r['previous_wav_sha256']==r['final_wav_sha256']==old['new_listening']['sha256']
        for n,b in recover(r).items():assert(ROOT/n).read_bytes()==b,n
    assert not list((ROOT/'tmp/lab-current').iterdir())
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('pitch_render*.json') if p!=ROOT/OUT);assert size<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and not k.startswith('new_')}
    result['inherited_legacy_new_fields_reference']=dict(path=before['previous_qa'],sha256=before['previous_qa_sha256'],fields=sorted(k for k in old if k.startswith('new_')))
    result['experimental_pitch_render_profile_elapsed_s']=[p['elapsed_s'] for p in native['profiles']]
    core='crates/rf-d-circuit/src/pitch_program_render.rs';tool='tools/render_pitch.py';inherited=old['covered_test_count']
    result.update(schema='rf-d/experimental-long-pitch-render/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_pitch_origin_commit=before['base_commit'],experimental_pitch_origin_commit_pending_self_commit=False,experimental_pitch_renderer=core,experimental_pitch_renderer_source_sha256=sources[core],experimental_pitch_render_tool=tool,experimental_pitch_render_tool_source_sha256=sources[tool],experimental_pitch_renderer_origin_commit=None,experimental_pitch_renderer_origin_commit_pending_self_commit=True,experimental_pitch_render_reference={n:sha(ROOT/n) for n in names+[REFERENCE,'evidence/pitch_render_publication01.json','evidence/pitch_render_api_correction01.json','evidence/pitch_render_wrapper_preparation_failure01.json']},experimental_pitch_long_scene_admitted=True,experimental_pitch_long_scene_temporal_refinement=a['temporal_refinement'],experimental_pitch_long_scene_rate_refinement=a['rate_refinement'],experimental_pitch_long_scene_selected_maximum_ticks=262144,experimental_pitch_long_scene_body_s=.3,experimental_pitch_long_scene_electrical_end_s=.301,experimental_pitch_long_scene_retunes_s=[.1,.2],experimental_pitch_long_scene_key_off_s=.25,experimental_pitch_long_scene_heap_allocations=0,experimental_pitch_long_scene_stream_batch_bitwise_identical=True,experimental_pitch_long_scene_current_view_migration=dict(path=listening['path'],previous_sha256=old['new_listening']['sha256'],current_sha256=listening['sha256'],admitted_private_input_retired=False,previous_receipts_and_sources_preserved=True,previous_view_regenerable=True),experimental_pitch_render_generated_bindings={n:sha(ROOT/n) for n in [*images(),'tools/render_pitch.py']},experimental_pitch_render_sink_and_collector_bytes_identical=True,experimental_pitch_render_receipt_bytes_before_qa=size,experimental_pitch_render_receipt_budget_bytes=8*1024*1024,inherited_test_count=inherited,covered_test_count=inherited+1,native_test_count=1,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=False,inherited_global_trajectory_suite_reexecuted=False,new_unit_test_definitions=1,new_unit_tests_executed=1,new_unit_test_invocations=1,new_experimental_pitch_long_scene_trajectories=2,new_original_equation_rows=0,new_audio=True,new_audio_export=True,new_audio_export_count=1,new_listening=listening,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,physical_cv_model=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','active_voice_implementation','active_initializer','active_readout','active_antialias','active_antialias_coefficients','active_output_pipeline','active_offline_producer','active_nominal_renderer','active_nominal_render_tool','cost_ratio','private_input_sha256']:assert result[k]==old[k],k
    return result

def main():
    try:r=audit()
    except Exception:
        s=Sources(['tools/validate_pitch_render.py']);r=dict(passed=False,**s.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/pitch_render_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/pitch_render_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('PITCH_RENDER_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['covered_test_count'],r['experimental_pitch_render_receipt_bytes_before_qa'],flush=True)
if __name__=='__main__':main()
