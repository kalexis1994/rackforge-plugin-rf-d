"""Protect prior release and admit only the archive-based small-signal probe."""
import base64,hashlib,json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_cutoff_opening_tests01.json'
ATTR=b'\n/tools/cutoff_opening_runner.rs text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_candidate_cycles_tests01.json';old=read(previous);before=read('evidence/voice_cutoff_opening_before01.json');require(old['passed'] and sha(ROOT/previous)==before['previous_qa_sha256'],'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(s) for n,s in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'new caller attribute');bad=read('evidence/voice_cutoff_opening01.json');good=read('evidence/voice_cutoff_opening02.json');require(not bad['passed'] and good['passed'] and len(bad['commands'])==1 and bad['commands'][0]['exit_code']!=0,'retained compile failure')
 require(bad['replay']['command']==bad['commands'][0]['command'] and bad['replay']['exit_code']==bad['commands'][0]['exit_code'] and bad['replay']['stderr']==bad['commands'][0]['stderr'],'identical compile replay')
 failed=bad['failed_source_text'];rust=failed['tools/cutoff_opening_runner.rs'];require(hashlib.sha256(rust.encode()).hexdigest()==bad['source_sha256']['tools/cutoff_opening_runner.rs'],'retained failed caller identity');fixed=rust.replace("b'RFCUTI01'",'b"RFCUTI01"').replace("b'RFCUTO01'",'b"RFCUTO01"').replace('[.5;4]','[0.5;4]').replace('[0.,.2,-.3,.1,.4]','[0.,0.2,-0.3,0.1,0.4]');require((ROOT/'tools/cutoff_opening_runner.rs').read_bytes()==fixed.encode(),'syntax-only caller repair')
 require(failed['tools/probe_cutoff_opening.py'].split('def compare',1)[1].split('def main',1)[0]==(ROOT/'tools/probe_cutoff_opening.py').read_text(encoding='utf8').split('def compare',1)[1].split('def main',1)[0],'unchanged audit and gates')
 require(bad['initial_input_sha256']==good['initial_input_sha256'],'same DC input bytes')
 for r in [bad,good]:
  require(r['source_sha256']==r['source_sha256_after'] and r['private_used_sha256']==r['private_used_sha256_after'],'immutable attempt')
  for n,h in r['private_used_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'frozen library')
  for p in r['outputs']:require(sha(ROOT/p['path'])==p['sha256'],'retained output');private[p['path']]=p['sha256']
 for n,h in good['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
 require(good['wall_s']<=480 and good['reference_wall_s']<=120 and len(good['commands'])==2 and all(c['exit_code']==0 and c['wall_s']<=120 for c in good['commands']),'bounded successful probe');require(good['initial_free_bytes']>=1024**3+8*1024**2 and good['final_free_bytes']>=1024**3 and sum(p['bytes'] for p in good['outputs'])<=8*1024**2,'storage budget')
 require(len(good['rows'])==3 and good['ideal_bus_small_signal'] and good['shared_complex_solver'] and not any(good[k] for k in ['new_library_compile','new_audio','physical_fidelity','real_time']) and good['new_roots']==good['new_trajectories']==good['new_spice_processes']==0,'small-signal scope')
 for r in good['rows']:
  require(r['native_dc_max_a']<=2e-11 and r['mass_matrix_ratio']<=1 and len(r['derivatives'])==2 and len(r['responses'])==8,'DC/mass coverage')
  for d in r['derivatives']:require(d['matrix_ratio']<=1,'G FD gate')
  for a in r['responses']:require(a['voltage_comparison_ratio']<=1 and a['admittance_comparison_ratio']<=1 and max(a['residuals_a_per_bus_v'])<=1e-11,'AC gate')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/cutoff-opening-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,new_dc_candidates=3,new_fd_columns=408,new_complex_solves=48,new_transfer_observations=24,shared_complex_solver=True,ideal_bus_small_signal=True,physical_fidelity=False,real_time=False,new_library_compile=False,new_audio=False,new_spice_processes=0,new_roots=0,new_trajectories=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_cutoff_opening.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_cutoff_opening_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_cutoff_opening_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CUTOFF_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
