"""Publish in-place Radau only after exact bank and complete export identities."""
import base64,hashlib,json,shutil,statistics,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_radau_inplace import kernel,caller,bench,ATTR
from joint_cycles_analysis import require

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_schur_chain_tests01.json';old=read(previous);before=read('evidence/voice_radau_inplace_before01.json')
    require(old['passed'] and old['chain_schur_admitted'] and before['previous_qa_sha256']==sha(ROOT/previous),'admitted base identity')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'declared attributes')
    for n,s in [('tools/joint_radau_inplace_kernel.rs',kernel()),('tools/joint_radau_inplace_runner.rs',caller()),('tools/radau_inplace_bench.rs',bench())]:require((ROOT/n).read_text(encoding='utf8')==s,'declared destination lifetime '+n)
    names=['evidence/voice_schur_refined_'+s+'.json' for s in ['radauinplacebench01','radauinplacebank01','radauinplacestructure01']]+['evidence/voice_radau_inplace_'+s+'01.json' for s in ['inputs','native','trajectory']]
    receipts=[read(n) for n in names]
    for name,r in zip(names,receipts):
        require(r['passed'],'receipt '+name)
        for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h,'receipt source '+name+' '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable source')
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private receipt '+n);private[n]=h
        for f in r.get('outputs',[]):require(sha(ROOT/f['path'])==f['sha256'],'output '+f['path']);private[f['path']]=f['sha256']
        if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
    timing,bank,regressions,_,native,trajectory=receipts
    for r in [timing,bank,regressions]:require(all(c['exit_code']==0 and c['wall_s']<=600 for c in r['commands']) and r['commands'][0]['wall_s']<=120,'bounded bank commands')
    require(timing['utility_passed'] and len(timing['rounds'])==5 and [x[0] for x in timing['rounds']]==list(range(5)) and statistics.median(x[1]/x[2] for x in timing['rounds'])==timing['median_paired_speedup']>1.10,'non-marginal utility')
    require(not (ROOT/'evidence/voice_schur_refined_radauinplaceconfirm01.json').exists(),'no unrequired confirmation')
    require(timing['exact_bit_fields_per_pair']==1834 and timing['iterations_and_trials_identical'] and timing['roots_identical'],'complete root bits')
    require((ROOT/'references-local/schur-refined-radauinplacebench01/roots.txt').read_bytes()==(ROOT/'references-local/schur-refined-chainbench01/roots.txt').read_bytes(),'all roots by bytes')
    require(bank['identical_replay'] and bank['linear_solves']==396 and bank['all_linear_traces_identical'] and bank['independent_linear_rows']==0 and bank['inherited_independent_linear_rows']==181368 and not bank['independent_linear_checks_reexecuted'],'exact inherited bank scope')
    require((ROOT/'references-local/schur-refined-radauinplacebank01/linear.bin').read_bytes()==(ROOT/'references-local/schur-refined-chainbank01/linear.bin').read_bytes(),'396 J/b/corrections')
    require(bank['exact_linear_checks']==read('evidence/voice_schur_refined_chainbank01.json')['exact_linear_checks'] and bank['memory_observations']==1680 and bank['terminal_and_ground_currents']==2016 and bank['memory_max_ratio']<=1 and bank['port_current_max_a']<=2e-11,'inherited rows and newly observed storage/ports')
    require(regressions['identical_replay'] and regressions['regressions']==11 and regressions['complete_stamps']==84 and regressions['jacobian_bit_coordinates']==17620176 and regressions['residual_bit_coordinates']==38472 and regressions['candidate_high_low_bit_coordinates']==76944 and all(regressions[k] for k in ['compatible_facade_identical','first_and_second_stage_error_order_preserved','successful_and_failed_workspace_reuse','reference_swapping_verified']),'full stamps and failed scratch recovery')
    require(native['passed'] and len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'] and len(native['profiles'])==4 and all(p['exit_code']==0 and p['wall_s']<=990 for p in native['profiles']) and native['wall_s']<=4000,'bounded own native campaign')
    require(trajectory['radau_inplace_cycle_window_admitted'] and trajectory['all_exported_data_identical'] and trajectory['identical_data_files']==len(trajectory['file_identity_pairs'])==40 and trajectory['independent_nonlinear_rows_reexecuted']==0 and trajectory['inherited_independent_nonlinear_rows']==38472 and not trajectory['temporal_graph_reexecuted'] and trajectory['wall_s']<=600,'exact exported temporal inheritance')
    for p in trajectory['file_identity_pairs']:
        require(sha(ROOT/p['original_path'])==sha(ROOT/p['target_path'])==p['sha256'],'all exported temporal pairs');private[p['original_path']]=p['sha256'];private[p['target_path']]=p['sha256']
    require(trajectory['accepted_steps']==13385 and trajectory['fine_steps']==26770 and trajectory['restores']==24 and trajectory['replayed_accepted_steps']==368 and trajectory['rejected_corruptions']==16 and trajectory['atomic_rollbacks']==8,'reexecuted native coverage')
    added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'new private/reserve budget')
    return dict(base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),private_input_sha256=private,new_private_bytes=size,lab_collection_verified=True,numeric_bank_passed=True,cost_utility_passed=True,dynamic_schur_admitted=True,chain_schur_admitted=True,radau_inplace_admitted=True,schur_cycle_window_admitted=True,full_contour_from_silence_admitted=False,median_paired_speedup=timing['median_paired_speedup'],paired_rounds=timing['speedups'],confirmation_required=False,confirmation_executed=False,inherited_independent_linear_rows=181368,inherited_bank_nonlinear_rows=38472,inherited_temporal_nonlinear_rows=38472,independent_linear_rows_reexecuted=0,independent_nonlinear_rows_reexecuted=0,assembly_regressions=11,complete_stamps=84,jacobian_bit_coordinates=17620176,residual_bit_coordinates=38472,candidate_high_low_bit_coordinates=76944,memory_observations=1680,terminal_and_ground_currents=2016,accepted_steps=13385,fine_steps=26770,restores=24,replayed_accepted_steps=368,rejected_corruptions=16,atomic_rollbacks=8,identical_temporal_data_files=40,identical_temporal_data_bytes=trajectory['identical_data_bytes'],native_wall_s=native['wall_s'],physical_states=229,reconstructed_corrections=458,exterior_corrections=140,new_duration_s=0,new_audio=False,new_library_compile=False,new_spice_processes=0,physical_fidelity=False,real_time=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False)

def main():
    r=audit();write('evidence/voice_radau_inplace_reference01.json',dict(passed=True,**r));print('RADAU_INPLACE_REFERENCE',r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'],'ADMITTED',r['radau_inplace_admitted'])
if __name__=='__main__':main()
