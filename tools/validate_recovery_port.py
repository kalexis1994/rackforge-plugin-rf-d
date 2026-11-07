"""Scoped nonlinear-port admission, failure history and protected corpus audit."""
import base64,hashlib,json,subprocess,shutil,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from validate_joint_charge_seed import local_links
from check_recovery_port_native import summarize_bench
OUT='evidence/recovery_port_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    before=read('evidence/recovery_port_before01.json');old=read(before['previous_qa']);assert old['passed'] and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'];saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,v in saved.items():assert(ROOT/n).read_bytes().startswith(v),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256'];lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';assert sha(ROOT/lib)==private[lib]
    reports=['evidence/recovery_port_model01.json','evidence/recovery_port_input_model02.json','evidence/recovery_port_analysis01.json','evidence/recovery_port_fast_native03.json','evidence/recovery_port_fast_analysis01.json'];values=[]
    for name in reports:
        r=read(name);assert r['passed'],name
        for n,v in recover(r).items():assert(ROOT/n).read_bytes()==v,(name,n)
        values.append(r)
    eight,twelve,analysis,fast,fast_analysis=values
    for r in [eight,twelve,fast]:
        assert r['compiler_sha256']==old['compiler']['sha256'] and r['library_sha256']==private[lib] and r['temporary_area_empty']
    for r in [eight,twelve]:
        assert r['native']['exit_code']==0 and r['native']['output_bytes']==65*4692*8<=32*1024**2
        assert len(unpack(r['native']['input']))==65*136*8 and r['native_law_identity']['directions']==64
        assert r['native_law_identity']['max_jacobian_error_s']<=1e-10
        assert len(r['independent_stages'])==48
        for p in r['independent_stages']:assert p['node_error_v']<=1e-9 and p['kcl_a']<=1e-12 and p['charge_error_v']<=1e-11 and p['jacobian_fd_scaled']<=1
        assert len(r['reserved_profiles'])==9
        for p in r['reserved_profiles']:
            expected=p['amplitude_v']==.01 or(r is twelve and p['amplitude_v']==.1);assert p['domain_admitted']==expected
            if not expected:assert p['unchanged_replay_identical']
        for n,h in r['generated_sha256'].items():assert sha(ROOT/n)==h
        assert r['retained_charge_coordinates']==18 and not r['full_voice_rt'] and not r['hardware_fidelity']
    assert eight['nonlinear_junctions']==8 and twelve['nonlinear_junctions']==12
    for r in [analysis,fast_analysis]:
        assert r['passed'] and len(r['production_comparisons'])==3 and r['production_sparse_node_coverage'] and r['no_reference_state_seeding'] and not r['cost_admitted'] and not r['whole_voice_rt'] and not r['dynamic_cutoff_admitted']
        for p in r['production_comparisons']:assert p['domain_admitted'] and p['sparse_nodes']['node_gate_pass'] and p['dense_ports']['audio_gate_pass'] and p['dense_ports']['panel_gate_pass'] and p['partial_maps']==124
        for p in r['implementation_comparisons']:assert p['node_error_v']<=1e-10 and p['charge_error_v']<=1e-11 and p['panel_error_a']<=1e-14
    assert fast['signed_bit_reject_fixtures']==24 and fast['exact_retries']==24 and fast['root_budget_rejection_included'] and fast['heap_allocations_vectors']==0 and fast['ports_match_nodes_by_bits']
    for p in fast['implementation_comparisons']:assert p['node_error_v']<=1e-10 and p['charge_error_v']<=1e-11 and p['panel_error_a']<=1e-14
    failed_native=read('evidence/recovery_port_native01.json');assert not failed_native['passed'] and failed_native['vectors']['exit_code']==0 and failed_native['bench']['exit_code']==0 and failed_native['unchanged_replay']['exit_code']==0
    snapshots=recover(failed_native);assert {n for n,v in snapshots.items() if(ROOT/n).read_bytes()!=v}=={'tools/check_recovery_port_native.py'}
    assert analysis['cost']==summarize_bench(unpack(failed_native['bench']['stdout'])) and analysis['unchanged_replay_cost']==summarize_bench(unpack(failed_native['unchanged_replay']['stdout']))
    failed_input=read('evidence/recovery_port_input_model01.json');assert not failed_input['passed'] and failed_input['failure'].splitlines()[-1]==failed_input['unchanged_replay_failure'].splitlines()[-1];snapshots=recover(failed_input);assert {n for n,v in snapshots.items() if(ROOT/n).read_bytes()!=v}=={'tools/check_recovery_port_input.py'}
    compile_failures=[read(f'evidence/recovery_port_fast_native{k:02d}.json') for k in [1,2]]
    for r in compile_failures:
        assert not r['passed'] and r['compile']['exit_code']!=0;snapshots=recover(r);assert {n for n,v in snapshots.items() if(ROOT/n).read_bytes()!=v}=={'tools/recovery_port_fast_kernel.rs'}
    assert unpack(compile_failures[0]['compile']['stderr'])==unpack(compile_failures[1]['compile']['stderr']) and compile_failures[0]['source_sha256']==compile_failures[1]['source_sha256']
    for path in (ROOT/'evidence').glob('recovery_port_qa_failure*.json'):
        failed=read(path.relative_to(ROOT).as_posix());assert not failed['passed'] and failed['failure'].splitlines()[-1]==failed['unchanged_replay'].splitlines()[-1];assert set(recover(failed))=={'tools/validate_recovery_port.py'}
    assert analysis['cost']['deadline_misses']==1200 and fast['cost']['deadline_misses']==29 and fast['cost']==fast_analysis['cost']==summarize_bench(unpack(fast['bench']['stdout']))
    for c in [analysis['cost'],analysis['unchanged_replay_cost'],fast['cost']]:assert c['blocks']==1200 and c['first_included'] and c['heap_allocations']==0 and not c['target_50_percent_pass']
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'] and not list((ROOT/'tmp/lab-current').iterdir()) and shutil.disk_usage(ROOT).free>1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    retained=sum(p.stat().st_size for p in(ROOT/'evidence').glob('recovery_port*') if p!=ROOT/OUT);assert retained<=8*1024**2,retained
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and(not k.startswith('new_') or k=='new_listening')}
    r.update(schema='rf-d/nonlinear-recovery-input-ports/v1',passed=True,passed_means_scoped_reserved_nodes_and_ports_with_cost_rejection=True,base_commit=before['base_commit'],previous_qa=before['previous_qa'],previous_qa_sha256=sha(ROOT/before['previous_qa']),source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_charge_control_origin_commit=before['base_commit'],experimental_charge_control_origin_commit_pending_self_commit=False,experimental_recovery_port_origin_commit=None,experimental_recovery_port_origin_commit_pending_self_commit=True,experimental_recovery_port_scope='Static cutoff .49/.5/.51 R61=200/L1 R14=25k; six Ebers-Moll BJT nonlinear, other devices local;18 charges; twelve junctions; .01/.1 V four-ms reservations at250ns and .1 V384k with sparse68-node coverage and dense ports;1 V and runtime rejected, no whole-voice or dynamic-control admission',experimental_recovery_port_retained_receipt_bytes=retained,experimental_recovery_port_reference={n:sha(ROOT/n) for n in reports},experimental_recovery_port_static_reserves_admitted=6,experimental_recovery_port_large_level_reserves_rejected=3,experimental_recovery_port_cost_original=analysis['cost'],experimental_recovery_port_cost_compact=fast['cost'],experimental_recovery_port_cost_admitted=False,experimental_recovery_port_production_comparisons=fast_analysis['production_comparisons'],experimental_recovery_port_fault_receipts_preserved=True,new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,inherited_test_count=old['covered_test_count'],covered_test_count=old['covered_test_count'],inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_native_trajectory_count=0,new_native_stamp_directions=128,new_native_rust_vector_steps=9222,real_time=False,physical_fidelity=False,physical_cv_general=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    return r

if __name__=='__main__':
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_recovery_port.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/recovery_port_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/recovery_port_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('RECOVERY_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_recovery_port_retained_receipt_bytes'])
