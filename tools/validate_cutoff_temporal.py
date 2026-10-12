"""Release control transients with protected history and scoped numeric gates."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_cutoff_temporal import ATTR,REPLACEMENTS,MARKS
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_cutoff_temporal_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_cutoff_opening_tests01.json';old=read(previous);before=read('evidence/voice_cutoff_temporal_before01.json');require(old['passed'] and sha(ROOT/previous)==before['previous_qa_sha256'],'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'caller attribute');s=(ROOT/'tools/joint_candidate_cycles_runner.rs').read_text(encoding='utf8')
 for a,b in REPLACEMENTS:require(s.count(a)==1,'single caller substitution');s=s.replace(a,b)
 require((ROOT/'tools/joint_cutoff_temporal_runner.rs').read_bytes()==s.encode(),'declared caller');inputs=read('evidence/voice_cutoff_temporal_inputs01.json');require(inputs['passed'] and inputs['substitutions']==[list(v) for v in REPLACEMENTS] and inputs['marks']==MARKS and len(inputs['profiles'])==4,'inputs')
 for n,h in inputs['source_sha256'].items():require(sha(ROOT/n)==h,'preparation identity')
 native=read('evidence/voice_cutoff_temporal_native01.json');ref=read('evidence/voice_cutoff_temporal_reference01.json')
 for obj in [native,ref]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable measurement')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measurement identity '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler/input identity')
 for n,h in native['private_used_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'frozen input')
 for p in native['outputs']:require(sha(ROOT/p['path'])==p['sha256'],'native output');private[p['path']]=p['sha256']
 require(native['reserve_bytes']==1024**3 and native['estimated_output_bytes']==32*1024**2 and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['minimum_free_bytes']>=native['reserve_bytes'] and sum(p['bytes'] for p in native['outputs'])<=native['estimated_output_bytes'],'disk budget');require(native['wall_s']<=3800 and native['lab_stack_bytes']==33554432 and len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'],'compile/resources');require(len(native['profiles'])==4 and all(p['exit_code']==0 and not p['administrative_stop'] and p['wall_s']<=900 for p in native['profiles']),'complete profiles')
 for n,h in ref['input_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'reference input')
 counts=dict(independent_nonlinear_rows=28800,independent_candidates=72,current_observations=48,lte_observations=24,restore_bit_replays=8,nominal_prefix_bit_coordinates=800)
 for k,v in counts.items():require(ref[k]==v,'coverage '+k)
 require(ref['wall_s']<=300 and ref['own_temporal_controls_admitted'] and ref['control_effect_admitted'] and ref['new_roots']==0 and not any(ref[k] for k in ['independent_all_step_propagation','steady_periodicity_admitted','new_audio','physical_fidelity','real_time']),'scope')
 require(len(ref['new_independent'])==4 and len(ref['same_clock_refinement'])==2 and len(ref['nominal_controls'])==2 and all(p['final_ticks']==MARKS[-1] and p['intervals']<=12000 and len(p['control_ledgers'])==5 for p in ref['profiles']),'finite window coverage')
 for obj in ref['new_independent']:
  for c in obj['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent equation gates')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/cutoff-temporal-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,own_temporal_controls_admitted=True,control_effect_admitted=True,new_roots=0,independent_all_step_propagation=False,steady_periodicity_admitted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_cutoff_temporal.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_cutoff_temporal_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_cutoff_temporal_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CUTOFF_TEMPORAL_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
