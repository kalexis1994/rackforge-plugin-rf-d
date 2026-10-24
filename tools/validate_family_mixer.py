"""Admit only measured conditional mixer/C27 continuations and protect earlier domains."""
import base64,hashlib,json,subprocess,traceback,shutil
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from vco_family import decode_window
from family_mixer_analysis import compare,capture_native,capture_spice,other_g,C
from validate_joint_charge_seed import local_links
OUT='evidence/family_mixer_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def audit():
    before=read('evidence/family_mixer_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256'] and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(x) for n,x in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    oracle=read('evidence/family_mixer_complete01.json');assert oracle['passed'] and len(oracle['cases'])==6 and len(oracle['method'])==2 and oracle['temporary_area_empty'] and sha(ROOT/oracle['pack'])==oracle['pack_sha256']
    for n,h in oracle['private_used_sha256'].items():assert h==private[n]==sha(ROOT/n)
    for n,h in oracle['reused_reference_sha256'].items():assert sha(ROOT/n)==h
    direct=read('evidence/family_mixer_oracle02.json');scaled=read('evidence/family_mixer_scaled_control01.json');assert not direct['passed'] and len(direct['cases'])==3 and 'unchanged_replay' in direct and scaled['passed'] and len(scaled['cases'])==2
    assert canonical([{k:v for k,v in x.items() if k!='window_pack'} for x in oracle['cases'][:3]])==canonical(direct['cases'])
    assert canonical({k:v for k,v in oracle['cases'][3].items() if k!='window_pack'})==canonical(scaled['cases'][1]['result'])
    initial=read('evidence/family_mixer_oracle01.json');diag=read('evidence/family_mixer_start_diagnostic01.json');assert not initial['passed'] and 'unchanged_replay' in initial and diag['passed'] and diag['max_index']==0 and diag['retained_window_max_kcl_a']<=1e-10
    methods=read('evidence/family_mixer_methods01.json');assert methods['passed'] and len(methods['cases'])==2 and not any(x['passed'] for x in methods['cases']) and all('unchanged_replay' in x for x in methods['cases'])
    for r in [initial,direct,methods,scaled,oracle]:
        recover(r);assert r['temporary_area_empty']
        assert sha(ROOT/r['pack'])==r['pack_sha256']
    derivation=read('evidence/family_mixer_coordinate_derivation01.json');assert derivation['passed'] and derivation['gates_unchanged'] and derivation['active_cards_unchanged']
    a=(ROOT/derivation['origin']).read_text(encoding='utf8')
    for x,y in derivation['changes']:assert a.count(x)==1;a=a.replace(x,y,1)
    assert(ROOT/derivation['derived']).read_bytes()==a.encode() and sha(ROOT/derivation['derived'])==derivation['derived_sha256']
    gen=read('evidence/family_mixer128_generation01.json');assert gen['passed'] and gen['training_count']==8 and not gen['reserved_data_used'] and gen['first_65_coefficients_bitwise_identical'] and gen['old_data_sha256']==sha(ROOT/'tools/vco_family_data.rs')
    for n,h in gen['generated_sha256'].items():assert sha(ROOT/n)==h
    for n,b in recover(gen).items():assert(ROOT/n).read_bytes()==b,n
    rejected=read('evidence/family_mixer_native01.json');assert not rejected['passed'] and 'unchanged_gate_replay' in rejected and rejected['temporary_area_empty']
    recover(rejected);assert sha(ROOT/rejected['pack'])==rejected['pack_sha256']
    native=read('evidence/family_mixer_native128_01.json');assert native['passed'] and len(native['profiles'])==12 and len(native['refinements'])==6 and native['temporary_area_empty'] and native['oracle_sha256']==sha(ROOT/'evidence/family_mixer_complete01.json')
    assert native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
    steps=read('evidence/family_mixer_steps01.json');assert steps['passed'] and steps['selected_roots']==24 and steps['new_trajectories']==0 and steps['native_sha256']==sha(ROOT/'evidence/family_mixer_native128_01.json')
    for n,b in recover(steps).items():assert(ROOT/n).read_bytes()==b,n
    for n,b in recover(native).items():assert(ROOT/n).read_bytes()==b,n
    assert sha(ROOT/native['pack'])==native['pack_sha256']
    allcmp=[];portmax=0.;negative=[False,False];rows=0
    for x in [*oracle['cases'],*oracle['method']]:
        raw=decode_window(x['window'],ROOT/x['window_pack']);_,m=capture_spice(raw,x['load'])
        # Full settled crossings outside the retained window belong to the original receipt.
        assert abs(m['start_s']-x['measurements']['start_s'])<=1e-16 and np.max(abs(raw[:,6]))<=.125
        original=(raw[:,6]-raw[:,5])/33000.;other=other_g(x['load'])*raw[:,6];actual=original+other+raw[:,7]
        assert np.max(abs(actual))<=1e-10
        negative[0]|=bool(np.max(abs(2*original+other+raw[:,7]))>1e-10);negative[1]|=bool(np.max(abs(original+other-raw[:,7]))>1e-10)
        assert x['exit_code']==0 and x['elapsed_s']<=180 and x['export_bytes']<256*1024**2;rows+=len(raw)
    assert all(negative)
    for i,x in enumerate(native['profiles']):
        assert x['scene']==i//2 and x['step_ns']==[500,250][i%2] and x['heap_allocations']==0 and x['exact_retry'] and x['atomic_rejections']==3 and x['elapsed_s']<=240
        raw=decode_window(x['window'],ROOT/native['pack']);m=capture_native(raw);assert canonical(m)==canonical(x['measurements']);comp=compare(m,oracle['cases'][x['scene']]['measurements']);assert canonical(comp)==canonical(x['comparison']);allcmp.append(comp)
        assert np.max(raw[:,12:14])<=1 and np.max(abs(raw[:,7]+raw[:,8]+raw[:,9]))<=1e-18
        for k in [0,len(raw)//2,len(raw)-1]:
            saw,bus=raw[k,3],raw[k,2];res=[33000]+([33000,33000,11000] if x['scene']%2 else []);sources=[saw]+[0.]*(len(res)-1);y=np.diag([2/12500.+1/r for r in res]);rhs=np.array([v/12500.+bus/r for v,r in zip(sources,res)]);w=np.linalg.solve(y,rhs);curr=np.array([(bus-z)/r for z,r in zip(w,res)]);error=max(abs(curr[0]-raw[k,7]),abs(sum(curr[1:])+bus/33000.-raw[k,8]));assert error<=1e-18;portmax=max(portmax,float(error))
        rows+=len(raw)
    for i in range(6):assert canonical(compare(native['profiles'][2*i]['measurements'],native['profiles'][2*i+1]['measurements']))==canonical(native['refinements'][i])
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'] and not list((ROOT/'tmp/lab-current').iterdir()) and shutil.disk_usage(ROOT).free>1024**3
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('family_mixer*') if p.is_file() and p!=ROOT/OUT);assert size<=32*1024**2,size
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and (not k.startswith('new_') or k=='new_listening')}
    r.update(schema='rf-d/conditional-family-mixer-c27/v1',passed=True,base_commit=before['base_commit'],previous_qa=before['previous_qa'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_stationary_family_origin_commit=before['base_commit'],experimental_stationary_family_origin_commit_pending_self_commit=False,experimental_family_mixer_origin_commit=None,experimental_family_mixer_origin_commit_pending_self_commit=True,experimental_family_mixer_admitted=True,experimental_family_mixer_scope='Six fixed-CV conditional ON mixer/C27 windows, BASE_Q29 imposed zero; H128 continuations from shared late C27 memory. No full filter, independent reduced startup, general CV/BUS dynamics, hardware fidelity or RT',experimental_family_mixer_rejected_h64=True,experimental_family_mixer_harmonics=128,experimental_family_mixer_scenes=6,experimental_family_mixer_native_profiles=12,experimental_family_mixer_receipt_bytes=size,experimental_family_mixer_worst_frequency_cents=max(x['frequency_error_cents'] for x in allcmp),experimental_family_mixer_worst_bus_v=max(max(x['signals']['bus'].values()) for x in allcmp),experimental_family_mixer_worst_current_a=max(max(x['signals'][name].values()) for x in allcmp for name in ['panel_bus','other','c27','keyboard']),experimental_family_mixer_panel_mna_error_a=portmax,experimental_family_mixer_reference={n:sha(ROOT/n) for n in ['evidence/family_mixer_complete01.json','evidence/family_mixer_native128_01.json','evidence/family_mixer128_generation01.json']},new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,covered_test_count=old['covered_test_count'],inherited_test_count=old['covered_test_count'],inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,new_reduced_trajectories=12,independent_reduced_startup=False,negative_controls_rejected=['duplicated_R45','reversed_C27_current'],new_original_equation_rows=0,real_time=False,physical_fidelity=False,physical_cv_general=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    return r
def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_family_mixer.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/family_mixer_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/family_mixer_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('FAMILY_MIXER_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_family_mixer_receipt_bytes'])
if __name__=='__main__':main()
