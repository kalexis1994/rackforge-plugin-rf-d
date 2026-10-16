"""Admit only the tested experimental Hz program, preserving the nominal engine."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_pitch_program import analyse,controls,CONTROL
from prepare_pitch_program import images
from validate_joint_charge_seed import local_links
OUT='evidence/pitch_program_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def audit():
    before=read('evidence/pitch_program_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    generated=images()
    for n,s in generated.items():assert(ROOT/n).read_bytes()==s.encode(),n
    prep=read('evidence/pitch_program_preparation_failure01.json');raw=base64.b64decode(prep['source_base64']);assert not prep['passed'] and prep['unchanged_replay']['exit_code']!=0 and 'SyntaxError' in prep['unchanged_replay']['stderr'] and hashlib.sha256(raw).hexdigest()==prep['source_sha256']
    try:compile(raw.decode('utf8'),prep['source_path'],'exec');raise AssertionError('expected archived syntax failure')
    except SyntaxError:pass
    names=sorted(p.relative_to(ROOT).as_posix() for p in(ROOT/'evidence').glob('pitch_program_native*.json'));assert names
    records=[read(n) for n in names];native=records[-1];assert native['passed'] and native['temporary_area_empty'] and not native['real_time'] and not native['physical_fidelity'] and not native['physical_cv_model'] and not native['new_audio'] and native['new_original_equation_rows']==0
    for n,b in recover(native).items():assert(ROOT/n).read_bytes()==b,n
    correction=read('evidence/pitch_program_capacity_correction01.json');assert correction['passed'] and correction['numerical_gates_unchanged'] and correction['unchanged_replay_preserved'] and correction['failure_sha256']==sha(ROOT/correction['failure'])
    original_probe=recover(read(correction['failure']))[correction['changed_path']];assert hashlib.sha256(original_probe).hexdigest()==correction['before_sha256'] and sha(ROOT/correction['changed_path'])==correction['after_sha256']
    assert original_probe.count(correction['replace_before'].encode())==1 and original_probe.replace(correction['replace_before'].encode(),correction['replace_after'].encode(),1)==(ROOT/correction['changed_path']).read_bytes()
    streams=[]
    for r in records:
        if 'stdout' in r:streams.append(unpack(r['stdout']))
        elif 'failed_process' in r:streams.append(unpack(r['failed_process']['stdout']))
        if isinstance(r.get('unchanged_replay'),dict):streams.append(unpack(r['unchanged_replay']['stdout']))
    nominal_trajectories=2*sum(raw.count(b'NOMINAL,') for raw in streams)
    complete_program_receipts=sum(raw.count(b'SEQUENCE,') for raw in streams)
    decision=read('evidence/pitch_program_refinement_decision01.json');assert decision['passed'] and decision['unchanged_numerical_gates'] and decision['unchanged_gate_replay_preserved'] and decision['failed_comparison_sha256']==sha(ROOT/decision['failed_comparison']) and decision['gates']==dict(rms_relative=.001,peak_relative=.003,mean_error_v=1e-6)
    assert decision['coarse_fine_ticks']==[1048576,524288] and decision['next_comparison_ticks']==native['profiles_ticks']==[524288,262144] and native['refined']
    assert not decision['measurements']['retune_up']['passed'] and decision['measurements']['retune_up']['rms_relative']>.001
    archived_differences={}
    for path,r in zip(names[:-1],records[:-1]):
        assert not r['passed'] and r['temporary_area_empty']
        if r['failed_phase']=='analysis':
            assert 'unchanged_gate_replay' in r
            try:analyse(unpack(r['stdout']));raise AssertionError('archived failure unexpectedly passes')
            except AssertionError as e:assert str(e)!='archived failure unexpectedly passes'
        else:assert r['failed_process']['exit_code']==r['unchanged_replay']['exit_code']!=0
        differences={n:dict(archived_sha256=hashlib.sha256(b).hexdigest(),current_sha256=sha(ROOT/n)) for n,b in recover(r).items() if(ROOT/n).read_bytes()!=b}
        assert set(differences)<={'tools/pitch_program_probe.rs','tools/check_pitch_program.py'},differences;archived_differences[path]=differences
    assert native['control']==CONTROL and native['control_sha256']==sha(ROOT/CONTROL)
    expected={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in controls().items()};assert native['input_images']==expected
    a=analyse(unpack(native['stdout']));assert canonical(a)==canonical(native['analysis']);assert [s[1] for s in a['measurements']['sequences']]==native['profiles_ticks']
    tests=native['unit_tests'];assert tests['exit_code']==0 and tests['stderr']=='' and '4 passed; 0 failed' in unpack(tests['stdout']).decode() and '6 filtered out' in unpack(tests['stdout']).decode()
    assert native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path'])) and native['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'];assert not list((ROOT/'tmp/lab-current').iterdir())
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('pitch_program*.json') if p!=ROOT/OUT);assert size<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    assert set(native['source_sha256'])<=set(sources)
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and (not k.startswith('new_') or k=='new_listening')}
    result['inherited_legacy_new_fields_reference']=dict(path=before['previous_qa'],sha256=before['previous_qa_sha256'],fields=sorted(k for k in old if k.startswith('new_') and k!='new_listening'))
    path='crates/rf-d-circuit/src/pitch_program_producer.rs';phase='crates/rf-d-circuit/src/pitch_phase_source.rs';inherited=old['covered_test_count']
    result.update(schema='rf-d/experimental-pitch-program/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_pitch_program_admitted=True,experimental_pitch_program_scope='nominal-cycle Hz transposition; numerical qualification only for tested scenes; no physical CV calibration',experimental_pitch_program_reference={n:sha(ROOT/n) for n in names+['evidence/pitch_program_preparation_failure01.json','evidence/pitch_program_capacity_correction01.json','evidence/pitch_program_refinement_decision01.json']},experimental_pitch_archived_adapter_source_differences=archived_differences,experimental_pitch_nominal_steps=10109,experimental_pitch_nominal_states_stages_raw_and_frames_bitwise_identical=True,experimental_pitch_generated_bindings={n:sha(ROOT/n) for n in generated},experimental_pitch_phase_decimal=a['decimal_phase'],experimental_pitch_frequency_ratios_tested=[1.,1.5,.5],experimental_pitch_key_on_s=.001,experimental_pitch_key_off_s=.01875,experimental_pitch_sequence_duration_s=.024,experimental_pitch_output_body_duration_s=.023,experimental_pitch_temporal_refinement=a['temporal_refinement'],experimental_pitch_rate_refinement=a['rate_refinement'],experimental_pitch_selected_maximum_ticks=int(native['profiles_ticks'][1]),experimental_pitch_persistent_bytes=int(a['measurements']['sizes'][0]),experimental_pitch_program_bytes=int(a['measurements']['sizes'][1]),experimental_pitch_workspace_bytes=int(a['measurements']['sizes'][2]),experimental_pitch_heap_allocations=0,experimental_pitch_receipt_bytes_before_qa=size,experimental_pitch_receipt_budget_bytes=8*1024*1024,experimental_pitch_producer=path,experimental_pitch_producer_source_sha256=sources[path],experimental_pitch_source=phase,experimental_pitch_source_sha256=sources[phase],experimental_pitch_origin_commit=None,experimental_pitch_origin_commit_pending_self_commit=True,active_nominal_renderer_origin_commit=before['base_commit'],active_nominal_renderer_origin_commit_pending_self_commit=False,active_nominal_render_tool_origin_commit=before['base_commit'],active_nominal_render_tool_origin_commit_pending_self_commit=False,inherited_test_count=inherited,covered_test_count=inherited+4,native_test_count=4,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=False,inherited_global_trajectories_reexecuted_scope='none; only short prefixes and experimental programs',inherited_global_trajectory_suite_reexecuted=False,new_unit_test_definitions=4,new_unit_tests_executed=4,new_unit_test_invocations=4*sum('unit_tests' in r for r in records),new_nominal_pitch_prefix_trajectories=nominal_trajectories,new_experimental_pitch_sequence_trajectories=complete_program_receipts,new_original_equation_rows=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,previous_listening_preserved_sha256=old['new_listening']['sha256'],new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,physical_cv_model=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','active_voice_implementation','active_initializer','active_readout','active_antialias','active_antialias_coefficients','active_output_pipeline','active_offline_producer','active_nominal_renderer','active_nominal_render_tool','cost_ratio','private_input_sha256']:assert result[k]==old[k],k
    return result

def main():
    try:r=audit()
    except Exception:
        s=Sources(['tools/validate_pitch_program.py']);r=dict(passed=False,**s.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/pitch_program_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/pitch_program_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('PITCH_PROGRAM_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_pitch_selected_maximum_ticks'],r['experimental_pitch_receipt_bytes_before_qa'],flush=True)
if __name__=='__main__':main()
