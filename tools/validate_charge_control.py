"""Admit static reserves and retain dynamic/cost rejection explicitly."""
import base64,hashlib,json,subprocess,shutil,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from vco_family import decode_window
from analyse_charge_control import audit as analyse
from validate_joint_charge_seed import local_links
OUT='evidence/charge_control_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    before=read('evidence/charge_control_before01.json');old=read(before['previous_qa']);assert old['passed'] and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'];saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,v in saved.items():assert(ROOT/n).read_bytes().startswith(v),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    reports=['evidence/charge_control_native01.json','evidence/charge_control_preparation01.json','evidence/charge_control_rust01.json','evidence/charge_control_refinement01.json','evidence/charge_control_analysis01.json','evidence/charge_control_exponential01.json','evidence/charge_control_exp_rust01.json','evidence/charge_control_exp_analysis01.json','evidence/charge_control_step_defect01.json']
    for name in reports:
        r=read(name);assert r['passed'],name
        for n,v in recover(r).items():assert(ROOT/n).read_bytes()==v,(name,n)
    original,preparation,native,fine,analysis,exponential,exp_native,exp_analysis,defect=map(read,reports)
    for r in [original,native,fine,exp_native]:
        assert r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']));lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';assert r['library_sha256']==private[lib]==sha(ROOT/lib) and r['temporary_area_empty']
    for n,h in preparation['generated_sha256'].items():assert sha(ROOT/n)==h
    assert preparation['no_parameter_interpolation'] and preparation['no_reserved_trajectory_fitting'] and len(original['models'])==3 and len(original['profiles'])==20
    assert len([p for p in original['profiles'] if p['domain_admitted']])==6
    for p in original['profiles']:
        assert p['exit_code']==0 and p['elapsed_s']<=240 and p['full_stream_bytes']<=32*1024**2 and p['full_grid_retired_after_metrics_and_selected_byte_checks']
        if not p['domain_admitted']:assert p['unchanged_native_replay']['identical'] and p['unchanged_native_replay']['stdout_sha256']==p['full_stream_sha256'] and p['unchanged_native_replay']['exit_code']==0
    for r in [original,fine]:
        assert sha(ROOT/r['pack'])==r['pack_sha256']
        for p in r['profiles']:
            assert np.isfinite(decode_window(p['state_window'],ROOT/r['pack'])).all() and np.isfinite(decode_window(p['signal_window'],ROOT/r['pack'])).all()
    assert fine['reference_converged'] and fine['original_250ns_replay_identical'] and fine['profiles'][-1]['reference_comparison']['domain_admitted']
    for p in fine['profiles']:assert p['full_grid_retired_after_metrics_and_selected_byte_checks'] and p['full_export_bytes']<=32*1024**2 and p['elapsed_s']<=240
    for k,v in analyse().items():assert analysis[k]==v,k
    assert analysis['charge_continuity_pass'] and not analysis['dynamic_cutoff_physical_admission'] and not analysis['cost_observed_admission'] and not analysis['whole_voice_rt'] and analysis['max_switch_charge_voltage_error_v']<=1e-12 and analysis['minimum_reset_negative_control_error_v']>1e-12
    assert native['signed_bit_reject_fixtures']==8 and native['exact_retries']==8 and native['conservative_relabel_checks']==6 and native['rust_python_node_error_v']<=1e-11 and native['rust_python_panel_error_a']<=1e-15 and native['physical_charge_coordinate_error_v']<=1e-11 and native['all_published_ports_match_nodes_by_bits']
    assert native['cost']['blocks']==1200 and native['cost']['heap_allocations']==0 and native['cost']['deadline_misses']>0 and not native['cost']['target_50_percent_pass']
    assert (ROOT/'tools/charge_control_exp_kernel.rs').read_bytes()==(ROOT/'tools/charge_control_kernel.rs').read_bytes().replace(b'charge_control_data.rs',b'charge_control_exp_data.rs')
    assert (ROOT/'tools/charge_control_exp_probe.rs').read_bytes()==(ROOT/'tools/charge_control_probe.rs').read_bytes().replace(b'charge_control_kernel.rs',b'charge_control_exp_kernel.rs')
    for n,h in exponential['generated_sha256'].items():assert sha(ROOT/n)==h
    for t in exponential['transitions']:assert t['eigen_residual']<=1e-10 and t['semigroup_error']<=1e-10 and t['identity_max_scaled_error']<=1
    assert exp_native['rust_python_node_error_v']<=1e-11 and exp_native['rust_python_panel_error_a']<=1e-15 and exp_native['cost']['target_50_percent_pass'] and exp_native['cost']['deadline_misses']==0 and exp_native['cost']['heap_allocations']==0
    assert not exp_analysis['dynamic_cutoff_physical_admission'] and not exp_analysis['dense_comparison']['domain_admitted'] and exp_analysis['dense_partial_transition_from_rust_state_not_reference']
    assert defect['results'][0]['local_linear_endpoint_defect_v']>1e-6 and defect['results'][1]['local_linear_endpoint_defect_v']<=1e-11 and defect['no_physical_or_rt_admission']
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'] and not list((ROOT/'tmp/lab-current').iterdir()) and shutil.disk_usage(ROOT).free>1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('charge_control*') if p!=ROOT/OUT);assert size<=12*1024**2,size
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and(not k.startswith('new_') or k=='new_listening')}
    r.update(schema='rf-d/charge-local-control-domain-rejection/v1',passed=True,passed_means_scoped_static_admission_and_explicit_rejections=True,base_commit=before['base_commit'],previous_qa=before['previous_qa'],previous_qa_sha256=sha(ROOT/before['previous_qa']),source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_charge_reduced_origin_commit=before['base_commit'],experimental_charge_reduced_origin_commit_pending_self_commit=False,experimental_charge_control_origin_commit=None,experimental_charge_control_origin_commit_pending_self_commit=True,experimental_charge_control_scope='Three own DC/G/M points R61=200/L1 cutoff .49/.50/.51; six static .01V reserves admitted; .1/1V, conservative dynamic switching and observed runtime rejected;18 compensated absolute capacitor-voltage coordinates, no VCO/contours/general control admission',experimental_charge_control_accepted_static_reserves=6,experimental_charge_control_rejected_level_reserves=12,experimental_charge_control_rejected_dynamic_reserves=2,experimental_charge_control_unchanged_replay_runs=14,experimental_charge_control_fine_reference_step_ns=analysis['fine_reference_step_ns'],experimental_charge_control_fine_reference_comparison=analysis['fine_reference_comparison'],experimental_charge_control_dynamic_comparison=analysis['candidate_at_fine_step'],experimental_charge_control_dynamic_admitted=False,experimental_charge_control_cost_admitted=False,experimental_charge_control_cost=native['cost'],experimental_charge_control_charge_continuity_error_v=analysis['max_switch_charge_voltage_error_v'],experimental_charge_control_reference={n:sha(ROOT/n) for n in reports},experimental_charge_control_retained_receipt_bytes=size,new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,inherited_test_count=old['covered_test_count'],covered_test_count=old['covered_test_count'],inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_native_trajectory_count=20+len(fine['profiles'])-1,new_native_run_count=20+14+len(fine['profiles']),real_time=False,physical_fidelity=False,physical_cv_general=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    r.update(experimental_charge_control_scope='Three own DC/G/M cutoff points and level reserves; static .01V admitted, higher levels and dynamic constitution rejected; compensated absolute charge coordinates; exponential FOH corrects local temporal defect and passes observed block budget, without VCO/contours/voice admission',experimental_charge_control_exponential_comparison=exp_analysis['dense_comparison'],experimental_charge_control_exponential_cost=exp_native['cost'],experimental_charge_control_exponential_block_budget_observed_pass=True,experimental_charge_control_method_endpoint_defects=defect['results'],experimental_charge_control_sdirk_rejections_retained=True)
    return r
if __name__=='__main__':
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_charge_control.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/charge_control_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/charge_control_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('CONTROL_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_charge_control_retained_receipt_bytes'])
