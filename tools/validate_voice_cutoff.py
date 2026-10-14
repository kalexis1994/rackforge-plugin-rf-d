"""Admit only the measured finite loaded continuation and joined native audio."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_voice_cutoff import EXAMPLE,ATTR,START,SPAN,caller,auditor
from joint_cycles_analysis import require,TICK
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_cutoff_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 old=read('evidence/voice_retrigger_tests01.json');before=read('evidence/voice_cutoff_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/'evidence/voice_retrigger_tests01.json') and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'frozen base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private input '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'one caller LF rule');require((ROOT/EXAMPLE).read_text(encoding='utf8')==caller() and (ROOT/'tools/check_voice_cutoff.py').read_text(encoding='utf8')==auditor(),'declared caller/original graph adapter')
 for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic documentation prefix')
 require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_retrigger_tests01.json',b'voice_cutoff_tests01.json')),'only declared README gate update')
 receipts=['evidence/voice_cutoff_inputs01.json','evidence/voice_cutoff_native01.json','evidence/voice_cutoff_reference01.json','evidence/voice_cutoff_listening01.json','evidence/voice_cutoff_cli01.json']
 for name in receipts:
  r=read(name);require(r['passed'],'admitted measurement '+name)
  for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h,'executed source '+n)
  if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable executed sources')
  for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'executed private input '+n);private[n]=h
  if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private inputs')
  for o in r.get('outputs',[])+r.get('files',[]):require(sha(ROOT/o['path'])==o['sha256'] and (ROOT/o['path']).stat().st_size==o['bytes'],'measured output');private[o['path']]=o['sha256']
  if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler identity')
 from prepare_cutoff_render import renderer,cli as cli_source,checker
 require((ROOT/'tools/render_voice_cutoff.py').read_text(encoding='utf8')==renderer() and (ROOT/'tools/cutoff_render_cli.py').read_text(encoding='utf8')==cli_source() and (ROOT/'tools/check_cutoff_cli.py').read_text(encoding='utf8')==checker(),'declared renderer CLI and complete negative fixtures')
 native,ref,listening,cli=[read(n) for n in receipts[1:]]
 require(native['passed'] and not native['new_library_compile'] and not native['new_cargo_cache'] and not native['replays'] and native['wall_s']<=4000 and len(native['profiles'])==2 and all(p['exit_code']==0 and p['wall_s']<=1900 for p in native['profiles']),'native campaign budget/scope')
 require(native['seam_bits_identical'] and native['seam_compared_accepted']==8 and native['new_source_event'] and len(ref['seams'])==2 and all(p['preserved_high_low_values']==458 and p['complete_accepted_bit_comparisons']==4 for p in ref['seams']),'original/optimized seam admission')
 require(len(ref['same_clock_refinement'])==22 and max(p['gate_ratio'] for p in ref['same_clock_refinement'])<=1 and len(ref['profiles'])==2 and ref['wall_s']<=600 and ref['continued_duration_s']==.016004 and ref['joined_duration_s']==.164012 and ref['new_source_event'],'independent graph and refinement scope')
 require(ref['independent_candidates']==6*sum(p['selected_accepted_count'] for p in ref['profiles']) and ref['independent_nonlinear_rows']==1374*sum(p['selected_accepted_count'] for p in ref['profiles']) and ref['maximum_active_replay_probes']<=3 and ref['rejected_corruptions']==8 and ref['atomic_rollbacks']==2,'coverage and rollback gates')
 for p in ref['profiles']:
  for root in p['root_checks']:require(root['residual_gate_ratio']<=1 and root['correction_gate_ratio']<=1,'unchanged original equation gates')
  for n,h in p['input_sha256'].items():require(sha(ROOT/n)==h,'audited native input');private[n]=h
 require(listening['identical_derived_replay'] and listening['native_resolution_max_error_v']<=2e-6 and listening['native_resolution_max_pcm_lsb']<=7 and not listening['repeated'] and not listening['dc_removed'] and not listening['peak_normalization'] and not listening['fades'] and len(listening['files'])==2 and all(f['frames']==7872 and f['wav_duration_s']==.164 for f in listening['files']),'whole native WAV/refinement')
 sidecar=read('references-local/cutoff-cli01/j7.json');require(len(sidecar['input_sha256'])==24 and sidecar['cutoff_start_ticks']==START and sidecar['final_ticks']==START+SPAN and sidecar['frames']==7872,'twenty-four input identities and integer audio clock')
 for n,h in sidecar['code_sha256'].items():require(sha(ROOT/n)==h,'sidecar code identity '+n)
 require(ref['event_compared_accepted']==native['event_compared_accepted']==16 and len(ref['source_events'])==2 and all(len(p)==2 and all(e['preserved_values']==458 and e['complete_accepted_bit_comparisons']==4 for e in p) for p in ref['source_events']),'charged source events and original block advances')
 require(sidecar['new_source_event'] and sidecar['source_events']==[dict(ticks=e['ticks'],keyboard_v=e['keyboard_v'],short=e['short'],cutoff_fraction=e['cutoff_fraction'],previous_cutoff_fraction=e['previous_cutoff_fraction']) for e in ref['source_events'][1]],'complete CLI source event provenance')
 require(cli['integration_checks']==4 and all(cli[k] for k in ['user_cli_wav_identical','sidecar_verified','existing_output_rejected_without_mutation','mismatched_seam_rejected_before_publication','incomplete_trace_rejected_before_publication']),'four reproducible CLI checks')
 size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=96*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'finite output budget and reserve');staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged release QA');names=set(old['source_sha256'])|{'evidence/voice_retrigger_tests01.json'}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 r=dict(schema='rf-d/loaded-cutoff-panel-control/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/'evidence/voice_retrigger_tests01.json'),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),new_private_bytes=size,public_block_library_sha256=old['public_block_library_sha256'],original_circuit_sources_unchanged=True,new_source_event=True,start_ticks=START,end_ticks=START+SPAN,continued_duration_s=SPAN*TICK,joined_native_duration_s=ref['joined_duration_s'],wav_duration_s=.164,wav_frames=7872,accepted_steps=ref['accepted_steps'],fine_endpoints=ref['fine_steps'],new_independent_nonlinear_rows=ref['independent_nonlinear_rows'],independent_candidates=ref['independent_candidates'],shared_clock_states=22,state_coordinates=229,seam_compared_accepted=8,event_compared_accepted=16,source_events=ref['source_events'],seam_full_state_values=458,max_state_voltage_error_v=max(p['max_voltage_error_v'] for p in ref['same_clock_refinement']),max_state_gate_ratio=max(p['gate_ratio'] for p in ref['same_clock_refinement']),restores=ref['restores'],replayed_accepted_steps=ref['replayed_accepted_steps'],oscillator_resets=sum(len(p['resets']) for p in ref['profiles']),rejected_corruptions=8,atomic_rollbacks=2,maximum_active_replay_probes=ref['maximum_active_replay_probes'],flux_records=sum(p['records'] for p in ref['flux_checks']),flux_selected_independent_endpoints=sum(p['selected_independent_endpoints'] for p in ref['flux_checks']),max_derivative_balance_error_v_per_s=max(p['max_derivative_balance_error_v_per_s'] for p in ref['flux_checks']),native_resolution_max_error_v=listening['native_resolution_max_error_v'],native_resolution_max_pcm_lsb=listening['native_resolution_max_pcm_lsb'],whole_audio_replay=True,cli_integration_checks=4,new_audio=True,new_circuit_duration_s=.016004,new_library_compile=False,heap_measured_this_block=False,deadline_measured=False,lab_stack_bytes=33554432,new_cargo_cache=False,new_spice_processes=0,inherited_test_count=255,covered_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,physical_fidelity=False,real_time=False,steady_periodicity_admitted=False,full_contour_from_silence_admitted=False,cutoff_reference={'path':receipts[2],'sha256':sha(ROOT/receipts[2])},cutoff_listening={'path':receipts[3],'sha256':sha(ROOT/receipts[3]),'files':listening['files']},local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
 for k in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening']:r[k]=old[k]
 return r
def main():
 try:r=audit()
 except Exception:
  first=traceback.format_exc()
  try:audit();second='unexpected pass'
  except Exception:second=traceback.format_exc()
  k=1
  while(ROOT/f'evidence/voice_cutoff_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_cutoff_qa_failure{k:02d}.json').write_text(json.dumps(dict(passed=False,failure=first,replay=second,failed_source_base64=base64.b64encode((ROOT/'tools/validate_voice_cutoff.py').read_bytes()).decode()),indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CUTOFF_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'],flush=True)
if __name__=='__main__':main()
