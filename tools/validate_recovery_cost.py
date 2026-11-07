"""Audit same-law numerical results, observed cost rejection and frozen inputs."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_recovery_cost import bench,read,decode,digest
from validate_joint_charge_seed import local_links
OUT='evidence/recovery_cost_tests01.json'

def audit():
    before=read('evidence/recovery_cost_before01.json');old=read(before['previous_qa']);saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()};assert old['passed'] and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,v in saved.items():assert (ROOT/n).read_bytes().startswith(v),n
    private=old['private_input_sha256'];lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';assert len(private)==8769 and all((ROOT/n).is_file() for n in private) and sha(ROOT/lib)==private[lib] and sha(Path(old['compiler']['path']))==old['compiler']['sha256']
    variants=['baseline01','joint03','predict01','static01','exp_native01','fir_native01'];records={}
    def receipt(s):return f'evidence/recovery_cost_{s}.json'
    for k in variants:
        r=read(receipt(k));records[k]=r;assert r['passed'] and r['temporary_area_empty'] and not r['whole_voice_rt'] and r['retained_charge_coordinates']==18 and r['constitutive_laws']==12
        assert r['compiler_sha256']==old['compiler']['sha256'] and r['library_sha256']==private[lib] and r['compile']['exit_code']==0
        for name,data in recover(r).items():
            if name not in ['tools/recovery_cost_probe.rs','tools/check_recovery_cost.py']:assert(ROOT/name).read_bytes()==data,(k,name)
        if k!='fir_native01':
            assert r['signed_bit_rejections']==42 and r['exact_valid_retries']==30
            for key in ['vectors','stress']:
                a=np.frombuffer(decode(r,key),'<f8');assert len(a)==3*1537*93 and np.isfinite(a).all()
                for p in r[key]['python_comparison']:assert p['node_error_v']<=1e-10 and p['panel_error_a']<=1e-14 and p['charge_error_v']<=1e-11
        if k in ['joint03','predict01','static01','exp_native01']:
            assert all(p['max_scaled_error']<=1 for p in r['laws']['comparisons'])
        if k in ['joint03','predict01','static01']:
            assert len(r['stages']['comparisons'])==(48 if k=='joint03' else 96)
            assert digest(unpack(r['stages']['data']))==r['stages']['sha256']
            for p in r['stages']['comparisons']:assert max(p['reported_residual'],p['recomputed_residual'])<=2e-13 and p['hybrid_kcl_a']<=1e-12 and p['charge_error_v']<=1e-11
        if 'cost' in r:
            assert r['cost']==bench(unpack(r['bench']['stdout'])) and not r['cost']['target_50_percent_pass']
            if k!='baseline01':assert r['unchanged_rejected_cost_replay']['cost']==bench(unpack(r['unchanged_rejected_cost_replay']['stdout']))
        else:
            assert not r['observed_cost_admitted']
            for mode,blocks in [('bench',1200),('long',4800)]:
                if mode not in r:continue
                item=r[mode];assert item['cost']==bench(unpack(item['stdout']),blocks)
                if not item['cost']['target_50_percent_pass']:assert item['unchanged_rejected_replay']['cost']==bench(unpack(item['unchanged_rejected_replay']['stdout']),blocks)
    exp=records['exp_native01'];fir=records['fir_native01'];assert exp['physical_admitted'] and len(exp['physical'])==3
    for p in exp['physical']:
        assert p['admitted'] and p['partial_maps']==124 and p['uses_only_own_rust_state'] and p['physical_sparse_nodes']['node_gate_pass'] and p['physical_dense_ports']['audio_gate_pass'] and p['physical_dense_ports']['panel_gate_pass'] and p['temporal_same_hybrid_dense_nodes']['node_gate_pass']
    assert digest(unpack(exp['endpoints']['data']))==exp['endpoints']['sha256'] and len(exp['endpoints']['comparisons'])==48
    for p in exp['endpoints']['comparisons']:assert max(p['reported_residual'],p['recomputed_residual'])<=2e-13 and p['algebraic_kcl_a']<=1e-12 and p['balance_v']<=1e-11 and p['charge_error_v']<=1e-11
    assert exp['bench']['cost']['target_50_percent_pass'] and exp['long']['cost']['deadline_misses']==1 and not exp['long']['cost']['target_50_percent_pass']
    assert fir['same_kernel_report_sha256']==sha(ROOT/receipt('exp_native01')) and fir['fir_check']['frames']==9288 and fir['fir_check']['voltage_and_indices_bit_exact'] and fir['fir_check']['atomic_invalid_input']
    for key in ['vectors','stress']:assert fir[key]['bit_exact'] and fir[key]['sha256']==exp[key]['sha256']
    assert fir['stages']['sha256']==exp['endpoints']['sha256']
    maps=read(receipt('exp_maps01'));assert maps['passed']
    for n,h in maps['generated_sha256'].items():assert sha(ROOT/n)==h
    for n,v in recover(maps).items():assert(ROOT/n).read_bytes()==v,n
    for p in maps['checks']:assert p['projection_error']<=1e-11 and max(p['imaginary_error'],p['semigroup_error'],p['identity_scaled'],p['eigen_residual'])<=1e-10
    for p in maps['independent']:assert max(p['relative_column_errors'])<=1e-10
    for key in ['joint01','joint02','exp_maps_failure01','exp_maps_failure02']:
        failed=read(receipt(key));assert not failed['passed'];recover(failed)
        if key.startswith('exp_maps'):assert failed['unchanged_replay_identical'] and failed['runs'][0]==failed['runs'][1]
        elif key=='joint02':assert failed['unchanged_failure_replay']['identical_to_failed_output'] and digest(unpack(failed['failed_output']))==failed['failed_output_sha256'] and failed['failure'].splitlines()[-1]==failed['unchanged_failure_replay']['analysis_failure'].splitlines()[-1]
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'] and not list((ROOT/'tmp/lab-current').iterdir())
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    retained=sum(p.stat().st_size for p in (ROOT/'evidence').glob('recovery_cost*') if p!=ROOT/OUT);assert retained<=10*1024**2,retained
    source={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert digest(subprocess.check_output(['git','show',':'+n],cwd=ROOT))==source[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and (not k.startswith('new_') or k=='new_listening')}
    r.update(schema='rf-d/recovery-cost-same-law/v1',passed=True,passed_means_same_law_and_observed_cost_rejections=True,base_commit=before['base_commit'],previous_qa=before['previous_qa'],previous_qa_sha256=sha(ROOT/before['previous_qa']),source_sha256=source,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_recovery_port_origin_commit=before['base_commit'],experimental_recovery_port_origin_commit_pending_self_commit=False,experimental_recovery_cost_origin_commit=None,experimental_recovery_cost_origin_commit_pending_self_commit=True,experimental_recovery_cost_admitted=False,experimental_recovery_cost_candidate='semilinear exponential FOH of nonlinear currents, one implicit endpoint, original FIR',experimental_recovery_cost_physical_reserves=exp['physical'],experimental_recovery_cost_short=exp['bench']['cost'],experimental_recovery_cost_confirmation=exp['long']['cost'],experimental_recovery_cost_split_fir= fir['bench']['cost'],experimental_recovery_cost_retained_receipt_bytes=retained,experimental_recovery_cost_reports={receipt(k):sha(ROOT/receipt(k)) for k in variants+['exp_maps01']},real_time=False,physical_fidelity=False,physical_cv_general=False,covered_test_count=old['covered_test_count'],inherited_test_count=old['covered_test_count'],new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    return r

if __name__=='__main__':
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_recovery_cost.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/recovery_cost_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/recovery_cost_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('RECOVERY_COST_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_recovery_cost_retained_receipt_bytes'])
