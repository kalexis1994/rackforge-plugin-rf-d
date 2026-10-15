"""Admit current-incidence assembly and explicitly select the verified facade."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_incidence_voice import derive
from affine_evidence import recover
from check_incidence_voice import LOCAL_KEYS
from check_hybrid_voice import unpack,parse,compare
from check_hybrid_schur import comparison
from profile_execution_cost import numerical,final_state
from validate_joint_charge_seed import local_links
OUT='evidence/incidence_voice_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def main():
    before=read('evidence/incidence_voice_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/incidence_voice_native01.json','evidence/incidence_voice_audit01.json','evidence/incidence_voice_selection01.json','evidence/incidence_voice_packet01.json'];native,audit,selection,packet=[read(n) for n in names]
    for r in [native,audit,selection,packet]:
        assert r['passed']
        for n,data in recover(r).items():assert sha(ROOT/n)==hashlib.sha256(data).hexdigest(),n
    assert native['numerical_integration_verified'] and len(native['compiles'])==3 and all(p['exit_code']==0 for p in native['compiles'])
    baseline=[p for p in read('evidence/hybrid_direct_native03.json')['profiles'] if p['mode']=='direct'];rows=[]
    for p in baseline:
        _,roots,_=parse(unpack(p['stdout']));rows.extend(','.join(map(str,row)) for row in roots)
    assert unpack(native['local_input'])==('\n'.join(rows)+'\n').encode()
    x=list(map(float,unpack(native['local_stdout']).decode().strip().split(',')[1:]));assert len(x)==len(LOCAL_KEYS) and native['local']==dict(zip(LOCAL_KEYS,x))
    x=native['local'];assert x['pairs']==24 and x['directions']==192 and x['physical_entries']==x['temporal_entries']==1336704 and x['invalid_cases']==33 and x['legal_edge_retries']==24
    assert x['max_stage_entries']==480 and x['packet_invalid_cases']==37 and x['packet_exact_retries']==27 and x['direction_fraction']<=1 and x['max_final_backward']<=1e-11
    grids=[]
    for p in native['profiles']:
        raw=unpack(p['stdout']);g,_,f=parse(raw);assert f==p['measurement'] and p['exit_code']==0
        i=0 if p['maximum_full_ticks']==33554432 else 1;reference=unpack(baseline[i]['stdout']);og,_,_=parse(reference)
        assert canonical(comparison(g,og,raw,reference))==canonical(p['direct_comparison'])
        assert numerical(raw)==numerical(reference) and final_state(raw)==final_state(reference)
        values=list(map(float,next(s for s in raw.decode().splitlines() if s.startswith('SOLVER,')).split(',')[1:]));assert p['solver']==dict(solves=int(values[0]),refinements=int(values[1]),max_nonzeros=int(values[2]),max_initial_backward=values[3],max_final_backward=values[4]) and values[4]<=1e-11
        y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
        assert f['heap_allocations']==0 and f['exact_replays']==4 and f['atomic_rejections']==5
        if p['mode']=='incidence':grids.append(g)
    assert len(grids)==2 and canonical(compare(grids[0],grids[1],True))==canonical(native['refinement'])
    ratio=native['profiles'][2]['measurement']['solve_s']/native['profiles'][0]['measurement']['solve_s'];assert ratio==native['cost_ratio']<=.9
    assert audit['native']==names[0] and audit['native_sha256']==sha(ROOT/names[0]) and audit['original_rows']==5712
    assert len(audit['profiles'])==2 and all(p['pairs']==12 and p['max_residual_a']<=20e-12 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    assert selection['control_receipt']==names[0] and selection['control_receipt_sha256']==sha(ROOT/names[0]) and selection['audit_receipt_sha256']==sha(ROOT/names[1]) and len(selection['profiles'])==3
    for p,c in zip(selection['profiles'],native['profiles']):
        raw=unpack(p['stdout']);reference=unpack(c['stdout']);g,_,f=parse(raw);og,_,_=parse(reference)
        assert f==p['measurement'] and numerical(raw)==numerical(reference) and final_state(raw)==final_state(reference) and comparison(g,og,raw,reference)==p['comparison']
        assert f['heap_allocations']==0 and f['exact_replays']==4 and f['atomic_rejections']==5
    selected_ratio=selection['profiles'][2]['measurement']['solve_s']/selection['profiles'][0]['measurement']['solve_s'];assert selected_ratio==selection['cost_ratio']<=.9
    values=list(map(int,unpack(packet['stdout']).decode().strip().split(',')[1:]));assert packet['measurements']==dict(zip(['contracts','previous_parts_bytes','selected_parts_bytes','tangent_bytes'],values))
    assert packet['measurements']==dict(contracts=7,previous_parts_bytes=226568,selected_parts_bytes=78480,tangent_bytes=74696)
    facade='crates/rf-d-circuit/src/active_nominal_voice.rs';implementation='crates/rf-d-circuit/src/incidence_hybrid_voice.rs';solver='crates/rf-d-circuit/src/incidence_hybrid_solver.rs'
    assert (ROOT/facade).read_text().endswith('#[path="incidence_hybrid_voice.rs"]mod implementation;\npub use implementation::*;\n')
    probe=(ROOT/'tools/incidence_voice_probe.rs').read_text();block='#[cfg(not(condensed))]\n#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"] mod circuit;\n#[cfg(condensed)]\n#[path="../crates/rf-d-circuit/src/incidence_hybrid_voice.rs"] mod circuit;'
    assert probe.count(block)==1 and (ROOT/'tools/active_nominal_voice_probe.rs').read_text()==probe.replace(block,'#[path="../crates/rf-d-circuit/src/active_nominal_voice.rs"]mod circuit;',1)
    for n,h in native['private_used_sha256'].items():assert private[n]==h==sha(ROOT/n),n
    for r in [native,selection,packet]:
        assert r['temporary_area_empty'] and r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
        assert r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    assert not list((ROOT/'tmp/lab-current').iterdir())
    receipt_bytes=sum(p.stat().st_size for p in (ROOT/'evidence').glob('incidence_voice*.json') if p!=ROOT/OUT);assert receipt_bytes<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for r in [native,audit,selection,packet]:assert set(r['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/current-incidence-assembly/admitted-selected-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),incidence_voice_numerically_verified=True,incidence_voice_optimization_admitted=True,incidence_voice_selected=True,incidence_voice_cost_ratios=[ratio,selected_ratio],incidence_voice_cost_gate=.9,incidence_voice_local=native['local'],incidence_voice_packet_contract=packet['measurements'],incidence_voice_original_rows=5712,incidence_voice_heap_allocations=0,incidence_voice_exact_replays=8,incidence_voice_atomic_rejections=10,incidence_voice_selected_exact_replays=8,incidence_voice_selected_atomic_rejections=10,incidence_voice_reference={n:sha(ROOT/n) for n in names},incidence_voice_receipt_bytes_before_qa=receipt_bytes,incidence_voice_receipt_budget_bytes=8*1024*1024,previous_active_engine={k:old.get(k) for k in ['active_solver','active_voice','active_solver_origin_commit','cost_ratio']},active_solver=solver,active_voice=facade,active_voice_implementation=implementation,active_solver_source_sha256=sources[solver],active_voice_source_sha256=sources[facade],active_solver_origin_commit=None,active_solver_origin_commit_pending_self_commit=True,active_solver_admission_receipt=OUT,cost_ratio=selected_ratio,inherited_tests_reexecuted=False,inherited_global_trajectories_reexecuted=True,inherited_global_trajectory_reexecutions=6,inherited_global_trajectory_suite_reexecuted=False,new_original_250_node_trajectories=0,inherited_private_hashes_recomputed=False,new_candidate_trajectories=2,new_fresh_control_trajectories=2,new_selected_trajectories=2,new_candidate_instrumented_trajectories=0,new_unit_test_definitions=0,new_audio=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    assert result['previous_active_engine']['active_solver']=='crates/rf-d-circuit/src/direct_hybrid_solver.rs'
    write(ROOT/OUT,result);print('INCIDENCE_QA',len(sources),len(private),'selected nominal engine; ratios',ratio,selected_ratio,'receipt bytes',receipt_bytes)
if __name__=='__main__':main()
