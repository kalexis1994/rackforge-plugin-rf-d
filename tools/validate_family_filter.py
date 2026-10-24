"""Scoped admission of the real filter input and its charge-consistent integrator."""
import base64,hashlib,json,subprocess,traceback,shutil
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from vco_family import decode_window
from validate_joint_charge_seed import local_links
OUT='evidence/family_filter_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    b=read('evidence/family_filter_before01.json');old=read(b['previous_qa']);assert old['passed'] and sha(ROOT/b['previous_qa'])==b['previous_qa_sha256'] and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==b['base_commit']
    saved={n:base64.b64decode(v) for n,v in b['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,v in saved.items():assert(ROOT/n).read_bytes().startswith(v),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    reports=['evidence/family_filter_native01.json','evidence/family_filter_reference01.json','evidence/family_filter_sdirk_native01.json','evidence/family_filter_sdirk_reference01.json','evidence/family_filter_cycles01.json','evidence/family_filter_retry01.json','evidence/family_filter_sdirk_derivation01.json','evidence/family_filter_constraint_diagnostic01.json']
    for name in reports:
        r=read(name);assert r['passed'],name
        for n,v in recover(r).items():assert(ROOT/n).read_bytes()==v,(name,n)
    trap=read(reports[0]);reference=read(reports[3]);native=read(reports[2]);cycles=read(reports[4]);retry=read(reports[5]);derivation=read(reports[6]);diagnostic=read('evidence/family_filter_constraint_replay01.json')
    assert diagnostic['passed'] and diagnostic['unchanged_output_identical'] and diagnostic['observed_max_residual_a']>1e-13
    assert native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
    lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';assert native['library_sha256']==private[lib]==sha(ROOT/lib)
    assert derivation['active_devices_unchanged'] and derivation['capacitor_values_unchanged'] and derivation['source_h128_unchanged'] and derivation['newton_gates_unchanged']
    for n,h in derivation['generated_sha256'].items():assert sha(ROOT/n)==h,n
    failure=read('evidence/family_filter_reference_failure01.json');assert not failure['passed'] and 'E0277' in failure['failure'] and 'E0277' in failure['unchanged_replay'];recover(failure)
    correction=read('evidence/family_filter_tangent_correction01.json');assert correction['only_error_conversion'] and correction['numerical_gates_unchanged'] and correction['failure_sha256']==sha(ROOT/'evidence/family_filter_reference_failure01.json') and hashlib.sha256(base64.b64decode(correction['old_helper_b64'])).hexdigest()==correction['old_helper_sha256']
    assert len(native['profiles'])==4 and len(reference['dc'])==12 and len(reference['roots'])==16 and reference['native_roots_used_as_seed'] is False and reference['shared_incoming_histories'] and not reference['independent_family_oracle'] and reference['tangent_columns']==48 and reference['tangent_rows_compared']==3312 and reference['tangent_max_scaled_error']<=1
    assert retry['fixtures']==12 and retry['rejected_trials']==36 and retry['signed_zeros_compared'] and retry['actual_iteration_budget_exhaustion'] and retry['exact_retry'] and retry['heap_allocations']==0
    typed=[];dcs=[];roots=[]
    for line in unpack(native['roots']['stdout']).decode().splitlines():
        z=line.split(',')
        if z[0]=='DC':dcs.append(z)
        elif z[0]=='ROOT':roots.append(z)
    for group,rows in [('dc',dcs),('roots',roots)]:
        for report,z in zip(reference[group],rows):
            flat=np.array(list(map(float,z[4:] if group=='dc' else z[146:])));v=flat[:69]+flat[69:];oracle=np.array(report['root']);err=float(np.max(abs(v[:68]-oracle[:68])));phase=float(abs(v[68]-oracle[68]));assert err<=1e-6 and phase<=1e-10
            typed.append(dict(group=group,node_error_v=err,phase_error_cycles=phase))
    for r in [native,trap]:
        assert r['temporary_area_empty'] and r['compile']['exit_code']==0 and r['roots']['exit_code']==0 and sha(ROOT/r['pack'])==r['pack_sha256']
        for p in r['profiles']:
            assert p['exit_code']==0 and p['elapsed_s']<=240 and p['stream_bytes']<256*1024**2
            a=decode_window(p['window'],ROOT/r['pack']);assert len(a)==p['rows'] and np.isfinite(a).all()
    assert len(cycles['profiles'])==4 and len(cycles['refinement'])==2 and cycles['initial_capacitor_charge_preserved'] and not cycles['full_settled_cycle_claim']
    for p in cycles['profiles']:assert p['algebraic_kcl_max_a']<=1e-13 and p['heap_allocations']==0 and p['charge_error_c']<=1e-16+1e-8*p['charge_throughput_c'] and p['j7_peak_v']>1e-9
    negative=cycles['negative_controls'];assert negative['fixed_base_trace_min_missing_harmonic_v']>1e-5 and negative['duplicate_r45_min_kcl_error_a']>1e-13 and negative['trace_controls_are_not_additional_circuit_trajectories']
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'] and not list((ROOT/'tmp/lab-current').iterdir()) and shutil.disk_usage(ROOT).free>1024**3
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('family_filter*') if p.is_file() and p!=ROOT/OUT);assert size<=32*1024**2,size
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{b['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and(not k.startswith('new_') or k=='new_listening')}
    worst_node=max(x['node_error_v'] for x in typed);worst_phase=max(x['phase_error_cycles'] for x in typed)
    r.update(schema='rf-d/family-real-filter-charge-consistent/v1',passed=True,base_commit=b['base_commit'],previous_qa=b['previous_qa'],previous_qa_sha256=b['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_family_mixer_origin_commit=b['base_commit'],experimental_family_mixer_origin_commit_pending_self_commit=False,experimental_family_filter_origin_commit=None,experimental_family_filter_origin_commit_pending_self_commit=True,experimental_family_filter_admitted=True,experimental_family_filter_scope='Real 68-node filter/recovery/two-VCA/J7 chain plus H128 phase; 12 own mean DC, 16 shared-history BE stage roots and four complete first cycles SDIRK2 at two CV; no settled note, KEY contours, independent VCO oracle or hardware/RT claim',experimental_family_filter_dc_roots=12,experimental_family_filter_stage_roots=16,experimental_family_filter_complete_cycles=4,experimental_family_filter_tangent_columns=48,experimental_family_filter_tangent_rows=3312,experimental_family_filter_typed_comparisons=typed,experimental_family_filter_reference_legacy_max_metric_mixed_units_not_used_for_admission=True,experimental_family_filter_worst_node_error_v=worst_node,experimental_family_filter_worst_phase_error_cycles=worst_phase,experimental_family_filter_worst_bus_refinement_v=max(max(x['signals']['bus']['dc_error'],x['signals']['bus']['harmonics_1_8_norm_error']) for x in cycles['refinement']),experimental_family_filter_worst_current_refinement_a=max(max(x['signals'][k]['dc_error'],x['signals'][k]['harmonics_1_8_norm_error']) for x in cycles['refinement'] for k in ['panel_bus','c27']),experimental_family_filter_initial_mean_dc_is_source_jump=True,experimental_family_filter_sdirk_order=2,experimental_family_filter_rejected_trapezoidal_cycles=4,experimental_family_filter_bitwise_retry_fixtures=12,experimental_family_filter_rejected_trial_count=36,experimental_family_filter_receipt_bytes=size,experimental_family_filter_reference={n:sha(ROOT/n) for n in reports},new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_native_trajectory_count=4,inherited_test_count=old['covered_test_count'],covered_test_count=old['covered_test_count'],inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,real_time=False,physical_fidelity=False,physical_cv_general=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    return r
def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_family_filter.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/family_filter_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/family_filter_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('FAMILY_FILTER_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_family_filter_receipt_bytes'])
if __name__=='__main__':main()
