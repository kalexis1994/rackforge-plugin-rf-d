"""Release only bounded, refined, audited adaptive returns; preserve old bytes."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_candidate_cycles import ATTR,REPLACEMENTS
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links

OUT='evidence/voice_candidate_cycles_tests01.json'
def read(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_dynamic_direction_tests01.json';old=read(previous);before=read('evidence/voice_candidate_cycles_before01.json');require(old['passed'] and sha(ROOT/previous)==before['previous_qa_sha256'],'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'new caller attributes');expected=(ROOT/'tools/joint_corrected_cycles_runner.rs').read_text(encoding='utf8')
 for a,b in REPLACEMENTS:require(expected.count(a)==1,'single substitution');expected=expected.replace(a,b)
 require((ROOT/'tools/joint_candidate_cycles_runner.rs').read_bytes()==expected.encode(),'exact caller derivative');inputs=read('evidence/voice_candidate_cycles_inputs01.json');require(inputs['passed'] and inputs['goal_ticks']==5373952000 and inputs['substitutions']==[list(x) for x in REPLACEMENTS] and len(inputs['outputs'])==2,'declared inputs')
 require(inputs['candidate_sha256']==private[inputs['candidate_path']],'admitted candidate root')
 for p in inputs['outputs']:require(sha(ROOT/p['path'])==p['sha256'] and p['bytes']==3224,'seed');private[p['path']]=p['sha256']
 for n,h in inputs['source_sha256'].items():require(sha(ROOT/n)==h,'prepare source')
 native=read('evidence/voice_candidate_cycles_native01.json');ref=read('evidence/voice_candidate_cycles_reference01.json')
 for obj in [native,ref]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable measurement')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measurement source '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'stable native input/compiler')
 for n,h in native['private_used_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'used input')
 for p in native['outputs']:require(sha(ROOT/p['path'])==p['sha256'],'native output');private[p['path']]=p['sha256']
 require(native['workers']==2 and native['processor_count']>=2 and native['initial_available_memory_bytes']>=1024**3 and native['lab_stack_bytes']==33554432 and native['reserve_bytes']==1024**3 and native['estimated_output_bytes']==64*1024**2,'resource contract')
 require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['minimum_free_bytes']>=native['reserve_bytes'] and native['wall_s']<=7400 and sum(p['bytes'] for p in native['outputs'])<=native['estimated_output_bytes'],'resource result');require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'],'successful compilation')
 require(len(native['profiles'])==2 and all(p['exit_code']==0 and p['wall_s']<=7200 and not p['administrative_stop'] for p in native['profiles']),'completed native profiles');require(not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'scope')
 require(ref['wall_s']<=300 and ref['adaptive_cycles_admitted'] and ref['refinement_admitted'] and len(ref['profiles'])==2 and len(ref['shared_clock_points'])==42 and len(ref['return_refinement'])==3,'refinement scope')
 for n,h in ref['input_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'reference input')
 independent=ref['new_independent'];require(len(independent['root_checks'])==36 and sum(x['rows'] for x in independent['root_checks'])==14400 and len(independent['current_checks'])==24 and len(independent['temporal_checks'])==12,'selected coverage')
 for x in independent['root_checks']:require(x['residual_gate_ratio']<=1 and x['correction_gate_ratio']<=1,'independent root gates')
 require(not any(ref[k] for k in ['steady_periodicity_admitted','global_settling_bound','physical_fidelity','real_time','independent_all_step_propagation','new_audio']) and ref['independent_roots']==0,'limited admission')
 for p in ref['profiles']:require(len(p['events'])==4 and len(p['cycles'])==3 and p['restore_bit_replays']==3 and p['endpoints']==2*p['intervals'],'profile coverage')
 require(ref['improvement_persists']==all(c['capacitor_l2_ratio_to_original_base']<=.01 and c['capacitor_max_ratio_to_original_base']<=.01 and c['j7_ratio_to_original_base']<=.01 for p in ref['profiles'] for c in p['cycles']),'measured hypothesis')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/candidate-cycles-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,adaptive_cycles_admitted=True,refinement_admitted=True,improvement_persists=ref['improvement_persists'],new_independent_nonlinear_rows=14400,new_independent_candidates=36,new_current_observations=24,new_lte_observations=12,new_return_intervals=6,new_restore_bit_replays=6,steady_periodicity_admitted=False,physical_fidelity=False,real_time=False,independent_roots=0,independent_all_step_propagation=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,new_library_compile=False,new_audio=False,new_spice_processes=0,physical_cards_changed=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))

def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_candidate_cycles.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_candidate_cycles_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_candidate_cycles_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CANDIDATE_QA',r['passed'],r['improvement_persists'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
