"""Preserve prior evidence and admit only the measured temporal approximation."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from validate_joint_charge_seed import local_links
OUT='evidence/observed_note_tests01.json'
RS=['crates/rf-d-circuit/src/observed_voice.rs','crates/rf-d-circuit/src/charge_observed_voice.rs','tools/observed_voice_trajectory.rs','tools/charge_observed_voice_trajectory.rs','tools/observed_voice_rollback.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RS)+'/evidence/observed*.json text eol=lf\n/evidence/charge_observed*.json text eol=lf\n').encode()
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    before=read('evidence/observed_voice_before01.json');old=read(before['previous_qa'])
    assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    assert (ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR
    for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:assert (ROOT/n).read_bytes().startswith(saved[n]),n
    private=dict(old['private_input_sha256'])
    for n,h in private.items():assert sha(ROOT/n)==h,n
    records=['evidence/observed_voice_native01.json','evidence/observed_voice_native02.json','evidence/observed_voice_audit01.json','evidence/charge_observed_voice_native01.json','evidence/charge_observed_voice_audit01.json','evidence/observed_voice_rollback01.json','evidence/observed_voice_rollback02.json','evidence/observed_note_native01.json','evidence/observed_note_audit01.json','evidence/observed_note_listening01.json']
    for name in records:
        r=read(name)
        assert r['passed'] or name in ['evidence/observed_voice_native01.json','evidence/observed_voice_rollback01.json'],name
        snapshots={}
        if not r['passed']:
            assert r['failed_phase']=='compile'
            if name=='evidence/observed_voice_native01.json':
                assert r['unchanged_replay']['exit_code']==r['compile']['exit_code']!=0
                assert r['unchanged_replay']['stderr_sha256']==r['compile']['stderr_sha256']
                snapshots={n:base64.b64decode(v) for n,v in read(r['output_directory']+'/failed_sources.json').items()}
            else:
                assert r['compile_exit_code']==r['unchanged_replay_exit_code']!=0
                snapshots={n:base64.b64decode(v) for n,v in r['source_base64'].items()}
                assert r['private_sha256']['references-local/observed-rollback01/compile.stderr']==r['private_sha256']['references-local/observed-rollback01/replay.stderr']
        for n,h in r['source_sha256'].items():
            if sha(ROOT/n)!=h:assert n in snapshots and hashlib.sha256(snapshots[n]).hexdigest()==h,(name,n)
        for field in ['private_sha256','private_used_sha256']:
            for n,h in r.get(field,{}).items():assert sha(ROOT/n)==h,n;private[n]=h
    preflight=read('evidence/charge_observed_voice_preflight_failure01.json')
    assert hashlib.sha256(base64.b64decode(preflight['source_base64'])).hexdigest()==preflight['source_sha256']
    assert preflight['unchanged_replay_exit_code']!=0 and 'FileExistsError' in preflight['unchanged_replay_stderr']
    note=read('evidence/observed_note_native01.json');proof=read('evidence/observed_note_audit01.json');audio=read('evidence/observed_note_listening01.json')
    assert note['duration_us']==100000 and note['gate_end_us']==75000 and note['source_unchanged'] and note['library_unchanged']
    assert len(note['profiles'])==2 and all(p['exit_code']==0 and p['wall_s']<=600 and p['compression_verified'] for p in note['profiles'])
    assert proof['strict_reference_duration_s']==.006 and proof['refinement']['clocks']==801
    assert all(p['ticks']==100000*524288 and p['atomic_rejections']==4 and p['max_bus_kcl_a']<=2e-11 for p in proof['profiles'])
    assert audio['duration_s']==audio['simulation_duration_s']==.1 and audio['frames']==4800 and len(audio['profiles'])==2
    assert not any(audio[k] for k in ['repeated_cycles','concatenated','peak_normalization','dc_removed'])
    rollback=read('evidence/observed_voice_rollback02.json')
    assert rollback['domain_atomic_rejections']==2 and rollback['exact_valid_candidate_replays']==1
    for pattern in ['observed-voice*/*','charge-observed-voice*/*','observed-note*/*','observed-rollback*/*']:
        for p in (ROOT/'references-local').glob(pattern):
            if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==note['library_sha256']
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']))
    assert size<=48*1024**2 and shutil.disk_usage(ROOT).free>=1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(schema='rf-d/observed-note/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,private_input_sha256=private,new_private_bytes=size,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),native_nodes=250,original_nodes=251,physical_circuit_changed=False,spatial_reduction=False,temporal_estimator_changed=True,newton_gates_changed=False,conditioned_dc_ramp_zero=True,fixed_panel_scene=True,imposed_audio_source=False,both_contours_loaded=True,shared_bus=True,note_duration_s=.1,gate_duration_s=.074,note_clocks=801,strict_reference_duration_s=.006,strict_short_duration_s=.024,original_selected_rows=sum(read(n)['original_rows'] for n in ['evidence/observed_voice_audit01.json','evidence/charge_observed_voice_audit01.json','evidence/observed_note_audit01.json']),accepted_note_steps=sum(p['steps'] for p in proof['profiles']),atomic_note_rollbacks=8,old_history_extended=False,own_continuous_history=True,new_audio=True,physical_fidelity=False,real_time=False,heap_measured=False,deadline_measured=False,new_cargo_cache=False,new_library_compile=False,inherited_test_count=255,inherited_tests_reexecuted=False,new_unit_test_definitions=0,compiler=old['compiler'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening','cutoff_ab_reference','cutoff_ab_listening']:r[key]=old[key]
    r['observed_note_reference']={'path':'evidence/observed_note_audit01.json','sha256':sha(ROOT/'evidence/observed_note_audit01.json')}
    r['observed_note_listening']={'path':'evidence/observed_note_listening01.json','sha256':sha(ROOT/'evidence/observed_note_listening01.json')}
    return r

def main():
    try:r=audit()
    except Exception:
        error=traceback.format_exc()
        try:audit();replay='unexpected pass'
        except Exception:replay=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/observed_note_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/observed_note_qa_failure{k:02d}.json',dict(passed=False,failure=error,unchanged_replay=replay,source_base64=base64.b64encode(Path(__file__).read_bytes()).decode()));raise
    write(ROOT/OUT,r);print('OBSERVED_NOTE_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
