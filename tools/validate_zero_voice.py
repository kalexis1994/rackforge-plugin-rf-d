"""Reject promotion while admitting exact laboratory evidence and its unchanged inputs."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_zero_voice import ATTR as A1,RUST,bank,solver,probe,kernel
from prepare_zero_scan import ATTR as A2,solver as scan_solver
from prepare_zero_profile import ATTR as A3,sources as profile_sources
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_zero_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 old=read('evidence/voice_extended_tests01.json');before=read('evidence/voice_zero_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/'evidence/voice_extended_tests01.json') and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'frozen base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+A1+A2+A3 and (ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==saved['crates/rf-d-circuit/src/lib.rs'],'only lab LF rules; no public exports')
 for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic document prefix')
 require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_extended_tests01.json',b'voice_zero_tests01.json')),'declared README QA replacement')
 expected={RUST[0]:probe(solver(),True),RUST[1]:kernel('zero_voice_solver.rs'),RUST[2]:probe((ROOT/'crates/rf-d-circuit/src/block_decay_solver.rs').read_text(encoding='utf8'),False),RUST[3]:kernel('zero_baseline_solver.rs'),'tools/zero_scan_solver.rs':probe(scan_solver(),False),'tools/zero_scan_kernel.rs':kernel('zero_scan_solver.rs'),'tools/zero_scan_bench.rs':(ROOT/'tools/zero_voice_bench.rs').read_text(encoding='utf8').replace('zero_voice_kernel.rs','zero_scan_kernel.rs').replace('ZERO_BENCH_PASSED','ZERO_SCAN_BENCH_PASSED'),**profile_sources()}
 for n,s in expected.items():require((ROOT/n).read_text(encoding='utf8')==s,'declared transformation '+n)
 raw,inputs=bank();require(raw==(ROOT/'references-local/voice-zero-inputs01/pairs.bin').read_bytes() and len(raw)==12+168*18368,'complete own bank derivation')
 for n in inputs:require(sha(ROOT/n)==old['private_input_sha256'][n],'own bank input unchanged')
 receipts=['evidence/voice_zero_inputs01.json','evidence/voice_zero_bench01.json','evidence/voice_zero_scan_inputs01.json','evidence/voice_zero_scan01.json','evidence/voice_zero_profile01.json']
 for name in receipts:
  r=read(name);require(r['passed'],'measured receipt '+name)
  for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h,'executed source '+n)
  if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable sources')
  for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private input');private[n]=h
  if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private inputs')
  for o in r.get('outputs',[]):require(sha(ROOT/o['path'])==o['sha256'] and (ROOT/o['path']).stat().st_size==o['bytes'],'retained measured output');private[o['path']]=o['sha256']
  if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler identity')
 a,b,p=[read(f'evidence/voice_zero_{n}01.json') for n in ['bench','scan','profile']]
 for r in [a,b]:require(r['numeric_bank_exact'] and r['ieee_cases']==1280 and r['signed_zero_negative_control'] and r['error_policy_checks']==6 and r['complete_stamp_bit_fields']==35471184 and not r['cost_utility_passed'] and not r['production_promoted'] and len(r['rounds'])==5 and not r['replays'] and all(c['exit_code']==0 for c in r['commands']) and r['commands'][0]['wall_s']<=120 and r['commands'][1]['wall_s']<=300,'exact numeric rejection of utility')
 for r in [a,b]:require('IEEE_PASSED,1280,rejects=260,signed_zero_control=1' in r['commands'][-1]['stdout'],'observed IEEE rejection counts')
 require(a['solver_scratch_bytes']==[459656,564144] and b['solver_scratch_bytes']==[459656,459656],'measured fixed storage')
 require(p['all_1834_f64_and_counters_identical'] and p['pairs']==168 and p['timing_is_nested'] and p['timing_overhead_not_subtracted'] and not p['production_promoted'] and len(p['phases'])==18 and p['phases'][0]['calls']==168 and not p['replays'] and all(c['exit_code']==0 for c in p['commands']),'current profiling exact scope')
 size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=96*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'budget and reserve');staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');names=set(old['source_sha256'])|{'evidence/voice_extended_tests01.json'}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 r=dict(schema='rf-d/exact-zero-traversal-rejected-cost/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/'evidence/voice_extended_tests01.json'),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),new_private_bytes=size,public_circuit_sources_unchanged=True,public_block_library_sha256=old['public_block_library_sha256'],production_promoted=False,candidates_rejected_for_cost=2,numeric_bank_pairs=168,new_selected_pairs=90,complete_stamp_bit_fields=35471184,bit_fields_per_pair=1834,current_pair_counters_compared=True,historical_counters_known_pairs=24,ieee_cases_per_candidate=1280,ieee_rejections_per_candidate=260,signed_zero_negative_control=True,error_policy_checks_per_candidate=6,combined_median_ratio=a['median_ratio'],combined_worst_round_ratio=a['worst_round_ratio'],combined_scratch_extra_bytes=104488,csr_median_ratio=b['median_ratio'],csr_worst_round_ratio=b['worst_round_ratio'],csr_scratch_extra_bytes=0,utility_median_gate=.95,utility_worst_gate=1.05,current_profile=p['phases'],timing_is_nested=True,timing_overhead_not_subtracted=True,new_audio=False,new_circuit_duration_s=0,new_independent_nonlinear_rows=0,previous_native_audio_duration_s=.068004,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,lab_stack_bytes=33554432,inherited_test_count=255,covered_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,heap_measured_this_block=False,deadline_measured=False,physical_fidelity=False,real_time=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
 for k in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening']:r[k]=old[k]
 return r
def main():
 try:r=audit()
 except Exception:
  first=traceback.format_exc()
  try:audit();second='unexpected pass'
  except Exception:second=traceback.format_exc()
  k=1
  while(ROOT/f'evidence/voice_zero_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_zero_qa_failure{k:02d}.json').write_text(json.dumps(dict(passed=False,failure=first,replay=second,failed_source_base64=base64.b64encode((ROOT/'tools/validate_zero_voice.py').read_bytes()).decode()),indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('ZERO_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'],flush=True)
if __name__=='__main__':main()
