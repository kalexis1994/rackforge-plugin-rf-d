"""Admit own nominal chain startup, its memory seams and the self-contained caller."""
import base64,hashlib,json,struct,subprocess
from decimal import localcontext
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import recover
from run_chain_startup import parse
from run_chain_startup_selected import derive as selected_derive
from check_chain_startup_control import derive as control_derive
from check_chain_startup_guards import ledger
from check_hybrid_voice import unpack,compare
from profile_execution_cost import numerical,final_state
from check_hybrid_schur import comparison
from validate_joint_charge_seed import local_links
OUT='evidence/chain_startup_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def bits(v):return struct.pack('<'+str(len(v))+'d',*v)
def main():
    before=read('evidence/chain_startup_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/chain_startup_native01.json','evidence/chain_startup_native02.json','evidence/chain_startup_audit01.json','evidence/chain_startup_control01.json','evidence/chain_startup_guards01.json','evidence/chain_startup_guards02.json','evidence/chain_startup_selected01.json'];failed,native,audit,control,guards,selected_guards,selected=[read(n) for n in names]
    images=[recover(r) for r in [failed,native,audit,control,guards,selected_guards,selected]]
    startup='crates/rf-d-circuit/src/nominal_chain_startup.rs';probe='tools/chain_startup_probe.rs'
    old_helper='rf_d_circuit::mixer_chain66_direct::initial_state(p.mixer,[0.;5],p.circuit,p.conversion,p.headphone,p.boundary,lab::SEED)?'
    new_helper='rf_d_circuit::circuit66::initial_state(p.circuit,p.conversion,p.headphone,p.boundary,lab::SEED)?'
    for image in images:
        for n,data in image.items():
            now=(ROOT/n).read_bytes()
            if data==now:continue
            if n==startup:assert now.startswith(data) and now[len(data):].startswith(b'\n/// Numerical guesses only'),n
            elif n==probe:assert data.count(old_helper.encode())==1 and data.replace(old_helper.encode(),new_helper.encode(),1)==now,n
            else:raise AssertionError(n)
    assert not failed['passed'] and failed['failed_phase']=='trajectory' and len(failed['profiles'])==1
    a=failed['failed_process'];b=failed['unchanged_replay'];assert a['exit_code']==b['exit_code']!=0 and a['stderr']==b['stderr']=='Error: "BLOCK_SEED:InvalidInput"\n' and unpack(a['stdout'])==unpack(b['stdout'])==b''
    assert native['passed'] and not native['uses_40ms_projected_seed'] and len(native['profiles'])==2
    grids=[];roots=[]
    for p in native['profiles']:
        data=parse(unpack(p['stdout']));assert p['measurement']==data['measurement'] and p['dc']==data['dc'] and p['exit_code']==0;grids.append(data['grid']);roots.append(data['roots'])
        assert bits(data['roots'][0][3:239])==bits(data['dc'][0]['state'])
        for event in data['events']:
            following=[x for x in data['roots'] if x[0]==event[0]*(125e-9/65536)];assert len(following)==2 and all(x[2]==event[1] and bits(x[3:239])==bits(event[2:]) for x in following)
    assert canonical(compare(grids[0],grids[1],True))==canonical(native['refinement'])
    first=parse(unpack(native['profiles'][0]['stdout']));x,y=[d['state'] for d in first['dc']];root_error=max(abs((x[k]-y[k])+(x[118+k]-y[118+k])) for k in range(118));assert root_error<=1e-6
    assert audit['passed'] and audit['native']==names[1] and audit['native_sha256']==sha(ROOT/names[1]) and audit['original_rows']==8806 and audit['dc_rows']==238 and audit['dynamic_rows']==8568
    assert len(audit['dc'])==2 and all(d['rows']==119 and d['residual_a']<=20e-12 and d['correction_v']<=2e-9 for d in audit['dc'])
    assert len(audit['profiles'])==2 and all(p['pairs']==18 and p['original_rows']==4284 and p['max_residual_a']<=20e-12 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    assert len(audit['initial_and_key_seams'])==4 and all(s['state_bits_preserved'] for s in audit['initial_and_key_seams'])
    assert control['passed'] and not control['admission_benchmark'] and control['native_sha256']==sha(ROOT/names[1]);raw=unpack(control['stdout']);other=unpack(native['profiles'][1]['stdout']);data=parse(raw);reference=parse(other)
    assert data['measurement']==control['measurement'] and numerical(raw)==numerical(other) and final_state(raw)==final_state(other) and data['dc']==reference['dc'] and data['events']==reference['events']
    assert comparison(data['grid'],reference['grid'],raw,other)==control['comparison']
    assert (ROOT/'tools/chain_startup_control.rs').read_bytes()==control_derive().encode()
    for r,n in [(guards,18),(selected_guards,22)]:
        assert r['passed'] and r['native_sha256']==sha(ROOT/names[1]) and r['guards']==dict(rejections=n,exact_retries=n,heap_allocations=0)
        assert list(map(int,unpack(r['stdout']).decode().strip().split(',')[1:]))==[n,n,0]
        guess=list(map(float,next(s for s in unpack(native['profiles'][0]['stdout']).decode().splitlines() if s.startswith('SEED,0,')).split(',')[2:]))
        assert unpack(r['input'])==struct.pack('<472d',*x,*guess)
        with localcontext() as ctx:ctx.prec=100;assert r['initial_memories']==ledger(x)
    assert selected['passed'] and selected['self_contained_cold_start'] and not selected['uses_40ms_projected_seed'] and selected['native_sha256']==sha(ROOT/names[1])
    assert len(selected['profiles'])==2 and (ROOT/'tools/chain_startup_selected.rs').read_bytes()==selected_derive().encode()
    for p,c in zip(selected['profiles'],native['profiles']):
        raw=unpack(p['stdout']);other=unpack(c['stdout']);data=parse(raw);reference=parse(other)
        assert numerical(raw)==numerical(other) and final_state(raw)==final_state(other) and data['dc']==reference['dc'] and data['events']==reference['events'] and p['measurement']==data['measurement']
    assert canonical(selected['refinement'])==canonical(native['refinement'])
    for r in [failed,native,control,guards,selected_guards,selected]:
        assert r['temporary_area_empty'] and r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
        assert r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    assert not list((ROOT/'tmp/lab-current').iterdir());receipt_bytes=sum(p.stat().st_size for p in (ROOT/'evidence').glob('chain_startup*.json') if p!=ROOT/OUT);assert receipt_bytes<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for r in [failed,native,audit,control,guards,selected_guards,selected]:assert set(r['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/own-nominal-chain-startup/admitted-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),chain_startup_admitted=True,chain_startup_self_contained_api=True,chain_startup_uses_40ms_projected_seed=False,chain_startup_initial_root_error_v=root_error,chain_startup_original_rows=8806,chain_startup_linear_memories=24,chain_startup_junction_memories=12,chain_startup_dc_guards=selected_guards['guards'],chain_startup_heap_allocations=0,chain_startup_selected_exact_replays=12,chain_startup_selected_atomic_rejections=10,chain_startup_historical_observations_identical=True,chain_startup_reference={n:sha(ROOT/n) for n in names},chain_startup_receipt_bytes_before_qa=receipt_bytes,chain_startup_receipt_budget_bytes=8*1024*1024,active_initializer=startup,active_initializer_entry='nominal_chain_startup::cold_start',active_initializer_source_sha256=sources[startup],active_initializer_origin_commit=None,active_initializer_origin_commit_pending_self_commit=True,active_initializer_admission_receipt=OUT,active_solver_origin_commit=before['base_commit'],active_solver_origin_commit_pending_self_commit=False,inherited_tests_reexecuted=False,inherited_global_trajectories_reexecuted=False,inherited_global_trajectory_reexecutions=0,inherited_global_trajectory_suite_reexecuted=False,new_original_250_node_trajectories=0,inherited_private_hashes_recomputed=False,new_startup_candidate_trajectories=2,new_startup_selected_trajectories=2,new_startup_historical_control_trajectories=1,new_startup_failed_preparation_attempts=1,new_unit_test_definitions=0,new_audio=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','active_voice_implementation','cost_ratio','inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    write(ROOT/OUT,result);print('CHAIN_STARTUP_QA',len(sources),len(private),'own DC and full 0-100ms admitted; original rows 8806; bytes',receipt_bytes)
if __name__=='__main__':main()
