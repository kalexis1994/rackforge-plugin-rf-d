"""Incremental preservation and scoped VCO/dual-contour voice admission."""
import base64,hashlib,json,re,shutil,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_dual_voice import generate_chain,generate_solver
from validate_joint_charge_seed import local_links
OUT='evidence/dual_voice_tests01.json'
ATTR=b'\n/crates/rf-d-circuit/src/dual_voice.rs text eol=lf\n/crates/rf-d-circuit/src/dual_voice_chain.rs text eol=lf\n/crates/rf-d-circuit/src/dual_voice_solver.rs text eol=lf\n/tools/dual_voice_bank.rs text eol=lf\n/evidence/dual_voice*.json text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    before=read('evidence/dual_voice_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    assert (ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR
    for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:assert (ROOT/n).read_bytes().startswith(saved[n]),n
    private=dict(old['private_input_sha256'])
    for n,h in private.items():assert sha(ROOT/n)==h,n
    native=read('evidence/dual_voice_native02.json');ref=read('evidence/dual_voice_reference01.json')
    for r in [native,ref]:
        assert r['passed']
        for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
    assert native['source_unchanged'] and native['library_unchanged'] and len(native['profiles'])==2
    assert all(p['exit_code']==0 and p['wall_s']<=600 for p in native['profiles'])
    assert ref['wall_s']<=300 and ref['common_clocks']==64 and ref['max_node_fraction']<=1 and ref['max_load_fraction']<=1
    assert ref['original_rows']==12550 and len(ref['linear_directions'])==2
    assert all(p['original_tangent_fraction']<=1 and p['dense_difference_fraction']<=1 and p['backward_fraction']<=1e-11 for p in ref['linear_directions'])
    assert sum(p['atomic_rejections'] for p in ref['profiles'])==6
    for p in ref['profiles']:assert p['ticks']==8000*524288 and p['selected_pairs']==12 and p['max_bus_kcl_a']<=2e-11
    assert (ROOT/'crates/rf-d-circuit/src/dual_voice_chain.rs').read_text(encoding='utf8')==generate_chain()
    assert (ROOT/'crates/rf-d-circuit/src/dual_voice_solver.rs').read_text(encoding='utf8')==generate_solver()
    for k in [1,2]:
        r=read(f'evidence/dual_voice_native{k:02d}.json')
        for n,h in r['private_sha256'].items():assert sha(ROOT/n)==h,n;private[n]=h
        if k==1:
            assert not r['passed'] and r['failed_phase']=='compile' and r['compile']['stderr_sha256']==r['unchanged_replay']['stderr_sha256']
            for n,v in read(r['output_directory']+'/failed_sources.json').items():assert hashlib.sha256(base64.b64decode(v)).hexdigest()==r['source_sha256'][n],n
    for k in [1,2]:
        r=read(f'evidence/dual_voice_prepare_failure{k:02d}.json');assert not r['passed'] and r['failure']==r['unchanged_replay']
        r=read(f'evidence/dual_voice_prepare_repair{k:02d}.json');assert r['unchanged_replay'] and not r['circuit_changed'] and not r['numerical_gates_changed']
    r=read('evidence/dual_voice_compile_repair01.json');assert r['unchanged_replay'] and not r['circuit_changed'] and not r['numerical_gates_changed']
    for p in (ROOT/'references-local').glob('dual-voice*/*'):
        if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));assert size<=32*1024**2 and shutil.disk_usage(ROOT).free>=1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    names=set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(schema='rf-d/dual-voice/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,new_private_bytes=size,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),native_nodes=250,original_nodes=251,profiles=2,duration_per_profile_s=.008,accepted_steps=sum(p['accepted_steps'] for p in ref['profiles']),fine_endpoints=2*sum(p['accepted_steps'] for p in ref['profiles']),new_independent_nonlinear_rows=12550,compared_effective_tangent_entries=500000,common_clocks=64,atomic_rollbacks=6,integrated_vco_voice=True,both_contours_loaded=True,shared_bus=True,imposed_audio_source=False,conditioned_dc_ramp_zero=True,fixed_panel_scene=True,new_audio=False,new_continuous_history_duration_s=.008,old_history_extended=False,reference={'path':'evidence/dual_voice_reference01.json','sha256':sha(ROOT/'evidence/dual_voice_reference01.json')},new_library_compile=False,new_cargo_cache=False,inherited_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,physical_fidelity=False,real_time=False,heap_measured=False,deadline_measured=False,compiler=old['compiler'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening','cutoff_ab_reference','cutoff_ab_listening']:r[key]=old[key]
    return r
def main():
    try:r=audit()
    except Exception:
        first=traceback.format_exc()
        try:audit();replay='unexpected pass'
        except Exception:replay=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/dual_voice_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/dual_voice_qa_failure{k:02d}.json',dict(passed=False,failure=first,unchanged_replay=replay,source_base64=base64.b64encode(Path(__file__).read_bytes()).decode()));raise
    write(ROOT/OUT,r);print('DUAL_VOICE_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
