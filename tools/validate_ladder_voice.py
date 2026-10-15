"""Close the integrated ladder experiment without promoting its failed cost."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_ladder_voice import derive
from check_hybrid_voice import unpack,parse,compare
from check_hybrid_schur import comparison
from check_ladder_voice import LOCAL_KEYS
from validate_joint_charge_seed import local_links
OUT='evidence/ladder_voice_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def main():
    before=read('evidence/ladder_voice_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/ladder_voice_native01.json','evidence/ladder_voice_guard01.json','evidence/ladder_voice_audit01.json'];native,guard,audit=[read(n) for n in names]
    for r in[native,guard,audit]:
        for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
    assert not native['passed'] and native['failed_phase']=='cost' and native['numerical_integration_verified']
    assert all(p['exit_code']==0 for p in native['compiles']) and len(native['compiles'])==3
    images=json.loads(unpack(native['failed_sources']))
    assert set(images)==set(native['source_sha256'])
    for n,data in images.items():assert hashlib.sha256(base64.b64decode(data)).hexdigest()==native['source_sha256'][n]
    a=native['failed_process'];b=native['unchanged_replay'];assert a['exit_code']==b['exit_code']==0 and a['stderr']==b['stderr']==''
    assert unpack(a['stdout']).split(b'FINAL,')[0]==unpack(b['stdout']).split(b'FINAL,')[0]
    ratio=native['profiles'][2]['measurement']['solve_s']/native['profiles'][0]['measurement']['solve_s'];assert ratio==native['cost_ratio'] and ratio>.9
    previous=read('evidence/hybrid_direct_native03.json');baseline=[p for p in previous['profiles'] if p['mode']=='direct'];expected=[]
    for p in baseline:
        _,roots,_=parse(unpack(p['stdout']));expected.extend(','.join(map(str,row)) for row in roots)
    assert unpack(native['local_input'])==('\n'.join(expected)+'\n').encode()
    x=native['local'];values=list(map(float,unpack(native['local_stdout']).decode().strip().split(',')[1:]));assert len(values)==len(LOCAL_KEYS) and x==dict(zip(LOCAL_KEYS,values))
    assert x['pairs']==24 and x['stages']==48 and x['directions']==144 and x['fd_columns']==222 and x['invalid_cases']==36
    assert x['reconstructed_error_v']<=2e-9 and x['original_residual_a']<=20e-12 and x['charge_error_a']==0
    assert max(x[k] for k in ['direction_fraction','fd_fraction'])<=1 and x['max_final_backward']<=1e-11
    grids=[];heap=0;replays=0;rejections=0
    for p in native['profiles']:
        raw=unpack(p['stdout']);g,roots,f=parse(raw);assert f==p['measurement'];assert p['exit_code']==0
        q=baseline[0 if p['maximum_full_ticks']==33554432 else 1];control=unpack(q['stdout']);og,_,_=parse(control)
        assert comparison(g,og,raw,control)==p['direct_comparison']
        y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
        assert p['solver']['max_final_backward']<=1e-11
        if p['mode']=='ladder':grids.append(g);heap+=f['heap_allocations'];replays+=f['exact_replays'];rejections+=f['atomic_rejections']
    assert json.dumps(compare(grids[0],grids[1],True),sort_keys=True)==json.dumps(native['refinement'],sort_keys=True)
    assert len(grids)==2 and heap==0 and replays==8 and rejections==10
    assert guard['passed'];v=guard['local'];assert list(map(int,unpack(guard['stdout']).decode().strip().split(',')[1:]))==list(v.values())
    assert v==dict(invalid_cases=83,exact_invalid_retries=83,coefficient_entries=98568,fill_swap_rhs_fixtures=16,capacity_retries=1,factor_overflow_retries=1,legal_edge_retries=2)
    assert audit['passed'] and audit['native']==names[0] and audit['original_rows']==5712 and len(audit['profiles'])==2
    assert all(p['pairs']==12 and p['max_residual_a']<=20e-12 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    for r in[native,guard]:
        assert r['temporary_area_empty'] and r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
        assert r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    for n,h in native['private_used_sha256'].items():assert private[n]==h==sha(ROOT/n),n
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    assert not list((ROOT/'tmp/lab-current').iterdir())
    receipt_bytes=sum(p.stat().st_size for p in (ROOT/'evidence').glob('ladder_voice*.json') if p!=ROOT/OUT);assert receipt_bytes<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for r in[native,guard,audit]:assert set(r['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/nominal-integrated-ladder-reconstruction/rejected-cost-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),global_ladder_integration_verified=True,global_ladder_reduction_admitted=False,ladder_cost_measured=True,ladder_voice_cost_gate_passed=False,ladder_voice_cost_ratio=ratio,ladder_voice_cost_gate=.9,ladder_voice_unknowns_per_stage=111,ladder_voice_temporal_unknowns=222,ladder_voice_reconstructed_physical_nodes=118,ladder_voice_local=x,ladder_voice_guards=v,ladder_voice_original_rows=5712,ladder_voice_heap_allocations=heap,ladder_voice_exact_replays=replays,ladder_voice_atomic_rejections=rejections,ladder_voice_reference={n:sha(ROOT/n) for n in names},inherited_tests_reexecuted=False,inherited_global_trajectories_reexecuted=True,inherited_global_trajectory_reexecutions=1,inherited_global_trajectory_suite_reexecuted=False,new_original_250_node_trajectories=0,inherited_private_hashes_recomputed=False,new_candidate_trajectories=2,new_fresh_control_trajectories=1,new_unit_test_definitions=0,new_audio=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,ladder_voice_receipt_bytes_before_qa=receipt_bytes,ladder_voice_receipt_budget_bytes=8*1024*1024,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in['active_solver','active_voice','cost_ratio','inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    write(ROOT/OUT,result);print('LADDER_VOICE_QA',len(sources),len(private),'integration verified; cost rejected; active=direct',ratio,receipt_bytes)
if __name__=='__main__':main()
