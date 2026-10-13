"""Admit an isolated resistance control with preserved nominal lineage and loads."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from decimal import Decimal
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,TICK
from prepare_decay_control import RUST,ATTR,EXPORT,family,START,SPAN
from prepare_decay_callers import callers
from prepare_decay_auditor import source,reference
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_decay_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
 previous='evidence/voice_release_tests01.json';old=read(previous);before=read('evidence/voice_decay_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous) and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'admitted base')
 saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR and (ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==saved['crates/rf-d-circuit/src/lib.rs']+EXPORT,'exports only in old Rust')
 for n,s in {**family(),**callers(),'tools/check_decay_control.py':source(),'tools/decay_control_reference.py':reference()}.items():require((ROOT/n).read_text(encoding='utf8')==s,'declared transformation '+n)
 for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic doc prefix')
 require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_release_tests01.json',b'voice_decay_tests01.json')),'declared README QA replacement')
 names=['evidence/voice_decay_'+tag+'.json' for tag in ['inputs01','native02','repair01','reference02','listening01','cli01']];receipts=[read(n) for n in names]
 audit_repair='evidence/voice_decay_auditor_repair01.json';ar=read(audit_repair)
 for name,r in zip(names+[audit_repair],receipts+[ar]):
  require(r['passed'],'admitted measurement '+name)
  for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h,'measured source '+n)
  if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable sources')
  for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private use '+n);private[n]=h
  if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private')
  for o in r.get('outputs',[])+r.get('files',[]):require(sha(ROOT/o['path'])==o['sha256'],'new output');private[o['path']]=o['sha256']
  if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
 inp,native,repair,ref,listening,cli=receipts;failure=read('evidence/voice_decay_native01.json');require(not failure['passed'] and len(failure['replays'])==1 and failure['commands'][-1]['exit_code']==failure['replays'][0]['exit_code']!=0,'preserved compile failure and unchanged replay')
 af=read('evidence/voice_decay_reference01.json');require(not af['passed'] and 'ValueError: own seed metadata/bits' in af['failure'] and 'ValueError: own seed metadata/bits' in af['replay'] and ar['only_parent_proposal_binding_and_output_version_changed'] and not ar['numerical_gates_changed'] and not ar['measured_inputs_changed'],'preserved auditor binding rejection and unchanged replay')
 rejected_audit=base64.b64decode(af['failed_source_base64']['tools/check_decay_control.py']);fixed_audit=rejected_audit.replace(b"points[0]['next_full']==4096",b"points[0]['next_full']==struct.unpack('<8sQ6IdQ458d',(ROOT/f'references-local/release-voice01/{maximum}/final.ckp').read_bytes())[4]").replace(b'voice_decay_reference01.json',b'voice_decay_reference02.json');require((ROOT/'tools/check_decay_control.py').read_bytes()==fixed_audit,'only auditor binding/output correction')
 rejected=base64.b64decode(failure['failed_source_base64'][RUST[3]]);require((ROOT/RUST[3]).read_bytes()==rejected.replace(b'p.keyboard,p.final_decay,p.short).map_err',b'p.keyboard,p.final_decay,p.short,p.decay_ohm).map_err') and repair['only_observer_argument_added'] and not repair['numerical_gates_changed'],'one missing observer argument repair')
 for o in failure['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'preserved rejected output');private[o['path']]=o['sha256']
 require(native['new_library_compile'] and not native['new_cargo_cache'] and native['lab_stack_bytes']==33554432 and len(native['commands'])==3 and all(c['exit_code']==0 and c['wall_s']<=120 for c in native['commands']) and not native['replays'],'bounded library and caller builds')
 require(native['nominal_three_way_identical'] and native['nominal_compared_accepted']==8 and native['invalid_control_rejections']==12 and native['invalid_control_restore_rejections']==2 and native['only_resistance_changed_at_event'],'nominal and atomic control gates')
 require(len(native['profiles'])==2 and native['wall_s']<=4000 and all(p['exit_code']==0 and p['wall_s']<=1900 for p in native['profiles']) and all(p['exit_code']==0 and p['wall_s']<=120 for p in native['legacy_runs']),'bounded native campaign')
 require(ref['controlled_release_admitted'] and ref['decay_ohm']==1000. and ref['continued_duration_s']==.016 and ref['joined_duration_s']==.036004 and ref['wall_s']<=600 and len(ref['same_clock_refinement'])==21,'new electrical scene and original graph')
 require(ref['independent_nonlinear_rows']==1374*sum(p['selected_accepted_count'] for p in ref['profiles']) and ref['independent_candidates']==6*sum(p['selected_accepted_count'] for p in ref['profiles']),'selected graph coverage')
 for p,f,s in zip(ref['profiles'],ref['flux_checks'],ref['seams']):
  require(p['final_decay'] and len(p['grids'])==21 and len(p['resets'])>=2 and p['rollbacks']==1,'complete controlled profile')
  for n,h in p['input_sha256'].items():require(private[n]==h,'graph input inventory')
  require(f['records']==p['fine_steps']+1 and f['selected_independent_endpoints']==2*p['selected_accepted_count']+1 and f['max_derivative_balance_error_v_per_s']<=2e-6,'flux and selected component balance')
  require(s['preserved_high_low_values']==458 and s['event_ticks']==START and s['old_decay_ohm']==100000. and s['new_decay_ohm']==1000. and s['only_resistance_changed'] and not s['source_voltage_event'] and s['nominal_compared_accepted']==4,'control event without state reset')
  for balance in [p['total_ledger'],*[q['ledger'] for q in p['phases']]]:require(len(balance['rows'])==9 and all(Decimal(r['error_c'])<=Decimal(r['gate_c']) for r in balance['rows']),'oriented charge balance')
 require(len(ref['joined_ledgers'])==2 and all(j['duration_s']==j['duration_ticks']*TICK and len(j['ledger']['rows'])==9 and all(Decimal(r['error_c'])<=Decimal(r['gate_c']) for r in j['ledger']['rows']) for j in ref['joined_ledgers']),'joined endpoints and integer clock duration')
 require(ref['maximum_active_replay_probes']<=3 and ref['rejected_corruptions']==8 and ref['atomic_rollbacks']==2 and ref['restores']==sum(p['restores'] for p in ref['profiles']) and ref['replayed_accepted_steps']==sum(p['replayed_accepted_steps'] for p in ref['profiles']),'bounded replay counts')
 require(listening['identical_derived_replay'] and listening['joined_simulated_window_s']==.036004 and listening['native_resolution_max_error_v']<=2e-6 and listening['native_resolution_max_pcm_lsb']<=7 and len(listening['files'])==2 and all(f['frames']==1728 and f['stretch']==1 and f['full_audio_duration_simulated'] and not f['repeated'] for f in listening['files']),'native joined audio')
 require(not any(listening[k] for k in ['dc_removed','fades','peak_normalization','repeated','physical_fidelity','real_time']),'audio adaptation scope')
 require(cli['integration_checks']==3 and all(cli[k] for k in ['user_cli_wav_identical','sidecar_verified','existing_output_rejected_without_mutation','mismatched_seam_rejected_before_publication']),'public CLI integration')
 require(not any(ref[k] for k in ['steady_periodicity_admitted','full_contour_from_silence_admitted','physical_fidelity','real_time']),'finite conditional scope')
 size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=128*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'new files and reserve')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 r=dict(schema='rf-d/electrical-decay-control/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),new_private_bytes=size,
  controlled_release_admitted=True,decay_ohm=1000.,continued_duration_s=.016,joined_duration_s=.036004,same_clock_states=21,independent_nonlinear_rows=ref['independent_nonlinear_rows'],independent_candidates=ref['independent_candidates'],accepted_steps=ref['accepted_steps'],fine_steps=ref['fine_steps'],reset_crossings=sum(len(p['resets']) for p in ref['profiles']),restores=ref['restores'],replayed_accepted_steps=ref['replayed_accepted_steps'],maximum_active_replay_probes=ref['maximum_active_replay_probes'],rejected_corruptions=8,atomic_rollbacks=2,
  nominal_three_way_identical=True,nominal_compared_accepted=8,invalid_control_rejections=12,invalid_control_restore_rejections=2,only_resistance_changed_at_event=True,preserved_state_high_low_values=458,nominal_sources_unchanged=True,new_library_compile=True,new_cargo_cache=False,new_spice_processes=0,lab_stack_bytes=33554432,
  inherited_test_count=255,native_test_count=0,covered_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,user_cli_integration_checks=3,heap_measured_this_block=False,deadline_measured=False,new_audio=True,new_audio_files=2,full_audio_duration_simulated=True,steady_periodicity_admitted=False,full_contour_from_silence_admitted=False,physical_fidelity=False,real_time=False,
  controlled_library_sha256=sha(ROOT/'references-local/decay-voice02/librf_d_circuit.rlib'),decay_listening='evidence/voice_decay_listening01.json',decay_reference='evidence/voice_decay_reference02.json',compile_rejection_preserved=True,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
 for k in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review']:r[k]=old[k]
 return r

def main():
 try:r=audit()
 except Exception:
  first=traceback.format_exc()
  try:audit();second='unexpected pass'
  except Exception:second=traceback.format_exc()
  k=1
  while(ROOT/f'evidence/voice_decay_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_decay_qa_failure{k:02d}.json').write_text(json.dumps(dict(passed=False,failure=first,replay=second,failed_source_base64=base64.b64encode((ROOT/'tools/validate_decay_control.py').read_bytes()).decode()),indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('DECAY_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
