"""Admit prepared evaluation with unchanged exterior and precision gates."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import derive
from check_hybrid_voice import unpack,parse,compare
from validate_joint_charge_seed import local_links
OUT='evidence/hybrid_stamp_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def identity(r):
    saved=json.loads(unpack(r['failed_sources'])) if 'failed_sources' in r else {}
    for n,h in r['source_sha256'].items():
        if sha(ROOT/n)!=h:assert n in saved and hashlib.sha256(base64.b64decode(saved[n])).hexdigest()==h,n
def main():
    before=read('evidence/hybrid_stamp_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    protected=old['private_input_sha256'];assert all((ROOT/n).is_file() for n in protected)
    native=read('evidence/hybrid_stamp_native09.json');audit=read('evidence/hybrid_stamp_audit01.json');guards=read('evidence/hybrid_stamp_guards01.json')
    assert native['passed'] and audit['passed'] and guards['passed'];identity(native);identity(audit);identity(guards)
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    for n,h in native['private_used_sha256'].items():assert protected[n]==h and sha(ROOT/n)==h,n
    x=native['local'];assert x['stages']==48 and x['fd_columns']==472 and x['invalid_parameters']==3
    assert max(x[k] for k in ['dc_fraction','dq_fraction','jacobian_fraction','mass_fraction','fd_fraction','fast_dc_fraction','fast_dq_fraction'])<=1
    assert guards['invalid_stage_cases']==guards['exact_retries']==26;unpack(guards['stdout'])
    assert len(native['profiles'])==3 and native['profiles'][0]['mode']=='baseline';grids=[];solves=refinements=0
    for p in native['profiles']:
        g,roots,f=parse(unpack(p['stdout']));assert f['heap_allocations']==0 and f['exact_replays']==4 and f['atomic_rejections']==5
        x=p['schur_comparison'];assert max(x['max_node_fraction'],x['max_load_fraction'],x['final_state_fraction'])<=1 and x['j7_rms_relative']<=.001 and x['j7_peak_relative']<=.003 and x['j7_mean_error_v']<=1e-6
        y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
        assert p['solver']['max_final_backward']<=1e-11
        if p['mode']=='prepared':grids.append(g);solves+=p['solver']['solves'];refinements+=p['solver']['refinements']
    assert json.dumps(compare(grids[0],grids[1],True),sort_keys=True)==json.dumps(native['refinement'],sort_keys=True)
    ratio=native['profiles'][2]['measurement']['solve_s']/native['profiles'][0]['measurement']['solve_s'];assert ratio==native['cost_ratio'] and ratio<=.9
    assert audit['original_rows']==5712 and all(p['max_residual_a']<=2e-11 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    for k in range(1,9):
        r=read(f'evidence/hybrid_stamp_native{k:02d}.json');assert not r['passed'];identity(r);a=r['failed_process'];b=r['unchanged_replay']
        if k==1:assert r['failed_phase']=='compile' and a['exit_code']==b['exit_code']!=0 and a['stderr']==b['stderr']
        else:assert r['failed_phase']=='cost' and r['cost_ratio']>.9 and a['exit_code']==b['exit_code']==0 and unpack(a['stdout']).split(b'FINAL,')[0]==unpack(b['stdout']).split(b'FINAL,')[0]
    assert native['temporary_area_empty'] and guards['temporary_area_empty'] and not list((ROOT/'tmp/lab-current').iterdir())
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']==native['compiler_sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    r.update(schema='rf-d/nominal-hybrid-prepared-stamp/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(protected),new_private_sound_inputs=0,new_audio=False,new_cargo_cache=False,new_library_compile=False,prepared_stamp_admitted=True,prepared_metadata_immutable=True,duplicated_cutoff_removed=True,sparse_low_direction=True,low_omitted=False,shared_candidate_prevalidated=True,chain_charge_memories_preserved=True,residual_only_trials=True,retained_chain_unknowns=118,source_and_charge_laws_changed=False,generated_sources_exact=True,local_stamp_stages=48,stamp_fd_columns=472,invalid_prepared_parameters=3,invalid_stage_cases=26,exact_stage_retries=26,original_rows=5712,observed_linear_solves=solves,observed_linear_refinements=refinements,reserved_output_observations=962,exact_replays=8,atomic_rejections=10,cost_ratio=ratio,cost_gate=.9,fresh_cost_control=True,hybrid_heap_allocations=0,real_time=False,physical_fidelity=False,full_voice_deadline_measured=False,inherited_test_count=255,inherited_tests_reexecuted=False,new_unit_test_definitions=0,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    r['hybrid_stamp_reference']={n:sha(ROOT/n) for n in ['evidence/hybrid_stamp_native09.json','evidence/hybrid_stamp_audit01.json','evidence/hybrid_stamp_guards01.json']}
    write(ROOT/OUT,r);print('HYBRID_STAMP_QA',len(sources),len(protected),ratio,solves)
if __name__=='__main__':main()
