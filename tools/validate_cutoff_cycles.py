"""Release exact continuations; keep optional listening separate from numerical admission."""
import base64,hashlib,json,subprocess,traceback,wave
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from prepare_cutoff_cycles import ATTR,MARKS,CALLER_REPLACEMENTS,WRAPPER_REPLACEMENTS,rendered
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
from render_cutoff_cycles import actual_signal
from render_vco1_circuit import coefficients,synthesize
OUT='evidence/voice_cutoff_cycles_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_cutoff_temporal_tests01.json';old=read(previous);before=read('evidence/voice_cutoff_cycles_before01.json');require(old['passed'] and sha(ROOT/previous)==before['previous_qa_sha256'],'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'caller attributes')
 for target,source,changes in [('tools/joint_cutoff_cycles_runner.rs','tools/joint_cutoff_temporal_runner.rs',CALLER_REPLACEMENTS),('tools/run_cutoff_cycles.py','tools/run_candidate_cycles.py',WRAPPER_REPLACEMENTS)]:require((ROOT/target).read_bytes()==rendered(source,changes).encode(),'declared source '+target)
 inputs=read('evidence/voice_cutoff_cycles_inputs01.json');require(inputs['passed'] and inputs['marks']==MARKS and inputs['cutoff_fraction']==1 and inputs['caller_substitutions']==[list(v) for v in CALLER_REPLACEMENTS] and inputs['wrapper_substitutions']==[list(v) for v in WRAPPER_REPLACEMENTS],'predeclared inputs')
 for n,h in inputs['source_sha256'].items():require(sha(ROOT/n)==h,'preparation source')
 native=read('evidence/voice_cutoff_cycles_native01.json');ref=read('evidence/voice_cutoff_cycles_reference02.json');listen=read('evidence/voice_cutoff_cycles_listening01.json');bad=read('evidence/voice_cutoff_cycles_reference01.json')
 require(not bad['passed'] and bad['source_sha256']==bad['source_sha256_after'] and bad['failure'].splitlines()[-1]==bad['replay'].splitlines()[-1]=="NameError: name 'D' is not defined",'preserved reference failure/replay')
 failed=bad['failed_source_text'];require(hashlib.sha256(failed.encode()).hexdigest()==bad['source_sha256']['tools/check_cutoff_cycles.py'],'failed source identity');current=(ROOT/'tools/check_cutoff_cycles.py').read_text(encoding='utf8');require(current.split('START=')[1].split('def main():')[0]==failed.split('START=')[1].split('def main():')[0] and 'from check_joint_reference import D\n' in current,'unchanged auditor body/gates, missing import repair')
 require(bad['source_sha256']['evidence/voice_cutoff_cycles_native01.json']==ref['source_sha256']['evidence/voice_cutoff_cycles_native01.json'],'same native data receipt')
 for obj in [native,ref,listen]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable measurement')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler/input identity')
 for n,h in native['private_used_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'frozen input')
 for p in native['outputs']:require(sha(ROOT/p['path'])==p['sha256'],'native output');private[p['path']]=p['sha256']
 require(native['reserve_bytes']==1024**3 and native['estimated_output_bytes']==64*1024**2 and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['minimum_free_bytes']>=native['reserve_bytes'] and sum(p['bytes'] for p in native['outputs'])<=native['estimated_output_bytes'],'disk resources');require(native['workers']==2 and native['processor_count']>=2 and native['initial_available_memory_bytes']>=1024**3 and native['lab_stack_bytes']==33554432 and native['wall_s']<=2600,'worker/time resources');require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'] and len(native['profiles'])==2 and all(p['exit_code']==0 and not p['administrative_stop'] and p['wall_s']<=2400 for p in native['profiles']),'successful native campaign')
 for n,h in ref['input_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'reference input')
 counts=dict(independent_candidates=138,independent_nonlinear_rows=55200,current_observations=92,lte_observations=46,new_restore_bit_replays=4)
 for k,v in counts.items():require(ref[k]==v,'coverage '+k)
 require(ref['wall_s']<=300 and ref['continuation_admitted'] and len(ref['profiles'])==2 and len(ref['same_clock_refinement'])==25 and ref['period_refinement_cents']<=1 and all(p['exact_checkpoint_seam'] and len(p['events'])==2 and len(p['control_checkpoint_ledgers'])==20 and p['new_intervals']<=60000 for p in ref['profiles']),'complete finite window');require(ref['new_initial_roots_applied']==ref['native_auxiliary_vco_startup_solves']==0 and not any(ref[k] for k in ['inherited_prefix_reexecuted','independent_all_step_propagation','steady_periodicity_admitted','physical_fidelity','real_time','new_audio']),'numerical scope')
 for obj in ref['new_independent']:
  for c in obj['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent equations')
 hypothesis=all(p['j7_seam_relative']<=.01 for p in ref['profiles']) and ref['listening_proposal']['phase_aligned_rms_error_v']<=.01*ref['listening_proposal']['fine_rms_v']+1e-7
 require(hypothesis==ref['listening_candidate_admitted'] and listen['listening_admitted']==hypothesis and not listen['full_audio_duration_simulated'] and not listen['complete_voice'] and not listen['physical_fidelity'] and not listen['real_time'],'listening scope')
 if listen['listening_admitted']:
  require(listen['pcm_roundtrip_exact'] and listen['source_maximum_half_ticks']==32768 and listen['duration_s']==2 and listen['volts_per_full_scale']==.1 and listen['gain_relative_to_8v_adapter']==80 and listen['highest_harmonic_hz']<=.45*48000 and len(listen['files'])==1,'adapter recipe');phase,v,freq,window=actual_signal(ref,32768);c=coefficients(phase,v,ref['listening_proposal']['harmonics']);audio=synthesize(c,freq,48000,duration=2.,volts_per_full_scale=.1)
  for p in listen['files']:
   require(sha(ROOT/p['path'])==p['sha256'],'WAV identity')
   with wave.open(str(ROOT/p['path']),'rb') as w:require(w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==48000 and w.getnframes()==96000 and w.readframes(96000)==np.rint(audio*32767).astype('<i2').tobytes(),'independent publication payload replay')
   private[p['path']]=p['sha256']
 else:require(not listen['files'],'no WAV under rejected loop hypothesis')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged release');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/cutoff-cycles-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,continuation_admitted=True,inherited_prefix_reexecuted=False,new_initial_roots_applied=0,native_auxiliary_vco_startup_solves=0,steady_periodicity_admitted=False,physical_fidelity=False,real_time=False,new_audio=listen['listening_admitted'],new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=listen,official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_cutoff_cycles.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_cutoff_cycles_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_cutoff_cycles_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CUTOFF_CYCLES_QA',r['passed'],r['new_audio'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
