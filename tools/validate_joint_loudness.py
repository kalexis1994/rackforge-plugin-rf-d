"""Release audit: protected history, generated access repair, coupled equations and scope."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_joint_loudness import ATTR
from repair_joint_loudness import repaired
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_loudness_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_cutoff_cycles_tests01.json';old=read(previous);before=read('evidence/voice_loudness_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base')
 saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'laboratory Rust attributes');require((ROOT/'tools/joint_loudness_kernel.rs').read_bytes()==repaired().encode(),'declared loaded equations/access repair')
 bad=read('evidence/voice_loudness_native01.json');require(not bad['passed'] and len(bad['commands'])==len(bad['replays'])==1 and bad['commands'][0]['stderr']==bad['replays'][0]['stderr'] and bad['commands'][0]['exit_code']!=0,'original compile rejection/replay')
 for n,s in bad['failed_source_text'].items():require(hashlib.sha256(s.encode()).hexdigest()==bad['source_sha256'][n],'failed source stored exactly')
 require(bad['source_sha256']==bad['source_sha256_after'] and bad['private_used_sha256']==bad['private_used_sha256_after'],'failure inputs immutable')
 inp=read('evidence/voice_loudness_inputs02.json');native=read('evidence/voice_loudness_native02.json');ref=read('evidence/voice_loudness_reference01.json');obs=read('evidence/voice_loudness_observations01.json')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared inputs '+n)
 for obj in [native,ref,obs]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'successful stable measurement')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measurement source '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler/private identities')
 for n,h in native['private_used_sha256'].items():require(private[n]==h,'same protected input')
 for attempt in [bad,native]:
  for p in attempt['outputs']:require(sha(ROOT/p['path'])==p['sha256'],'artifact identity');private[p['path']]=p['sha256']
 for n,h in obs['private_input_sha256'].items():require(private[n]==h,'observation input')
 require(len(native['commands'])==2 and all(c['exit_code']==0 for c in native['commands']) and native['commands'][0]['wall_s']<=120 and native['commands'][1]['wall_s']<=300 and not native['replays'],'native budgets')
 require(native['minimum_free_bytes']>=native['reserve_bytes']==1024**3 and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and sum(p['bytes'] for p in native['outputs'])<=16*1024**2,'disk budget')
 require('profiles=12,steps=288,bit_replays=12' in native['commands'][1]['stderr'] and ref['independent_nonlinear_rows']==9840 and ref['independent_candidates']==48 and ref['first_step_bit_replays']==12 and len(ref['root_checks'])==24 and len(ref['profiles'])==12 and len(ref['same_clock_refinement'])==6 and all(p['gate_ratio']<=1 for p in ref['same_clock_refinement']) and obs['endpoint_vectors']==24 and obs['current_values']==72,'new coverage')
 require(ref['wall_s']<=300 and ref['loaded_follower_admitted'] and not any(ref[k] for k in ['full_contour_admitted','adaptive_controller_admitted','new_audio','physical_fidelity','real_time']),'scope')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged release')
 sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/joint-loudness-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,independent_candidates=48,independent_nonlinear_rows=9840,new_steps=288,first_step_bit_replays=12,native_port_endpoint_vectors=24,native_port_current_values=72,loaded_follower_admitted=True,full_contour_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_loudness.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  n=1
  while (ROOT/f'evidence/voice_loudness_qa_failure{n:02d}.json').exists():n+=1
  (ROOT/f'evidence/voice_loudness_qa_failure{n:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('LOUDNESS_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
