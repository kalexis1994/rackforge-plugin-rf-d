"""Incremental release identities and scoped functional dual-contour admission."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from run_c5_trigger import ROOT,sha,write
from validate_joint_charge_seed import local_links
OUT='evidence/c5_trigger_tests01.json'
ATTR=b'\n/crates/rf-d-circuit/src/dual_contour.rs text eol=lf\n/tools/c5_trigger_bank.rs text eol=lf\n/evidence/c5_trigger*.json text eol=lf\n/crates/rf-d-circuit/src/dual_contour_checkpoint.rs text eol=lf\n/tools/c5_trigger_checkpoint_bank.rs text eol=lf\n'
ATTR+=b'/evidence/c5_trigger_observation01.svg text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    before=read('evidence/c5_trigger_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    assert (ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR
    for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:assert (ROOT/n).read_bytes().startswith(saved[n]),n
    private=dict(old['private_input_sha256'])
    for n,h in private.items():assert sha(ROOT/n)==h,n
    review=read('evidence/c5_trigger_review01.json');assert review['visual_review']
    for n,h in review['images'].items():assert sha(ROOT/n)==h,n;private[n]=h
    native=read('evidence/c5_trigger_native02.json');ref=read('evidence/c5_trigger_reference01.json');checkpoint=read('evidence/c5_trigger_checkpoint01.json');obs=read('evidence/c5_trigger_observation01.json')
    for r in [native,ref,checkpoint]:
        assert r['passed']
        for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
        for n,h in r.get('private_sha256',{}).items():assert sha(ROOT/n)==h,n;private[n]=h
    assert native['source_unchanged'] and native['library_unchanged'] and len(native['profiles'])==8
    assert all(p['exit_code']==0 and p['wall_s']<=300 for p in native['profiles'])
    assert ref['native_receipt_sha256']==sha(ROOT/ref['native_receipt']) and len(ref['profiles'])==8
    assert ref['original_rows']==40920 and ref['fd_entries']==1469664
    assert sum(p['accepted_steps'] for p in ref['profiles'])==86228
    assert sum(p['local_replays'] for p in ref['profiles'])==124
    assert all(p['events']==4 and p['atomic_rejections']==4 and p['grid_count']==144 for p in ref['profiles'])
    assert max(p['max_original_kcl_a'] for p in ref['profiles'])<=2e-11
    assert max(p['max_original_correction_v'] for p in ref['profiles'])<=2e-9
    assert max(p['max_fd_gate_fraction'] for p in ref['profiles'])<=1
    assert all(p['node_gate_fraction']<=1 and p['port_gate_fraction']<=1 and p['common_clocks']==144 for p in ref['refinement'])
    assert checkpoint['source_unchanged'] and checkpoint['fixtures']==40 and checkpoint['complete_pair_replays']==40 and checkpoint['corruptions_rejected']==320
    assert obs['passed'] and not obs['normalization'] and not obs['dc_removed']
    for key in ['input_sha256','code_sha256','output_sha256','private_sha256']:
        for n,h in obs[key].items():assert sha(ROOT/n)==h,n
    private.update(obs['private_sha256'])
    first=read('evidence/c5_trigger_native01.json');assert not first['passed'] and first['failed_phase']=='compile' and first['replay_same_exit'] and first['compile']['stderr_sha256']==first['unchanged_replay']['stderr_sha256']
    for n,h in first['private_sha256'].items():assert sha(ROOT/n)==h,n;private[n]=h
    snapshots=read(first['output_directory']+'/failed_sources.json')
    for n,v in snapshots.items():assert hashlib.sha256(base64.b64decode(v)).hexdigest()==first['source_sha256'][n],n
    failed=read('evidence/c5_trigger_reference_failure01.json');repair=read('evidence/c5_trigger_reference_repair01.json')
    assert not failed['passed'] and failed['failure'].splitlines()[-1]==failed['replay'].splitlines()[-1]
    assert repair['unchanged_replay'] and not repair['native_sources_changed'] and not repair['native_data_changed'] and not repair['numeric_gates_changed']
    original=base64.b64decode(failed['source_base64']).decode()
    expected=original.replace("assert at(20000)<at(10000)-.1,(mode,timer,'no decay',at(10000),at(20000))","release_peak=max(physical(s)[timer] for tick,(s,_) in trace.items() if 10000*1073741824<=tick<=20000*1073741824)\n            assert at(20000)<release_peak-.1,(mode,timer,'no decay after actual peak',release_peak,at(20000))").replace('first_peak_v=held_peak,release_v=at(20000)','first_peak_v=held_peak,post_source_release_peak_v=release_peak,release_v=at(20000)')
    assert (ROOT/'tools/audit_c5_trigger.py').read_text()==expected
    compiler=read('evidence/voice_assembly_public01.json')['compiler'];assert sha(Path(compiler['path']))==compiler['sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));assert size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    names=set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(schema='rf-d/dual-contour/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],
        source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,new_private_bytes=size,
        protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),original_circuit_sources_unchanged=True,
        native_nodes=54,original_nodes=55,profiles=8,duration_per_profile_s=.036,accepted_steps=86228,fine_endpoints=172456,
        new_independent_nonlinear_rows=40920,fd_entries=1469664,shared_clock_states=576,provisional_pair_replays=124,
        local_restore_replays=40,corruptions_rejected=320,atomic_rollbacks=32,source_events=32,c5_internal=True,shared_trigger_loaded=True,
        fixed_panel_scene=True,integrated_voice=False,new_audio=False,new_continuous_history_duration_s=0,
        reference={'path':'evidence/c5_trigger_reference01.json','sha256':sha(ROOT/'evidence/c5_trigger_reference01.json')},
        checkpoint={'path':'evidence/c5_trigger_checkpoint01.json','sha256':sha(ROOT/'evidence/c5_trigger_checkpoint01.json')},
        new_library_compile=False,new_cargo_cache=False,inherited_test_count=255,inherited_tests_reexecuted=False,
        inherited_python_test_definitions=2,new_unit_test_definitions=0,physical_fidelity=False,real_time=False,heap_measured=False,deadline_measured=False,
        compiler=compiler,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening',
        'sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference',
        'extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path',
        'public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening',
        'cutoff_ab_reference','cutoff_ab_listening']:r[key]=old[key]
    return r
def main():
    try:r=audit()
    except Exception:
        first=traceback.format_exc()
        try:audit()
        except Exception:replay=traceback.format_exc()
        else:replay='unexpected pass'
        k=1
        while (ROOT/f'evidence/c5_trigger_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/c5_trigger_qa_failure{k:02d}.json',dict(passed=False,failure=first,replay=replay,source_base64=base64.b64encode(Path(__file__).read_bytes()).decode()));raise
    write(ROOT/OUT,r);print('C5_TRIGGER_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
