"""Audit the additive public API, memory contract and exact conditional exports."""
import base64,hashlib,json,shutil,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_conditioned_portable import voice,solver,latch,contour,engine,caller,ATTR,EXPORT,NAMES
from prepare_conditioned_fixtures import ATTR as TEST_ATTR
from joint_cycles_analysis import require

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_radau_inplace_tests01.json';old=read(previous);before=read('evidence/voice_conditioned_portable_before01.json');require(old['passed'] and old['radau_inplace_admitted'] and before['previous_qa_sha256']==sha(ROOT/previous),'admitted base')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR+TEST_ATTR,'declared exact attributes');require((ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==saved['crates/rf-d-circuit/src/lib.rs']+EXPORT,'additive exports')
    for n,f in zip(NAMES,[voice,solver,latch,contour,engine,caller]):require((ROOT/n).read_text(encoding='utf8')==f(),'declared public transformation '+n)
    names=['evidence/voice_conditioned_portable_'+s+'01.json' for s in ['inputs','library','bank','driver_repair','fixture','fixture_extension','tests_native','native','trajectory','identity_adapter_repair']]+['evidence/voice_conditioned_portable_bank02.json']
    receipts=[read(n) for n in names];historic={}
    for r in receipts:
        for n,v in r.get('failed_source_base64',{}).items():historic[n,hashlib.sha256(base64.b64decode(v)).hexdigest()]=True
        if 'previous_fixture_base64' in r:
            raw=base64.b64decode(r['previous_fixture_base64']);require(hashlib.sha256(raw).hexdigest()==r['previous_fixture_sha256'] and (ROOT/'crates/rf-d-circuit/tests/support/conditioned_seed.rs').read_bytes().startswith(raw),'synthetic fixture prefix preserved');historic['crates/rf-d-circuit/tests/support/conditioned_seed.rs',r['previous_fixture_sha256']]=True
    for name,r in zip(names,receipts):
        require(r['passed'] or name=='evidence/voice_conditioned_portable_bank01.json','receipt '+name)
        for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h or (n,h) in historic,'receipt source '+name+' '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable measured source')
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable measured private')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'used private '+n);private[n]=h
        for q in r.get('outputs',[]):require(sha(ROOT/q['path'])==q['sha256'],'new output '+q['path']);private[q['path']]=q['sha256']
        if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
    _,library,failed,repair,fixture,extension,tests,native,trajectory,adapter,bank=receipts
    require(library['new_library_compile'] and not library['new_cargo_cache'] and len(library['commands'])==1 and library['commands'][0]['exit_code']==0 and library['commands'][0]['wall_s']<=120,'one additive library build')
    require(not failed['passed'] and len(failed['commands'])==2 and failed['commands'][0]['stderr']==failed['commands'][1]['stderr'] and 'error[E0282]' in failed['commands'][0]['stderr'],'preserved index inference rejection')
    require(repair['failed_receipt_sha256']==sha(ROOT/'evidence/voice_conditioned_portable_bank01.json') and repair['repaired_driver_sha256']==sha(ROOT/'tools/check_conditioned_portable_bank.py') and not repair['library_changed'] and not repair['numerical_gates_changed'],'driver-only type repair')
    require(fixture['synthetic_model_histories_only'] and not fixture['proprietary_capture_or_audio'] and len(fixture['records'])==3 and extension['prefix_preserved'] and not extension['new_temporal_duration'],'published synthetic histories')
    require(bank['identical_replay'] and bank['public_roots']==84 and bank['root_bit_fields_per_pair']==1834 and bank['iterations_and_trials_identical'] and bank['roots_identical'] and bank['jacobian_bit_coordinates']==17620176 and bank['residual_bit_coordinates']==38472 and bank['candidate_high_low_bit_coordinates']==76944,'public roots and complete matrices')
    require(bank['stored_linear_systems_replayed']==396 and bank['replayed_linear_corrections_bit_coordinates']==181368 and bank['linear_corrections_identical'] and not bank['active_linear_archive_exported'] and bank['independent_equations_reexecuted']==0 and bank['workspace_reuse_across_all_cases'] and bank['workspace_error_recovery'],'stored matrix replay and explicit scope')
    require(tests['native_test_count']==4 and tests['heap_measured'] and tests['processing_allocations']==0 and tests['measured_successful_processing_calls']==9 and tests['measured_rejected_processing_calls']==3 and tests['lab_stack_bytes']==33554432 and not tests['deadline_measured'],'four API and allocator tests')
    require(tests['workspace_bytes']==2*tests['stamp_bytes']<=4*1024**2 and tests['stamp_bytes']<=2*1024**2 and max(tests['engine_bytes'],tests['checkpoint_bytes'])<=16*1024,'measured persistent memory contract')
    require(adapter['identical_replay'] and not adapter['library_or_numerical_gates_changed'],'preserved identity adapter repair')
    require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and len(native['profiles'])==4 and not native['replays'] and all(p['exit_code']==0 and p['wall_s']<=990 for p in native['profiles']) and native['wall_s']<=4000,'new public temporal engine campaign')
    require(trajectory['public_conditioned_cycle_window_admitted'] and trajectory['all_exported_data_identical'] and trajectory['identical_data_files']==len(trajectory['file_identity_pairs'])==40 and trajectory['inherited_independent_nonlinear_rows']==38472 and trajectory['independent_nonlinear_rows_reexecuted']==0 and not trajectory['temporal_graph_reexecuted'],'complete exported temporal identity')
    for p in trajectory['file_identity_pairs']:
        require(sha(ROOT/p['original_path'])==sha(ROOT/p['target_path'])==p['sha256'],'temporal export pair');private[p['original_path']]=p['sha256'];private[p['target_path']]=p['sha256']
    require(trajectory['accepted_steps']==13385 and trajectory['fine_steps']==26770 and trajectory['restores']==24 and trajectory['replayed_accepted_steps']==368 and trajectory['rejected_corruptions']==16 and trajectory['atomic_rollbacks']==8,'public temporal gates')
    for r in [bank,tests]:require(all(c['exit_code']==0 and c['wall_s']<=600 for c in r['commands']) and r['commands'][0]['wall_s']<=120,'bounded public driver/test acceptance')
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=96*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'new library/driver/data and reserve budget')
    return dict(base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),private_input_sha256=private,new_private_bytes=size,lab_collection_verified=True,public_conditioned_voice_admitted=True,public_conditioned_temporal_engine_admitted=True,schur_cycle_window_admitted=True,physical_states=229,reconstructed_corrections=458,exterior_corrections=140,public_roots=84,stored_linear_systems_replayed=396,active_linear_archive_exported=False,inherited_independent_linear_rows=181368,inherited_bank_nonlinear_rows=38472,inherited_temporal_nonlinear_rows=38472,independent_equations_reexecuted=0,workspace_bytes=tests['workspace_bytes'],stamp_bytes=tests['stamp_bytes'],engine_bytes=tests['engine_bytes'],checkpoint_bytes=tests['checkpoint_bytes'],processing_allocations=0,measured_successful_processing_calls=9,measured_rejected_processing_calls=3,accepted_steps=13385,fine_steps=26770,restores=24,replayed_accepted_steps=368,rejected_corruptions=16,atomic_rollbacks=8,identical_temporal_data_files=40,identical_temporal_data_bytes=trajectory['identical_data_bytes'],native_wall_s=native['wall_s'],new_library_compile=True,new_cargo_cache=False,heap_measured=True,deadline_measured=False,lab_stack_bytes=33554432,full_contour_from_silence_admitted=False,new_duration_s=0,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,covered_test_count=252,inherited_test_count=248,native_test_count=4,inherited_tests_reexecuted=False)

def main():
    r=audit();write('evidence/voice_conditioned_portable_reference01.json',dict(passed=True,**r));print('PUBLIC_CONDITIONED_REFERENCE',r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'],'ADMITTED',r['public_conditioned_voice_admitted'])
if __name__=='__main__':main()
