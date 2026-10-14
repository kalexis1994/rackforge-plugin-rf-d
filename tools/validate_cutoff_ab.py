"""Admit the counterfactual branch, common origin, independent scope and paired audio."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_cutoff_ab import EXAMPLE,ATTR,START,SPAN,caller,auditor
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/cutoff_ab_tests01.json'
EOL_ATTR=b'\n/evidence/cutoff_ab*.json text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 old=read('evidence/voice_cutoff_tests01.json');before=read('evidence/cutoff_ab_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/'evidence/voice_cutoff_tests01.json') and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'frozen base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR+EOL_ATTR and (ROOT/EXAMPLE).read_text(encoding='utf8')==caller() and (ROOT/'tools/check_cutoff_ab.py').read_text(encoding='utf8')==auditor(),'declared caller auditor and LF rules');eol=read('evidence/cutoff_ab_eol01.json');require(eol['passed'] and eol['gitattributes_after_sha256']==sha(ROOT/'.gitattributes') and eol['attribute'].encode()==EOL_ATTR and eol['numeric_sources_and_gates_unchanged'],'explicit evidence checkout identity')
 for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic prefix')
 require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_cutoff_tests01.json',b'cutoff_ab_tests01.json')),'declared README gate')
 failed=read('evidence/cutoff_ab_preflight_failure01.json');repair=read('evidence/cutoff_ab_preflight_repair01.json');require(not failed['passed'] and failed['failure']==failed['unchanged_replay'] and repair['passed'] and repair['no_native_measurement_before_repair'] and repair['before_unchanged'],'unmeasured preparation failure and replay retained')
 original=base64.b64decode(failed['source_base64']['tools/prepare_cutoff_ab.py']).decode('utf8');expected=original.replace('.replace("phase in range(3)","phase==0")','.replace("and phase in range(3) and","and phase==0 and")');require((ROOT/'tools/prepare_cutoff_ab.py').read_text(encoding='utf8')==expected and (ROOT/'tools/cutoff_ab_audit.py').read_bytes()==base64.b64decode(failed['source_base64']['tools/cutoff_ab_audit.py']),'only restricted guard substitution repairs preparation')
 for n,h in repair['source_sha256'].items():require(sha(ROOT/n)==h,'declared preparation repair '+n)
 receipts=[f'evidence/cutoff_ab_{n}01.json' for n in ['inputs','native','reference','listening','cli']]
 for name in receipts:
  r=read(name);require(r['passed'],'admitted '+name)
  for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h,'executed source '+n)
  if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable executed sources')
  for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'executed private '+n);private[n]=h
  if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable executed private inputs')
  for o in r.get('outputs',[])+r.get('files',[]):require(sha(ROOT/o['path'])==o['sha256'] and (ROOT/o['path']).stat().st_size==o['bytes'],'measured output');private[o['path']]=o['sha256']
  if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'frozen compiler')
 inp,native,ref,audio,cli=[read(n) for n in receipts];require(not native['new_library_compile'] and not native['new_cargo_cache'] and not native['replays'] and native['wall_s']<=4000 and len(native['profiles'])==2 and all(p['exit_code']==0 and p['wall_s']<=1900 for p in native['profiles']),'finite native scope')
 require(native['seam_bits_identical'] and native['seam_compared_accepted']==8 and not native['new_source_event'] and len(ref['seams'])==2 and all(s['preserved_values']==458 and s['complete_accepted_bit_comparisons']==4 for s in ref['seams']),'exact open origin and original block advances')
 require(ref['wall_s']<=600 and len(ref['same_clock_refinement'])==11 and max(x['gate_ratio'] for x in ref['same_clock_refinement'])<=1 and ref['independent_candidates']==6*sum(p['selected_accepted_count'] for p in ref['profiles']) and ref['independent_nonlinear_rows']==1374*sum(p['selected_accepted_count'] for p in ref['profiles']),'original open and same-clock scope')
 for p in ref['profiles']:
  for root in p['root_checks']:require(root['residual_gate_ratio']<=1 and root['correction_gate_ratio']<=1,'unchanged original equation gates')
  for n,h in p['input_sha256'].items():require(sha(ROOT/n)==h,'independently audited private '+n);private[n]=h
 require(ref['closed_coverage_inherited'] and not ref['closed_equations_reexecuted'] and ref['new_continuous_history_duration_s']==0 and len(ref['forks'])==2 and all(f['common_state_values']==458 and f['start_ticks']==START and f['end_ticks']==START+SPAN and f['open_alpha']==1. and f['closed_alpha']==.5 and len(f['same_clock_differences'])==11 for f in ref['forks']),'same-origin A/B without concatenation or repeated coverage')
 require(ref['maximum_active_replay_probes']<=3 and ref['rejected_corruptions']==8 and ref['atomic_rollbacks']==2,'bounded replay and atomicity')
 require(audio['identical_derived_replay'] and len(audio['files'])==4 and all(f['frames']==384 and f['wav_duration_s']==.008 for f in audio['files']) and all(x['max_error_v']<=2e-6 and x['max_error_pcm_lsb']<=7 for x in audio['refinement']) and not any(audio[x] for x in ['dc_removed','peak_normalization','fades','repeated']) and audio['new_continuous_history_duration_s']==0,'paired complete native audio')
 require(cli['integration_checks']==4 and all(cli[x] for x in ['paired_wavs_identical','sidecar_verified','existing_output_rejected_without_mutation','mismatched_state_rejected_before_publication','incomplete_trace_rejected_before_publication']),'four paired CLI gates');side=read('references-local/cutoff-ab-cli01/pair.json');require(len(side['input_sha256'])==7 and side['start_ticks']==START and side['end_ticks']==START+SPAN and side['open_alpha']==1. and side['closed_alpha']==.5 and side['new_continuous_history_duration_s']==0,'paired CLI provenance')
 for n,h in side['code_sha256'].items():require(sha(ROOT/n)==h,'sidecar code '+n)
 size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'finite budget and reserve');staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');names=set(old['source_sha256'])|{'evidence/voice_cutoff_tests01.json'}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 r=dict(schema='rf-d/same-origin-cutoff-ab/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/'evidence/voice_cutoff_tests01.json'),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,new_private_bytes=size,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),original_circuit_sources_unchanged=True,new_open_duration_s=.008,new_continuous_history_duration_s=0,start_ticks=START,end_ticks=START+SPAN,accepted_steps=ref['accepted_steps'],fine_endpoints=ref['fine_steps'],new_independent_nonlinear_rows=ref['independent_nonlinear_rows'],closed_independent_equations_inherited=1374*sum(f['closed_selected_accepted_count'] for f in ref['forks']),closed_equations_reexecuted=False,shared_clock_states=11,state_coordinates=229,seam_compared_accepted=8,common_origin_values=458,max_state_gate_ratio=max(x['gate_ratio'] for x in ref['same_clock_refinement']),restores=ref['restores'],replayed_accepted_steps=ref['replayed_accepted_steps'],oscillator_resets=sum(len(p['resets']) for p in ref['profiles']),maximum_active_replay_probes=ref['maximum_active_replay_probes'],rejected_corruptions=8,atomic_rollbacks=2,wav_frames=384,wav_duration_s=.008,wav_count=4,audio_refinement=audio['refinement'],ab_metrics=audio['ab_metrics'],cli_integration_checks=4,new_library_compile=False,new_cargo_cache=False,inherited_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,physical_fidelity=False,real_time=False,heap_measured=False,deadline_measured=False,cutoff_ab_reference={'path':receipts[2],'sha256':sha(ROOT/receipts[2])},cutoff_ab_listening={'path':receipts[3],'sha256':sha(ROOT/receipts[3]),'files':audio['files']},local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
 for k in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening']:r[k]=old[k]
 return r
def main():
 try:r=audit()
 except Exception:
  first=traceback.format_exc()
  try:audit();second='unexpected pass'
  except Exception:second=traceback.format_exc()
  k=1
  while(ROOT/f'evidence/cutoff_ab_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/cutoff_ab_qa_failure{k:02d}.json').write_text(json.dumps(dict(passed=False,failure=first,replay=second,source_base64=base64.b64encode((ROOT/'tools/validate_cutoff_ab.py').read_bytes()).decode()),indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CUTOFF_AB_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
