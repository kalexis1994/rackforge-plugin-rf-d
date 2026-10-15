"""Close affine reconstruction with original equations and an unchanged cost gate."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_affine_newton import derive
from affine_evidence import recover
from check_hybrid_voice import unpack,parse,compare
from check_hybrid_schur import comparison
from check_affine_newton import LOCAL_KEYS,AFFINE_KEYS
from profile_affine_predecessor import derive as profile_derive
from validate_joint_charge_seed import local_links
OUT='evidence/affine_newton_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def numerical(data):return [line for line in data.splitlines() if line.startswith((b'GRID,',b'ROOT,',b'SOLVER,',b'AFFINE,'))]
def main():
    before=read('evidence/affine_newton_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/affine_newton_native01.json','evidence/affine_newton_profile01.json','evidence/affine_newton_audit01.json'];native,profile,audit=[read(n) for n in names]
    for r in[native,profile,audit]:
        image=recover(r)
        for n,data in image.items():assert sha(ROOT/n)==hashlib.sha256(data).hexdigest(),n
    assert native['numerical_integration_verified'] and len(native['compiles'])==4 and all(p['exit_code']==0 for p in native['compiles'])
    baseline=[p for p in read('evidence/hybrid_direct_native03.json')['profiles'] if p['mode']=='direct'];prior=[p for p in read('evidence/split_ladder_native02.json')['profiles'] if p['mode']=='split']
    rows=[]
    for p in baseline:
        _,roots,_=parse(unpack(p['stdout']));rows.extend(','.join(map(str,row)) for row in roots)
    assert unpack(native['local_input'])==('\n'.join(rows)+'\n').encode()
    values=list(map(float,unpack(native['local_stdout']).decode().strip().split(',')[1:]));assert len(values)==len(LOCAL_KEYS) and native['local']==dict(zip(LOCAL_KEYS,values))
    x=native['local'];assert x['pairs']==24 and x['stages']==48 and x['directions']==576 and x['physical_entries']==1336704 and x['invalid_cases']==44 and x['exact_retries']==93
    assert x['direction_fraction']<=1 and max(x[k] for k in ['physical_backward','max_final_backward','reduced_max_final_backward'])<=1e-11
    assert x['physical_solves']==x['directions']+x['exact_retries'] and x['reduced_rhs']==x['reduced_solves']==x['physical_solves']+x['physical_refinements']
    grids=[];replays=rejects=0
    for p in native['profiles']:
        raw=unpack(p['stdout']);g,roots,f=parse(raw);assert f==p['measurement'] and p['exit_code']==0
        i=0 if p['maximum_full_ticks']==33554432 else 1;control=unpack(baseline[i]['stdout']);og,_,_=parse(control);assert canonical(comparison(g,og,raw,control))==canonical(p['direct_comparison'])
        control=unpack(prior[i]['stdout']);og,_,_=parse(control);assert canonical(comparison(g,og,raw,control))==canonical(p['previous_comparison'])
        v=list(map(float,next(s for s in raw.decode().splitlines() if s.startswith('SOLVER,')).split(',')[1:]));assert p['solver']==dict(solves=int(v[0]),refinements=int(v[1]),max_nonzeros=int(v[2]),max_initial_backward=v[3],max_final_backward=v[4]);assert v[4]<=1e-11
        y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
        if p['mode']=='affine':
            v=list(map(float,next(s for s in raw.decode().splitlines() if s.startswith('AFFINE,')).split(',')[1:]));assert p['affine']==dict(zip(AFFINE_KEYS,v));a=p['affine']
            assert a['preparations']==a['physical_solves'] and a['reduced_rhs']==a['physical_solves']+a['physical_refinements']==p['solver']['solves'] and a['max_final_backward']<=1e-11
            assert f['exact_replays']==4 and f['atomic_rejections']==5 and f['heap_allocations']==0;replays+=4;rejects+=5;grids.append(g)
    assert len(grids)==2 and canonical(compare(grids[0],grids[1],True))==canonical(native['refinement'])
    ratio=native['profiles'][3]['measurement']['solve_s']/native['profiles'][0]['measurement']['solve_s'];assert ratio==native['cost_ratio']
    previous_ratio=native['profiles'][3]['measurement']['solve_s']/native['profiles'][1]['measurement']['solve_s'];assert previous_ratio==native['previous_cost_ratio']
    admitted=ratio<=.9;assert native['passed']==admitted
    if not admitted:
        assert native['failed_phase']=='cost';a=native['failed_process'];b=native['unchanged_replay'];assert a['exit_code']==b['exit_code']==0 and a['stderr']==b['stderr']==''
        assert numerical(unpack(a['stdout']))==numerical(unpack(b['stdout']))
    assert profile['passed'] and not profile['admission_benchmark'] and profile['timing_includes_exact_replays']
    assert profile['control_receipt_sha256']==sha(ROOT/profile['control_receipt'])
    raw=unpack(profile['stdout']);g,_,f=parse(raw);control=unpack(prior[1]['stdout']);og,_,_=parse(control)
    assert comparison(g,og,raw,control)==profile['comparison'] and f==profile['measurement']
    assert [s for s in numerical(raw) if not s.startswith(b'AFFINE,')]==numerical(control)
    v=list(map(int,next(s for s in raw.decode().splitlines() if s.startswith('CALLPROFILE,')).split(',')[1:]));assert profile['timed_calls']==dict(reduced_s=v[0]*1e-9,original_s=v[1]*1e-9,reduced_calls=v[2],original_calls=v[3])
    assert all(v>0 for v in profile['timed_calls'].values())
    assert audit['passed'] and audit['native']==names[0] and audit['native_sha256']==sha(ROOT/names[0]) and audit['original_rows']==5712
    assert len(audit['profiles'])==2 and all(p['pairs']==12 and p['max_residual_a']<=20e-12 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    for n,h in native['private_used_sha256'].items():assert private[n]==h==sha(ROOT/n),n
    for r in[native,profile]:
        assert r['temporary_area_empty'] and r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
        assert r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    for n,s in {**derive(),**profile_derive()}.items():assert (ROOT/n).read_bytes()==s.encode(),n
    assert not list((ROOT/'tmp/lab-current').iterdir())
    receipt_bytes=sum(p.stat().st_size for p in (ROOT/'evidence').glob('affine_newton*.json') if p!=ROOT/OUT);assert receipt_bytes<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for r in[native,profile,audit]:assert set(r['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/affine-newton-complete-physical-correction/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),affine_newton_numerically_verified=True,affine_newton_optimization_admitted=admitted,affine_newton_cost_ratio=ratio,affine_newton_previous_cost_ratio=previous_ratio,affine_newton_cost_gate=.9,affine_newton_local=native['local'],affine_newton_profiles=[p['affine'] for p in native['profiles'] if p['mode']=='affine'],affine_newton_original_rows=5712,affine_newton_heap_allocations=0,affine_newton_exact_replays=replays,affine_newton_atomic_rejections=rejects,affine_newton_previous_timed_calls=profile['timed_calls'],affine_newton_reference={n:sha(ROOT/n) for n in names},affine_newton_receipt_bytes_before_qa=receipt_bytes,affine_newton_receipt_budget_bytes=8*1024*1024,inherited_tests_reexecuted=False,inherited_global_trajectories_reexecuted=True,inherited_global_trajectory_reexecutions=3,inherited_global_trajectory_suite_reexecuted=False,new_original_250_node_trajectories=0,inherited_private_hashes_recomputed=False,new_candidate_trajectories=2,new_fresh_control_trajectories=2,new_candidate_instrumented_trajectories=0,new_predecessor_instrumented_trajectories=1,new_unit_test_definitions=0,new_audio=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    assert not admitted,'Promotion requires a separate active-engine integration; do not silently promote the laboratory module.'
    for k in ['active_solver','active_voice','cost_ratio','inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    write(ROOT/OUT,result);print('AFFINE_QA',len(sources),len(private),'numerical closure; active direct; ratio',ratio,'receipt bytes',receipt_bytes)
if __name__=='__main__':main()
