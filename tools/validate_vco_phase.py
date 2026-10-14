"""Promote a scoped phase prototype; preserve catalogs and bounded failed evidence."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from compact_vco_phase_failures import decoded
from validate_joint_charge_seed import local_links
OUT='evidence/vco_phase_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def identity(r):
    snapshots=r.get('executed_source_base64',r.get('failed_source_base64',{}))
    for n,h in r['source_sha256'].items():
        if sha(ROOT/n)!=h:assert n in snapshots and hashlib.sha256(base64.b64decode(snapshots[n])).hexdigest()==h,n
def main():
    before=read('evidence/vco_phase_before01.json');old=read(before['previous_qa'])
    assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    protected=old['private_input_sha256'];assert all((ROOT/n).is_file() for n in protected)
    profile=read('evidence/vco_phase_profile01.json');native=read('evidence/vco_phase_native05.json');storage=read('evidence/vco_phase_failure_storage01.json')
    assert profile['passed'] and native['passed'] and storage['passed'];identity(profile);identity(native);identity(storage);identity(read('evidence/vco_phase_native04.json'))
    assert sha(ROOT/profile['generated_source'])==profile['generated_source_sha256']
    for n,h in {**profile['private_used_sha256'],**native['private_used_sha256']}.items():assert n in protected and protected[n]==h and sha(ROOT/n)==h,n
    for k in [1,2,3]:
        path=ROOT/f'evidence/vco_phase_native{k:02d}.json';r=decoded(path);assert not r['passed']
        assert all(hashlib.sha256(base64.b64decode(r['failed_source_base64'][n])).hexdigest()==h for n,h in r['source_sha256'].items())
        if k==1:assert r['failed_phase']=='compile' and r['unchanged_replay_exit_code']!=0 and r['failed_probe_stderr']==r['unchanged_replay_stderr']
        else:
            # Identical electrical outputs make the old deterministic collector
            # reproduce its rejection; wall-time BENCH lines are not identities.
            assert r['failed_phase']=='probe' and r['unchanged_replay_exit_code']==0
            assert r['failed_probe_stdout'].split('BENCH,',1)[0]==r['unchanged_replay_stdout'].split('BENCH,',1)[0]
    for item in storage['records']:assert sha(ROOT/item['path'])==item['stored_sha256'] and item['restitution_exact']
    assert native['port_cases']==20 and native['fd_columns']==80 and max(native['port_fractions'].values())<=1
    assert len(native['shape'])==2 and all(x['observations']==481 for x in native['shape'])
    assert all(s['ac_harmonics_1_to_8_relative']<=.02 and s['dc_error_v']<=.005 for x in native['shape'] for s in x['signals'])
    assert all(x['max_phase_error_cycles']<=1e-4 and x['frequency_error_cents']<=.01 for x in native['epochs'])
    assert len(native['local_responses'])==72 and max(x['relative_error'] for x in native['local_responses'])<=.02 and max(x['backward'] for x in native['local_responses'])<=1e-10
    assert native['phase_wrap_cases']==200 and native['atomic_rejections']==7 and native['exact_valid_retry']
    assert len(native['benchmark'])==3 and all(x['samples']==1000000 and x['allocations']==0 and x['phase_error_cycles']<=1e-10 for x in native['benchmark'])
    assert native['temporary_area_empty'] and not list((ROOT/'tmp/lab-current').iterdir())
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']==native['compiler_sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(schema='rf-d/nominal-phase-prototype/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,private_input_sha256=protected,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(protected),new_private_sound_inputs=0,new_audio=False,new_cargo_cache=False,new_library_compile=False,new_native_reference_trajectory=False,nominal_phase_vco=True,phase_vco_memories_approximated=True,exact_output_resistor_port=True,output_terminals=4,source_harmonics=52,dc_retained=True,frequency_hz=profile['frequency_hz'],reference_voice_circuit_changed=False,full_voice=False,general_cv=False,physical_fidelity=False,real_time=False,full_voice_deadline_measured=False,phase_samples_measured=3000000,phase_heap_allocations=0,phase_wrap_cases=200,atomic_rejections=7,reserved_wave_observations=962,local_bus_tangents=72,original_port_cases=20,port_fd_columns=80,inherited_test_count=255,inherited_tests_reexecuted=False,new_unit_test_definitions=0,compiler=old['compiler'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening','cutoff_ab_reference','cutoff_ab_listening','observed_note_reference','observed_note_listening']:r[key]=old[key]
    r['phase_reference']={'path':'evidence/vco_phase_native05.json','sha256':sha(ROOT/'evidence/vco_phase_native05.json')}
    write(ROOT/OUT,r);print('VCO_PHASE_QA',len(sources),len(protected),r['phase_samples_measured'])
if __name__=='__main__':main()
