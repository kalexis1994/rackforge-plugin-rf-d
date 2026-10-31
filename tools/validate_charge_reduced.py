"""Admit local charge reduction and measured block cost, never whole-voice RT."""
import base64,hashlib,json,subprocess,shutil,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from vco_family import decode_window
from validate_joint_charge_seed import local_links
OUT='evidence/charge_reduced_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    before=read('evidence/charge_reduced_before01.json');old=read(before['previous_qa']);assert old['passed'] and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'];saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,v in saved.items():assert(ROOT/n).read_bytes().startswith(v),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    reports=['evidence/charge_reduced_oracle02.json','evidence/charge_reduced_derivation01.json','evidence/charge_reduced_domain01.json','evidence/charge_reduced_native01.json','evidence/charge_reduced_validation01.json','evidence/charge_reduced_retirement01.json']
    for name in reports:
        r=read(name);assert r['passed'],name
        for n,v in recover(r).items():assert(ROOT/n).read_bytes()==v,(name,n)
    oracle,derivation,domain,native,validation,retirement=map(read,reports)
    assert oracle['compiler_sha256']==native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
    lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';assert oracle['library_sha256']==native['library_sha256']==private[lib]==sha(ROOT/lib)
    failed=read('evidence/charge_reduced_oracle01.json');assert not failed['passed'] and 'E0277' in failed['failure'] and 'E0277' in unpack(failed['unchanged_replay']['stderr']).decode();original=recover(failed)['tools/charge_reduced_oracle.rs'];left,right=original.rsplit(b'1e-6)?;',1);assert left+b'1e-6).map_err(|e|format!("STAMP:{e:?}"))?;'+right==(ROOT/'tools/charge_reduced_oracle.rs').read_bytes()
    assert len(oracle['profiles'])==8 and len(derivation['models'])==2 and len(domain['profiles'])==8 and len(validation['production_clock_comparisons'])==4
    for m in derivation['models']:
        assert len(m['c'])==18 and len(m['coordinate_inverse'])==68 and len(m['frequency_checks'])==33 and len(m['discrete_checks'])==8 and m['mass_error_f']<=1e-20 and m['poles_real_max_per_s']<0
        assert max(p['max_scaled_error'] for p in m['frequency_checks'])<=1 and all(x['node_error_v']<=1e-11 and x['charge_balance_c']<=1e-20 and x['algebraic_kcl_a']<=1e-12 for x in m['discrete_checks'])
    for n,h in derivation['generated_sha256'].items():assert sha(ROOT/n)==h
    assert domain['reduced_parameters_fitted_to_reserved_cases'] is False and all(p['nonlinear_domain_admitted'] and p['all_nodes_error_v']<=1e-6 for p in domain['profiles'])
    pack=ROOT/domain['compact_pack'];assert sha(pack)==domain['compact_sha256']==retirement['compact_sha256']
    for p in domain['profiles']:
        assert np.isfinite(decode_window(p['full_state_window'],pack)).all() and np.isfinite(decode_window(p['signal_window'],pack)).all() and p['full_original_rows_not_all_retained']
    assert not(ROOT/retirement['retired_path']).exists() and retirement['retired_sha256']==oracle['pack_sha256'] and retirement['protected_inputs_retired']==0 and retirement['original_full_grid_not_reconstructible_from_compact'] and retirement['all_selected_full_states_verified_before_retirement']
    assert native['temporary_area_empty'] and native['signed_bit_reject_fixtures']==12 and native['exact_retries']==12 and not native['whole_voice_realtime']
    assert all(c['blocks']==1200 and c['deadline_misses']==0 and c['target_50_percent_pass'] and c['heap_allocations']==0 for c in native['costs'])
    assert validation['all_native_published_outputs_equal_reconstructed_ports_by_bits'] and validation['all_eight_nonlinear_reserves_admitted'] and validation['no_whole_voice_admission']
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'] and not list((ROOT/'tmp/lab-current').iterdir()) and shutil.disk_usage(ROOT).free>1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and retirement['retired_path'] not in staged and not any(n.endswith('.wav') for n in staged)
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('charge_reduced*') if p!=ROOT/OUT);assert size<=16*1024**2
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and(not k.startswith('new_') or k=='new_listening')}
    r.update(schema='rf-d/local-charge-reduced-kernel/v1',passed=True,base_commit=before['base_commit'],previous_qa=before['previous_qa'],previous_qa_sha256=sha(ROOT/before['previous_qa']),source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_mono_origin_commit=before['base_commit'],experimental_mono_origin_commit_pending_self_commit=False,experimental_charge_reduced_origin_commit=None,experimental_charge_reduced_origin_commit_pending_self_commit=True,experimental_charge_reduced_scope='Local linearization of fixed-control loaded68 chain;18 capacitor voltage increments and50 eliminated algebraic coordinates; two operating points, small-signal multisine reserves,384kHz perturbation output+48kHz FIR; no VCO/contours/large-signal or whole-voice RT admission',experimental_charge_reduced_capacitors=18,experimental_charge_reduced_algebraic_variables=50,experimental_charge_reduced_models=2,experimental_charge_reduced_frequency_checks=66,experimental_charge_reduced_direct_discrete_checks=16,experimental_charge_reduced_native_nonlinear_trajectories=8,experimental_charge_reduced_nonlinear_worst_node_error_v=max(p['all_nodes_error_v'] for p in domain['profiles']),experimental_charge_reduced_production_full_node_comparison_is_sparse=True,experimental_charge_reduced_costs=native['costs'],experimental_charge_reduced_block_budget_observed_pass=True,experimental_charge_reduced_retired_unadmitted_bytes=retirement['retired_bytes'],experimental_charge_reduced_retained_receipt_bytes=size,experimental_charge_reduced_reference={n:sha(ROOT/n) for n in reports},new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,inherited_test_count=old['covered_test_count'],covered_test_count=old['covered_test_count'],inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_native_trajectory_count=8,real_time=False,physical_fidelity=False,physical_cv_general=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    return r
if __name__=='__main__':
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_charge_reduced.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/charge_reduced_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/charge_reduced_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('CHARGE_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_charge_reduced_retained_receipt_bytes'])
