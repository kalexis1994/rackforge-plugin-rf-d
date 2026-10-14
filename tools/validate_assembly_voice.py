"""Admit direct assembly only with immutable history, public utility and every-advance equality."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_assembly_voice import ATTR as A1,RUST,kernel,bench,vco_helper
from promote_assembly_voice import ATTR as A2,EXPORT,sources as public_sources,paired,PAIRED,START,SPAN
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_assembly_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 old=read('evidence/voice_zero_tests01.json');before=read('evidence/voice_assembly_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/'evidence/voice_zero_tests01.json') and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'frozen base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+A1+b'\n/tools/assembly_vco_helper.rs text eol=lf\n'+A2,'declared LF rules');require((ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==saved['crates/rf-d-circuit/src/lib.rs']+EXPORT,'two isolated exports')
 for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic doc prefix')
 require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_zero_tests01.json',b'voice_assembly_tests01.json')),'declared README gate update')
 expected={RUST[0]:kernel(),RUST[1]:bench(),'tools/assembly_vco_helper.rs':vco_helper(),**public_sources(),PAIRED:paired()}
 for n,s in expected.items():require((ROOT/n).read_text(encoding='utf8')==s,'declared transformation '+n)
 snapshots={}
 for attempt,needle in [(1,'cannot find `joint_vco_fine`'),(2,'function `solve_linear_sparse` is private')]:
  f=read(f'evidence/voice_assembly_lab{attempt:02d}.json');repair=read(f'evidence/voice_assembly_repair{attempt:02d}.json');require(not f['passed'] and len(f['replays'])==1 and f['commands'][0]['exit_code']==f['replays'][0]['exit_code']!=0 and needle in f['commands'][0]['stderr'] and needle in f['replays'][0]['stderr'],'compile rejection and unchanged replay');require(repair['passed'] and repair['numeric_gates_unchanged'] and repair['failure_sha256']==sha(ROOT/repair['failure_path']),'repair binding')
  for n,b in f['failed_source_base64'].items():
   digest=hashlib.sha256(base64.b64decode(b)).hexdigest();require(digest==f['source_sha256'][n]==repair['before_source_sha256'][n],'preserved failed source');snapshots.setdefault(n,set()).add(digest)
  for o in f['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'retained failed output');private[o['path']]=o['sha256']
 # The numerical transformation and caller are unchanged across both binding repairs.
 f1=read('evidence/voice_assembly_lab01.json');f2=read('evidence/voice_assembly_lab02.json')
 for f in [f1,f2]:
  previous=base64.b64decode(f['failed_source_base64']['tools/prepare_assembly_voice.py']).decode('utf8');now=(ROOT/'tools/prepare_assembly_voice.py').read_text(encoding='utf8');require(previous[previous.index('def public_voice():'):previous.index('def kernel():')]==now[now.index('def public_voice():'):now.index('def kernel():')],'only adapter repair; physical transformation unchanged');require(base64.b64decode(f['failed_source_base64'][RUST[1]])==(ROOT/RUST[1]).read_bytes(),'same lab benchmark and gates')
 names=['evidence/voice_assembly_inputs01.json','evidence/voice_assembly_inputs02.json','evidence/voice_assembly_inputs03.json','evidence/voice_assembly_repair01.json','evidence/voice_assembly_repair02.json','evidence/voice_assembly_lab03.json','evidence/voice_assembly_promotion01.json','evidence/voice_assembly_public01.json','evidence/voice_assembly_paired01.json','evidence/voice_assembly_reference01.json']
 for name in names:
  r=read(name);require(r['passed'],'admitted receipt '+name)
  for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h or h in snapshots.get(n,set()),'current or preserved executed source '+n)
  if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable source inputs')
  for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private use');private[n]=h
  if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private inputs')
  for o in r.get('outputs',[]):require(sha(ROOT/o['path'])==o['sha256'] and (ROOT/o['path']).stat().st_size==o['bytes'],'measured output');private[o['path']]=o['sha256']
  if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
 lab,pub,native,ref=[read(f'evidence/{n}.json') for n in ['voice_assembly_lab03','voice_assembly_public01','voice_assembly_paired01','voice_assembly_reference01']]
 for r in [lab,pub]:require(r['numeric_bank_exact'] and r['cost_utility_passed'] and r['median_ratio']<=.95 and r['worst_round_ratio']<=1.05 and r['parts_bit_fields']==35548128 and r['complete_stamp_bit_fields']==35471184 and r['invalid_parts_cases']==12 and r['error_policy_checks']==6 and r['workspace_bytes']==[3378208,3378208] and len(r['rounds'])==5 and not r['replays'] and all(c['exit_code']==0 for c in r['commands']),'public/lab gates')
 require(pub['public'] and pub['new_library_compile'] and native['every_accepted_bits_identical'] and native['wall_s']<=1900 and not native['replays'] and len(native['profiles'])==2 and all(p['exit_code']==0 and p['wall_s']<=900 for p in native['profiles']),'bounded public trajectory');require(ref['every_accepted_bits_identical'] and ref['admitted_interval_identical'] and ref['grid_states']==12 and ref['new_independent_nonlinear_rows']==0 and ref['start_ticks']==START and ref['end_ticks']==START+SPAN,'matched own interval and charge scope')
 for maximum in [1048576,524288]:
  raw=(ROOT/f'references-local/extended-release01/{maximum}/checkpoints.bin').read_bytes();seed=(ROOT/f'references-local/voice-assembly-seeds01/{maximum}.ckp').read_bytes();require(sum(raw[k:k+3728]==seed for k in range(0,len(raw),3728))==1,'own unique seed by bytes')
 size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=96*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'budget/reserve');staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');source_names=set(old['source_sha256'])|{'evidence/voice_zero_tests01.json'}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(source_names)}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 ratio=sum(p['candidate_kernel_ns'] for p in ref['profiles'])/sum(p['baseline_kernel_ns'] for p in ref['profiles']);lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';r=dict(schema='rf-d/direct-loaded-assembly/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/'evidence/voice_zero_tests01.json'),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),new_private_bytes=size,public_assembly_family_admitted=True,original_families_unchanged=True,public_block_library_sha256=old['public_block_library_sha256'],public_assembly_library_sha256=sha(ROOT/lib),public_assembly_library_path=lib,parts_bit_fields=35548128,complete_stamp_bit_fields=35471184,total_assembly_bit_fields=71019312,numeric_bank_pairs=168,workspace_bytes=3378208,invalid_parts_cases=12,error_policy_checks=6,lab_median_ratio=lab['median_ratio'],public_median_ratio=pub['median_ratio'],public_worst_round_ratio=pub['worst_round_ratio'],paired_kernel_ratio=ratio,every_accepted_bits_identical=True,accepted_steps=ref['accepted_steps'],fine_endpoints=ref['fine_endpoints'],grid_states=12,start_ticks=START,end_ticks=START+SPAN,duration_per_profile_s=.004,new_circuit_duration_s=0,new_independent_nonlinear_rows=0,inherited_independent_nonlinear_rows=ref['inherited_independent_nonlinear_rows'],compile_rejections_preserved=2,unchanged_compile_replays=2,new_audio=False,previous_native_audio_duration_s=.068004,new_cargo_cache=False,new_spice_processes=0,lab_stack_bytes=33554432,inherited_test_count=255,covered_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,heap_measured_this_block=False,deadline_measured=False,physical_fidelity=False,real_time=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
 for k in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening']:r[k]=old[k]
 return r
def main():
 try:r=audit()
 except Exception:
  first=traceback.format_exc()
  try:audit();second='unexpected pass'
  except Exception:second=traceback.format_exc()
  k=1
  while(ROOT/f'evidence/voice_assembly_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_assembly_qa_failure{k:02d}.json').write_text(json.dumps(dict(passed=False,failure=first,replay=second,failed_source_base64=base64.b64encode((ROOT/'tools/validate_assembly_voice.py').read_bytes()).decode()),indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('ASSEMBLY_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'],flush=True)
if __name__=='__main__':main()
