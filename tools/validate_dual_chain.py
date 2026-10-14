"""Incremental source/private preservation and scoped loaded-contour admission."""
import base64,hashlib,json,shutil,subprocess,traceback
from prepare_dual_chain import ROOT,sha,write
from validate_joint_charge_seed import local_links
OUT='evidence/dual_chain_tests01.json'
ATTR=b'\n/crates/rf-d-circuit/src/dual_contour_loaded.rs text eol=lf\n/crates/rf-d-circuit/src/dual_chain.rs text eol=lf\n/tools/dual_chain_bank.rs text eol=lf\n/evidence/dual_chain*.json text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    before=read('evidence/dual_chain_before01.json');old=read(before['previous_qa'])
    assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    assert (ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR
    for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:assert (ROOT/n).read_bytes().startswith(saved[n]),n
    private=dict(old['private_input_sha256'])
    for n,h in private.items():assert sha(ROOT/n)==h,n
    native=read('evidence/dual_chain_native04.json');ref=read('evidence/dual_chain_reference01.json');star=read('evidence/dual_chain_star01.json');obs=read('evidence/dual_chain_observations01.json')
    for r in [native,ref,star,obs]:
        assert r.get('passed',True)
        for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
    assert native['source_unchanged'] and native['library_unchanged'] and len(native['profiles'])==2
    assert ref['native_receipt_sha256']==sha(ROOT/ref['native_receipt'])
    assert star['retained_amount_cursor'] and star['original_rows']==14518
    assert ref['fd_entries']==139240 and ref['common_clocks']==144
    assert ref['max_node_refinement_fraction']<=1 and ref['max_load_refinement_fraction']<=1
    assert sum(p['accepted_steps'] for p in ref['profiles'])==21250
    assert sum(p['local_replays'] for p in ref['profiles'])==20 and sum(p['atomic_rejections'] for p in ref['profiles'])==6
    assert all(p['exit_code']==0 and p['wall_s']<=300 for p in native['profiles'])
    assert ref['wall_s']<=300 and star['wall_s']<=300
    assert max(p['max_kcl_a'] for p in star['profiles'])<=2e-11 and max(p['max_correction_v'] for p in star['profiles'])<=2e-9
    assert obs['trace_sha256']==sha(ROOT/native['output_directory']/'profile-4.stdout') and obs['observations']==144
    for k in [1,2,3,4]:
        r=read(f'evidence/dual_chain_native{k:02d}.json')
        for n,h in r['private_sha256'].items():assert sha(ROOT/n)==h,n;private[n]=h
        if k<4:
            assert not r['passed'] and r['source_unchanged'] and r['library_unchanged']
            snapshots=read(r['output_directory']+'/failed_sources.json')
            for n,s in snapshots.items():assert hashlib.sha256(base64.b64decode(s)).hexdigest()==r['source_sha256'][n],n
            if k==1:assert r['failure'].splitlines()[-1]==r['unchanged_replay'].splitlines()[-1]
            else:assert r['compile']['exit_code']==r['unchanged_replay']['exit_code'] and r['compile']['stderr_sha256']==r['unchanged_replay']['stderr_sha256']
    for k in [1,2,3]:
        r=read(f'evidence/dual_chain_repair{k:02d}.json');assert r['unchanged_replay'] and not r['numeric_gates_changed'] and not r['circuit_changed']
    for p in (ROOT/'references-local').glob('dual-chain*/*'):
        if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
    compiler=old['compiler'];assert sha(__import__('pathlib').Path(compiler['path']))==compiler['sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));assert size<=32*1024**2 and shutil.disk_usage(ROOT).free>=1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    names=set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(schema='rf-d/dual-chain/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,new_private_bytes=size,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),native_nodes=118,original_nodes=119,profiles=2,duration_per_profile_s=.036,accepted_steps=21250,fine_endpoints=42500,new_independent_nonlinear_rows=14518,compared_fd_entries=139240,common_clocks=144,local_endpoint_replays=20,atomic_rollbacks=6,vca_base_internal=True,tail_internal=True,q26_q28_shared=True,c18_once=True,c5_internal=True,shared_trigger_loaded=True,fixed_panel_scene=True,integrated_signal_chain=True,integrated_vco_voice=False,new_audio=False,new_continuous_history_duration_s=0,reference={'path':'evidence/dual_chain_reference01.json','sha256':sha(ROOT/'evidence/dual_chain_reference01.json')},original_star={'path':'evidence/dual_chain_star01.json','sha256':sha(ROOT/'evidence/dual_chain_star01.json')},new_library_compile=False,new_cargo_cache=False,inherited_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,physical_fidelity=False,real_time=False,heap_measured=False,deadline_measured=False,compiler=compiler,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening','cutoff_ab_reference','cutoff_ab_listening']:r[key]=old[key]
    return r
def main():
    try:r=audit()
    except Exception:
        error=traceback.format_exc()
        try:audit();replay='unexpected pass'
        except Exception:replay=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/dual_chain_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/dual_chain_qa_failure{k:02d}.json',dict(passed=False,failure=error,unchanged_replay=replay,source_base64=base64.b64encode(__import__('pathlib').Path(__file__).read_bytes()).decode()));raise
    write(ROOT/OUT,r);print('JOINT_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
