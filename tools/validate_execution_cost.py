"""Close the measured cost map and the current-pivot-support experiment."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import recover
from prepare_execution_cost import derive as profile_derive
from prepare_support_pivot import derive
from profile_execution_cost import NAMES,numerical,final_state
from check_support_pivot import LOCAL_KEYS
from check_hybrid_voice import unpack,parse,compare
from check_hybrid_schur import comparison
from validate_joint_charge_seed import local_links
OUT='evidence/execution_cost_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def main():
    before=read('evidence/execution_cost_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/execution_cost_profile01.json','evidence/support_pivot_native01.json','evidence/support_pivot_audit01.json'];profile,native,audit=[read(n) for n in names]
    for r in [profile,native,audit]:
        for n,data in recover(r).items():assert sha(ROOT/n)==hashlib.sha256(data).hexdigest(),n
    assert profile['passed'] and not profile['admission_benchmark'] and profile['timing_includes_exact_replays']
    assert profile['control_receipt_sha256']==sha(ROOT/profile['control_receipt']);control=read(profile['control_receipt'])
    assert len(profile['profiles'])==2
    for p,index in zip(profile['profiles'],[0,3]):
        raw=unpack(p['stdout']);reference=unpack(control['profiles'][index]['stdout']);g,_,f=parse(raw);og,_,_=parse(reference)
        assert numerical(raw)==numerical(reference) and final_state(raw)==final_state(reference) and comparison(g,og,raw,reference)==p['comparison'] and f==p['measurement']
        values=list(map(int,next(s for s in raw.decode().splitlines() if s.startswith('EXECUTION,')).split(',')[1:]));assert len(values)==2*len(NAMES)
        assert p['timers']=={n:dict(ns=values[2*k],calls=values[2*k+1]) for k,n in enumerate(NAMES)}
        t=p['timers'];assert t['advance']['calls']==f['steps']+f['exact_replays']+f['atomic_rejections']
        assert t['prepare']['calls']==t['solve']['calls']==p['timers']['factor_or_reduced_prepare']['calls']
        assert t['full_evaluation']['calls']==2*t['prepare']['calls'] and t['residual_evaluation']['calls']>0
        assert t['advance']['ns']>=t['full_evaluation']['ns']+t['residual_evaluation']['ns']
        if p['mode']=='affine':
            assert all(t[k]['calls']==t['full_evaluation']['calls']+t['residual_evaluation']['calls'] for k in ['local_kernel','parent_parts','binding_validation','binding_merge'])
            assert all(t[k]['calls']==t['prepare']['calls'] for k in ['physical_csr','local_algebra','retained_projection'])
            assert t['prepare']['ns']>=sum(t[k]['ns'] for k in ['physical_csr','local_algebra','retained_projection','factor_or_reduced_prepare'])
        else:assert t['solve']['ns']>=t['prepare']['ns']+t['correction_or_reduced_solve']['ns']+t['physical_backward']['ns']
    assert native['numerical_integration_verified'] and len(native['compiles'])==3 and all(p['exit_code']==0 for p in native['compiles'])
    baseline=[p for p in read('evidence/hybrid_direct_native03.json')['profiles'] if p['mode']=='direct'];rows=[]
    for p in baseline:
        _,roots,_=parse(unpack(p['stdout']));rows.extend(','.join(map(str,row)) for row in roots)
    assert unpack(native['local_input'])==('\n'.join(rows)+'\n').encode()
    x=list(map(float,unpack(native['local_stdout']).decode().strip().split(',')[1:]));assert len(x)==len(LOCAL_KEYS) and native['local']==dict(zip(LOCAL_KEYS,x))
    x=native['local'];assert x['directions']==192 and x['physical_entries']==1336704 and x['invalid_cases']==33 and x['legal_edge_retries']==24 and x['cancellation_probes']==1
    assert x['direction_fraction']<=1 and x['max_final_backward']<=1e-11
    grids=[]
    for p in native['profiles']:
        raw=unpack(p['stdout']);g,_,f=parse(raw);assert f==p['measurement'] and p['exit_code']==0
        i=0 if p['maximum_full_ticks']==33554432 else 1;reference=unpack(baseline[i]['stdout']);og,_,_=parse(reference)
        assert canonical(comparison(g,og,raw,reference))==canonical(p['direct_comparison'])
        assert numerical(raw)==numerical(reference) and final_state(raw)==final_state(reference)
        values=list(map(float,next(s for s in raw.decode().splitlines() if s.startswith('SOLVER,')).split(',')[1:]));assert p['solver']==dict(solves=int(values[0]),refinements=int(values[1]),max_nonzeros=int(values[2]),max_initial_backward=values[3],max_final_backward=values[4]) and values[4]<=1e-11
        y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
        assert f['heap_allocations']==0 and f['exact_replays']==4 and f['atomic_rejections']==5
        if p['mode']=='support':grids.append(g)
    assert len(grids)==2 and canonical(compare(grids[0],grids[1],True))==canonical(native['refinement'])
    ratio=native['profiles'][2]['measurement']['solve_s']/native['profiles'][0]['measurement']['solve_s'];assert ratio==native['cost_ratio'];admitted=ratio<=.9;assert native['passed']==admitted
    if not admitted:
        assert native['failed_phase']=='cost';a=native['failed_process'];b=native['unchanged_replay'];assert a['exit_code']==b['exit_code']==0 and a['stderr']==b['stderr']==''
        assert numerical(unpack(a['stdout']))==numerical(unpack(b['stdout'])) and final_state(unpack(a['stdout']))==final_state(unpack(b['stdout']))
    assert audit['passed'] and audit['native']==names[1] and audit['native_sha256']==sha(ROOT/names[1]) and audit['original_rows']==5712
    assert len(audit['profiles'])==2 and all(p['pairs']==12 and p['max_residual_a']<=20e-12 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    for n,h in native['private_used_sha256'].items():assert private[n]==h==sha(ROOT/n),n
    for r in [profile,native]:
        assert r['temporary_area_empty'] and r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
        assert r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    for n,s in {**derive(),**profile_derive()}.items():assert (ROOT/n).read_bytes()==s.encode(),n
    assert not list((ROOT/'tmp/lab-current').iterdir())
    receipt_bytes=sum(p.stat().st_size for prefix in ['execution_cost','support_pivot'] for p in (ROOT/'evidence').glob(prefix+'*.json') if p!=ROOT/OUT);assert receipt_bytes<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for r in [profile,native,audit]:assert set(r['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/execution-cost-current-pivot-support/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),execution_cost_profile_reference=names[0],execution_cost_profile_timers={p['mode']:p['timers'] for p in profile['profiles']},support_pivot_numerically_verified=True,support_pivot_optimization_admitted=admitted,support_pivot_cost_ratio=ratio,support_pivot_cost_gate=.9,support_pivot_local=native['local'],support_pivot_fill_fixture=True,support_pivot_original_rows=5712,support_pivot_heap_allocations=0,support_pivot_exact_replays=8,support_pivot_atomic_rejections=10,execution_cost_reference={n:sha(ROOT/n) for n in names},execution_cost_receipt_bytes_before_qa=receipt_bytes,execution_cost_receipt_budget_bytes=8*1024*1024,inherited_tests_reexecuted=False,inherited_global_trajectories_reexecuted=True,inherited_global_trajectory_reexecutions=5,inherited_global_trajectory_suite_reexecuted=False,new_original_250_node_trajectories=0,inherited_private_hashes_recomputed=False,new_candidate_trajectories=2,new_fresh_control_trajectories=1,new_candidate_instrumented_trajectories=0,new_current_instrumented_trajectories=2,new_unit_test_definitions=0,new_audio=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    # This closure records eligibility only. Active selection requires an explicit integration.
    for k in ['active_solver','active_voice','cost_ratio','inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    write(ROOT/OUT,result);print('EXECUTION_QA',len(sources),len(private),'support cost gate',admitted,'ratio',ratio,'receipt bytes',receipt_bytes)
if __name__=='__main__':main()
