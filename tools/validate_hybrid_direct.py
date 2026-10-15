"""Admit direct assembly and zero-pivot skips with preserved failed cost evidence."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_direct import derive
from check_hybrid_voice import unpack,parse,compare
from check_hybrid_schur import comparison
from validate_joint_charge_seed import local_links
OUT='evidence/hybrid_direct_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def identity(r):
    images=[json.loads(unpack(x['failed_sources'])) for x in [r,*ARCHIVES] if 'failed_sources' in x]
    for n,h in r['source_sha256'].items():
        if sha(ROOT/n)!=h:assert any(n in saved and hashlib.sha256(base64.b64decode(saved[n])).hexdigest()==h for saved in images),n
ARCHIVES=[]
def main():
    before=read('evidence/hybrid_direct_before01.json');old=read(before['previous_qa'])
    assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    protected=old['private_input_sha256'];assert all((ROOT/n).is_file() for n in protected)
    native=read('evidence/hybrid_direct_native03.json');audit=read('evidence/hybrid_direct_audit01.json')
    ARCHIVES.extend(read(f'evidence/hybrid_direct_native{k:02d}.json') for k in [1,2])
    for r in [native,audit]:assert r['passed'];identity(r)
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    for failed in ARCHIVES:
        assert not failed['passed'] and failed['failed_phase']=='cost' and failed['cost_ratio']>.9;identity(failed)
        a=failed['failed_process'];b=failed['unchanged_replay'];assert a['exit_code']==b['exit_code']==0
        assert unpack(a['stdout']).split(b'FINAL,')[0]==unpack(b['stdout']).split(b'FINAL,')[0]
        assert failed['temporary_area_empty']
    profile=read('evidence/hybrid_direct_profile01.json');assert profile['passed'];identity(profile)
    assert profile['timed_sections_s']['direct_assembly_validation']>0 and profile['timed_sections_s']['factorization']>0
    assert all(value==0 for value in profile['comparison'].values() if isinstance(value,float))
    for n,h in native['private_used_sha256'].items():assert protected[n]==h and sha(ROOT/n)==h,n
    x=native['local'];assert x['directions']==192 and x['direction_fraction']<=1 and x['max_final_backward']<=1e-11
    assert x['bitwise_matrix_entries']==24*236*236 and x['invalid_cases']==x['exact_invalid_retries']==33 and x['new_legal_edge_retries']==24 and x['cancellation_probes']==1
    unpack(native['local_stdout']);unpack(native['local_input'])
    previous=read('evidence/hybrid_stage_native01.json');baseline=[p for p in previous['profiles'] if p['mode']=='stage']
    assert len(native['profiles'])==3 and native['profiles'][0]['mode']=='baseline'
    grids=[];solves=refinements=0
    for p in native['profiles']:
        data=unpack(p['stdout']);g,roots,f=parse(data)
        assert f['heap_allocations']==0 and f['exact_replays']==4 and f['atomic_rejections']==5
        control=baseline[0 if p['maximum_full_ticks']==33554432 else 1];raw=unpack(control['stdout']);og,_,_=parse(raw)
        result=comparison(g,og,data,raw);assert result==p['schur_comparison']
        assert data.split(b'FINAL,')[0]==raw.split(b'FINAL,')[0]
        assert max(result[k] for k in ['max_node_fraction','max_load_fraction','final_state_fraction','j7_rms_relative','j7_peak_relative','j7_mean_error_v'])==0
        y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
        assert p['solver']['max_final_backward']<=1e-11
        if p['mode']=='direct':grids.append(g);solves+=p['solver']['solves'];refinements+=p['solver']['refinements']
    assert json.dumps(compare(grids[0],grids[1],True),sort_keys=True)==json.dumps(native['refinement'],sort_keys=True)
    ratio=native['profiles'][2]['measurement']['solve_s']/native['profiles'][0]['measurement']['solve_s']
    assert ratio==native['cost_ratio'] and ratio<=.9
    assert audit['original_rows']==5712 and all(p['max_residual_a']<=2e-11 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    assert all(r['temporary_area_empty'] for r in [native,profile]) and not list((ROOT/'tmp/lab-current').iterdir())
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']==native['compiler_sha256']==profile['compiler_sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']==profile['library_sha256']
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    r.update(schema='rf-d/nominal-hybrid-direct-schur/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(protected),new_private_sound_inputs=0,new_audio=False,new_cargo_cache=False,new_library_compile=False,direct_stage_assembly_admitted=True,dense_intermediate_removed=True,dense_intermediate_bytes=236*236*8,all_coefficients_inspected=True,zero_pivot_candidates_skipped=True,prepared_pivot_scales_from_actual_interior=True,finite_weights_required_for_zero_shortcut=True,all_actual_inputs_inspected=True,cancellation_probes=1,scalar_formula_unchanged=True,bitwise_matrix_entries=24*236*236,monolithic_refined_directions=192,linear_invalid_cases=33,linear_exact_retries=33,new_legal_edge_retries=24,original_rows=5712,observed_linear_solves=solves,observed_linear_refinements=refinements,reserved_output_observations=962,exact_replays=8,atomic_rejections=10,cost_ratio=ratio,cost_gate=.9,fresh_cost_control=True,hybrid_heap_allocations=0,real_time=False,physical_fidelity=False,full_voice_deadline_measured=False,inherited_test_count=255,inherited_tests_reexecuted=False,new_unit_test_definitions=0,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    r['hybrid_direct_reference']={n:sha(ROOT/n) for n in ['evidence/hybrid_direct_native01.json','evidence/hybrid_direct_native02.json','evidence/hybrid_direct_native03.json','evidence/hybrid_direct_profile01.json','evidence/hybrid_direct_audit01.json']}
    r['new_numerical_boundary_checks']='33 nonfinite/structural/capacity/singular rejections with exact retries and 24 new legal edges followed by exact restoration'
    write(ROOT/OUT,r);print('HYBRID_DIRECT_QA',len(sources),len(protected),ratio,solves)
if __name__=='__main__':main()
