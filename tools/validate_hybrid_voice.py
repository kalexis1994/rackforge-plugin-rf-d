"""Admit the scoped hybrid branch, preserving all prior source/input IDs."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_hybrid_voice import unpack,parse,compare,US
from validate_joint_charge_seed import local_links
OUT='evidence/hybrid_voice_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def identity(r):
    snapshots=json.loads(unpack(r['failed_sources'])) if 'failed_sources' in r else {}
    for n,h in r['source_sha256'].items():
        if sha(ROOT/n)!=h:assert n in snapshots and hashlib.sha256(base64.b64decode(snapshots[n])).hexdigest()==h,n
def main():
    before=read('evidence/hybrid_voice_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    protected=old['private_input_sha256'];assert all((ROOT/n).is_file() for n in protected)
    native=read('evidence/hybrid_voice_native05.json');audit=read('evidence/hybrid_voice_audit01.json');profile=read('evidence/hybrid_voice_profile01.json')
    assert native['passed'] and audit['passed'] and profile['passed'];identity(native);identity(audit);identity(profile)
    assert sha(ROOT/profile['generated_source'])==profile['generated_source_sha256']
    assert profile['maximum_source_error_v']<=50e-6 and profile['closure_difference_v']<=100e-6 and profile['compacted_knots']==901
    for n,h in {**profile['private_used_sha256'],**native['private_used_sha256']}.items():assert protected[n]==h and sha(ROOT/n)==h,n
    grids=[]
    for p in native['profiles']:
        g,roots,f=parse(unpack(p['stdout']));grids.append(g)
        assert f['exact_replays']==4 and f['atomic_rejections']==5 and f['heap_allocations']==0
        assert len(roots)==12 and len(g)==481 and f['ticks']==100000*US
        x=p['reserved_comparison'];assert x['j7_rms_relative']<=.03 and x['j7_peak_relative']<=.06 and x['j7_mean_error_v']<=1e-5
        assert max(x['contour_fraction'],x['bus_fraction'],x['load_fraction'])<=1
    assert json.dumps(compare(grids[0],grids[1],True),sort_keys=True)==json.dumps(native['refinement'],sort_keys=True)
    assert audit['original_rows']==5712 and all(p['max_residual_a']<=2e-11 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    preflight=read('evidence/hybrid_voice_preflight_failure01.json');identity(preflight);assert not preflight['passed'] and 'UnicodeDecodeError' in preflight['unchanged_replay']
    for k in [1,2,3,4]:
        r=read(f'evidence/hybrid_voice_native{k:02d}.json');assert not r['passed'];identity(r)
        a=r['failed_process'];b=r['unchanged_replay']
        if k==3:
            assert r['failed_phase']=='profile' and a['exit_code']==b['exit_code']==0
            assert unpack(a['stdout']).split(b'FINAL,')[0]==unpack(b['stdout']).split(b'FINAL,')[0]
            assert 'bus_fraction' in r['failure']
        else:assert r['failed_phase']=='compile' and a['exit_code']==b['exit_code']!=0 and a['stderr']==b['stderr']
    assert native['temporary_area_empty'] and not list((ROOT/'tmp/lab-current').iterdir())
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']==native['compiler_sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(schema='rf-d/nominal-hybrid-voice/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,private_input_sha256=protected,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(protected),new_private_sound_inputs=0,new_audio=False,new_cargo_cache=False,new_library_compile=False,new_native_reference_trajectory=False,nominal_hybrid_branch=True,branch_start_s=.04,branch_end_s=.1,chain_unknowns=118,vco_memories_approximated=True,exact_loaded_output_port=True,chain_charge_memories_preserved=True,reference_voice_circuit_changed=False,full_voice_startup=False,general_cv=False,physical_fidelity=False,real_time=False,full_voice_deadline_measured=False,hybrid_heap_allocations=0,original_rows=5712,reserved_output_observations=962,exact_replays=8,atomic_rejections=10,inherited_test_count=255,inherited_tests_reexecuted=False,new_unit_test_definitions=0,compiler=old['compiler'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening','cutoff_ab_reference','cutoff_ab_listening','observed_note_reference','observed_note_listening','phase_reference']:r[key]=old[key]
    r['hybrid_reference']={n:sha(ROOT/n) for n in ['evidence/hybrid_voice_native05.json','evidence/hybrid_voice_audit01.json','evidence/hybrid_voice_profile01.json']}
    write(ROOT/OUT,r);print('HYBRID_QA',len(sources),len(protected),r['original_rows'])
if __name__=='__main__':main()
