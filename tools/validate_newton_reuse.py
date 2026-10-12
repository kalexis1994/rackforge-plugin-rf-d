"""Publish source/artifact identities for scoped exact-operation reuse."""
import json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
from prepare_newton_reuse_portability import audit_portability
OUT='evidence/newton_reuse_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 audit_portability()
 previous='evidence/voice_contour_cycle_tests01.json';old=read(previous);ref=read('evidence/newton_reuse_reference01.json');require(old['passed'] and ref['passed'] and ref['operation_reuse_admitted'] and ref['full_observation_identity'],'admitted reference');require(ref['source_sha256']==ref['source_sha256_after'],'stable auditor')
 for n,h in ref['source_sha256'].items():require(sha(ROOT/n)==h,'auditor source')
 for n,h in ref['private_input_sha256'].items():require(sha(ROOT/n)==h,'auditor private')
 require(ref['accepted_steps']==13385 and ref['fine_steps']==26770 and ref['restores']==24 and ref['replayed_accepted_steps']==368 and ref['inherited_independent_nonlinear_rows']==38472 and not ref['independent_equations_reexecuted'],'inherited scope')
 require(ref['median_paired_speedup']>1 and not any(ref[k] for k in ['new_audio','real_time','physical_fidelity']) and ref['new_duration_s']==0,'performance scope')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/newton-reuse-release/v1',passed=True,base_commit=ref['base_commit'] if 'base_commit' in ref else read('evidence/newton_reuse_before01.json')['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=ref['private_input_sha256'],median_paired_speedup=ref['median_paired_speedup'],operation_reuse_admitted=True,full_observation_identity=True,full_profile_equal_files=ref['full_profile_equal_files'],full_profile_equal_bytes=ref['full_profile_equal_bytes'],accepted_steps=ref['accepted_steps'],fine_steps=ref['fine_steps'],restores=ref['restores'],replayed_accepted_steps=ref['replayed_accepted_steps'],inherited_independent_nonlinear_rows=38472,independent_equations_reexecuted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_base64=__import__('base64').b64encode((ROOT/'tools/validate_newton_reuse.py').read_bytes()).decode())
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/newton_reuse_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/newton_reuse_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('REUSE_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
