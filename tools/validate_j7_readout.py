"""Admit passive J7 sampling without changing the protected electrical engine."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import recover,Sources
from check_hybrid_voice import unpack,US,compare
from check_j7_readout import audio,difference
from run_chain_startup import parse
from profile_execution_cost import numerical,final_state
from validate_joint_charge_seed import local_links
OUT='evidence/j7_readout_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    before=read('evidence/j7_readout_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'evidence').glob('j7_readout_native*.json'));assert names
    native=read(names[-1]);assert native['passed'] and native['electrical_identity'] and not native['real_time'] and not native['physical_fidelity'] and not native['bandlimited']
    for index,n in enumerate(names,1):
        r=read(n);images=recover(r)
        for name,data in images.items():
            now=(ROOT/name).read_bytes()
            if data==now:continue
            if name=='docs/J7_READOUT_PROTOCOLO.md':assert now.startswith(data),name
            elif name=='tools/j7_readout_probe.rs':
                normalized=data.replace(b'[32*US,8*US,4*US,2*US]',b'[32*US,8*US,4*US,2*US,US]').replace(b'[32*US,8*US]',b'[32*US,8*US,4*US,2*US,US]')
                assert normalized==now,name
            elif name=='tools/check_j7_readout.py' and index==1:
                expected=data.replace(b'bandlimited=False)',b"bandlimited=False,identity_receipt='evidence/j7_readout_native01.json',identity_receipt_sha256=sha(ROOT/'evidence/j7_readout_native01.json'),electrical_identity=True)").replace(b'for maximum in [32*US,8*US]:',b'for maximum in [4*US,2*US]:')
                assert expected==now,name
            else:raise AssertionError(name)
        assert r['temporary_area_empty'] and r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path'])) and r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
        if not r['passed']:
            replay=read(f'evidence/j7_readout_failure_replay{index:02d}.json');assert replay['passed'] and replay['native']==n and replay['native_sha256']==sha(ROOT/n) and not replay['relaxed_gates'] and replay['gate_failures'][0]==replay['gate_failures'][1]
            for name,data in recover(replay).items():assert data==images[name]
            a,b=r['failed_process'],r['unchanged_replay'];assert a['exit_code']==b['exit_code']==0 and a['stderr']==b['stderr']==''
            x,y=unpack(a['stdout']),unpack(b['stdout']);assert numerical(x)==numerical(y) and final_state(x)==final_state(y) and audio(x)==audio(y)
            try:difference(*(audio(unpack(p['stdout']))[0] for p in r['profiles']))
            except AssertionError as e:assert str(e)==replay['gate_failures'][0] and str(e) in r['failure']
            else:raise AssertionError('failed gate unexpectedly passed')
        for p in r['profiles']:assert parse(unpack(p['stdout']))['measurement']==p['measurement'] and audio(unpack(p['stdout']))[1]==p['readout_guards']
    diagnostic=read('evidence/j7_readout_grid_diagnostic01.json');assert not diagnostic['passed'] and diagnostic['diagnostic_complete'] and diagnostic['unchanged_replay'] and diagnostic['native_sha256']==sha(ROOT/names[0]) and diagnostic['gate_failures'][0]==diagnostic['gate_failures'][1] and not diagnostic['changes_to_equations']
    for name,data in recover(diagnostic).items():assert (ROOT/name).read_bytes()==data
    try:compare(*(parse(unpack(p['stdout']))['grid'] for p in read(names[0])['profiles']),True)
    except AssertionError as e:assert str(e)==diagnostic['gate_failures'][0]
    else:raise AssertionError('grid diagnostic unexpectedly passed')
    assert native['control']=='evidence/chain_startup_selected01.json' and native['control_sha256']==sha(ROOT/native['control']);control=read(native['control']);assert control['passed']
    identity=read(native['identity_receipt']);assert native['identity_receipt']==names[0] and native['identity_receipt_sha256']==sha(ROOT/names[0])
    identity_raw=unpack(identity['profiles'][0]['stdout']);identity_data=parse(identity_raw);other=unpack(control['profiles'][1]['stdout']);ref=parse(other)
    assert numerical(identity_raw)==numerical(other) and final_state(identity_raw)==final_state(other) and identity_data['dc']==ref['dc'] and identity_data['events']==ref['events']
    assert [p['maximum_full_ticks'] for p in native['profiles']]==[2*US,US];samples=[];guards=[];steps=[]
    for i,p in enumerate(native['profiles']):
        assert p['exit_code']==0 and p['stderr']=='';raw=unpack(p['stdout']);d=parse(raw);a,g=audio(raw);samples.append(a);guards.append(g);steps.append(d['measurement']['steps'])
        assert p['measurement']==d['measurement'] and p['readout_guards']==g
        final=list(map(float,final_state(raw)));assert a[0]==0. and a[-1]==final[115]+final[233]
        for e in d['events']:assert a[round(e[0]/(US*1000000)*48000)]==e[2+115]+e[2+233]
    assert native['inherited_profile_receipt']==names[1] and native['inherited_profile_receipt_sha256']==sha(ROOT/names[1]) and native['new_trajectories']==1
    assert json.dumps(native['profiles'][0],sort_keys=True)==json.dumps(read(names[1])['profiles'][1],sort_keys=True)
    assert steps[1]>steps[0] and difference(*samples)==native['refinement']
    tests=native['unit_tests'];assert tests['exit_code']==0 and tests['stderr']=='' and '2 passed; 0 failed' in unpack(tests['stdout']).decode()
    assert not list((ROOT/'tmp/lab-current').iterdir());size=sum((ROOT/n).stat().st_size for n in names+['evidence/j7_readout_before01.json','evidence/j7_readout_failure_replay01.json','evidence/j7_readout_grid_diagnostic01.json','evidence/j7_readout_failure_replay02.json']);assert size<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    assert set(native['source_sha256'])<=set(sources)
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/j7-offline-passive-readout/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),j7_readout_admitted=True,j7_readout_rate_hz=48000,j7_readout_samples_per_profile=4801,j7_readout_unit='V',j7_readout_span_s=.1,j7_readout_endpoint_inclusive=True,j7_readout_electrical_identity=True,j7_readout_refinement=native['refinement'],j7_readout_guards=guards,j7_readout_reference={n:sha(ROOT/n) for n in names},j7_readout_receipt_bytes_before_qa=size,j7_readout_receipt_budget_bytes=8*1024*1024,active_readout='crates/rf-d-circuit/src/j7_audio_readout.rs',active_readout_source_sha256=sources['crates/rf-d-circuit/src/j7_audio_readout.rs'],active_readout_origin_commit=None,active_readout_origin_commit_pending_self_commit=True,active_initializer_origin_commit=before['base_commit'],active_initializer_origin_commit_pending_self_commit=False,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=False,new_j7_readout_trajectories=5,new_j7_readout_failure_replay_trajectories=2,j7_readout_finer_profile_reused=True,j7_readout_nominal_maximum_full_h_s=2e-6,new_original_equation_rows=0,new_unit_test_definitions=2,new_unit_tests_executed=2,new_audio=False,new_audio_voltage_buffer=True,new_audio_export=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,bandlimited=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','active_voice_implementation','cost_ratio','inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    return result
def main():
    try:r=audit()
    except Exception:
        # Preserve this validator and repeat the unchanged assertions before any repair.
        s=Sources(['tools/validate_j7_readout.py']);r=dict(passed=False,**s.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/j7_readout_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/j7_readout_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('J7_READOUT_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['j7_readout_refinement'])
if __name__=='__main__':main()
