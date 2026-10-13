"""Release exact quadrant assembly and equivalent CSR structural validation."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from prepare_voice_pivot import ATTR as A1,profile_sources,bank
from prepare_voice_block import ATTR as A2,block_kernel,block_bench
from prepare_voice_paired import ATTR as A3,paired,engine
from promote_voice_block import ATTR as A4,EXPORT,sources as public_sources
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_block_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
 old=read('evidence/voice_decay_tests01.json');before=read('evidence/voice_pivot_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/'evidence/voice_decay_tests01.json') and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base')
 saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+A1+A2+A3+A4+b'\n/crates/rf-d-circuit/src/block_decay_solver.rs text eol=lf\n','exact Rust rules');require((ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==saved['crates/rf-d-circuit/src/lib.rs']+EXPORT,'exports only')
 expected={**profile_sources(),'tools/voice_block_kernel.rs':block_kernel(),'tools/voice_block_bench.rs':block_bench(),'tools/voice_block_engine.rs':engine(),'tools/voice_pivot_paired.rs':paired(),**public_sources()}
 for n,s in expected.items():require((ROOT/n).read_text(encoding='utf8')==s,'declared transformation '+n)
 for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic doc prefix')
 require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_decay_tests01.json',b'voice_block_tests01.json')),'declared README replacement')
 inputs=read('evidence/voice_pivot_inputs01.json');data,_=bank();require(data==(ROOT/'references-local/voice-pivot-inputs01/pairs.bin').read_bytes() and inputs['pairs']==78 and inputs['record_bytes']==18368,'entire bank derivation')
 failure=read('evidence/voice_pivot_layout_failure01.json');failed=base64.b64decode(failure['failed_source_base64']);require(not failure['passed'] and 'declared finite bank' in failure['failure'] and 'declared finite bank' in failure['unchanged_replay'] and (ROOT/'tools/prepare_voice_pivot.py').read_bytes()==failed.replace(b'len(r)==18384',b'len(r)==18368'),'record-size failure/replay and one repair')
 rejected=read('evidence/voice_block_library_rejected01.json');snapshots={n:base64.b64decode(v) for n,v in rejected['preserved_source_base64'].items()}
 for n,b in snapshots.items():require(hashlib.sha256(b).hexdigest()==rejected['preserved_source_sha256'][n],'preserved V1 source '+n)
 names=['evidence/voice_pivot_inputs01.json','evidence/voice_pivot_bench01.json','evidence/voice_block_bench01.json','evidence/voice_block_paired_repair01.json','evidence/voice_block_paired02.json','evidence/voice_block_paired_reference02.json','evidence/voice_block_promotion01.json','evidence/voice_block_library01.json','evidence/voice_block_structure_inputs01.json','evidence/voice_block_library02.json','evidence/voice_block_portable01.json','evidence/voice_block_portable_reference01.json']
 for name in names:
  r=read(name);require(r['passed'],'admitted measurement '+name)
  for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h or n in snapshots and hashlib.sha256(snapshots[n]).hexdigest()==h,'measured or preserved source '+n)
  if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable measured sources')
  for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private use');private[n]=h
  if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private')
  for o in r.get('outputs',[]):require(sha(ROOT/o['path'])==o['sha256'],'new output');private[o['path']]=o['sha256']
  if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
 f=read('evidence/voice_block_paired01.json');require(not f['passed'] and len(f['replays'])==1 and f['commands'][0]['exit_code']==f['replays'][0]['exit_code']!=0,'paired compile rejection preserved')
 for o in f['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'failed output');private[o['path']]=o['sha256']
 broken=base64.b64decode(f['failed_source_base64']['tools/voice_pivot_paired.rs']);prefix=b'pub use rf_d_circuit::*;\n';require(broken.startswith(prefix) and (ROOT/'tools/voice_pivot_paired.rs').read_bytes()==broken[len(prefix):].replace(b'use rf_d_circuit::{decay_voice',prefix+b'use rf_d_circuit::{decay_voice',1),'only inner doc placement repair')
 pivot=read('evidence/voice_pivot_bench01.json');lab=read('evidence/voice_block_bench01.json');v1=read('evidence/voice_block_library01.json');v2=read('evidence/voice_block_library02.json');native=read('evidence/voice_block_portable01.json');ref=read('evidence/voice_block_portable_reference01.json')
 require(pivot['numeric_bank_passed'] and not pivot['cost_utility_passed'] and lab['cost_utility_passed'] and not v1['cost_utility_passed'] and v2['cost_utility_passed'],'separate rejected and admitted costs')
 require(v2['median_ratio']<=.9 and v2['worst_round_ratio']<=1.05 and v2['complete_stamp_bit_fields']==16468764 and 'STRUCTURE_PASSED,209764' in v2['commands'][-1]['stdout'],'same public utility/structure gates')
 for r in [pivot,lab,v1,v2]:require(not r['replays'] and all(c['exit_code']==0 and c['wall_s']<=300 for c in r['commands']),'bounded benchmark/build')
 require(native['passed'] and native['public'] and native['wall_s']<=600 and not native['replays'] and len(native['profiles'])==2 and ref['public_portable'] and ref['every_accepted_bits_identical'] and ref['admitted_prefix_identical'] and ref['duration_per_profile_s']==.004 and ref['new_independent_nonlinear_rows']==0 and ref['grid_states']==12,'public trajectory scope')
 inherited=0
 for maximum in [1048576,524288]:
  lines=(ROOT/f'references-local/decay-voice02/{maximum}/selected.txt').read_text(encoding='utf8').splitlines();tick=0
  for l in lines:
   if l.startswith('STEP,'):tick=int(l.split(',')[3])
   if l.startswith('SELECT,') and tick<=14911799296+2097152000:inherited+=1374
 size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=96*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'budget/reserve');staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');source_names=set(old['source_sha256'])|{'evidence/voice_decay_tests01.json'}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(source_names)}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 r=dict(schema='rf-d/exact-block-assembly-csr-policy/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/'evidence/voice_decay_tests01.json'),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),new_private_bytes=size,public_block_family_admitted=True,nominal_sources_unchanged=True,complete_stamp_bit_fields=16468764,structural_policy_positions=209764,numeric_bank_pairs=78,pivot_cost_rejected=True,public_quadrants_only_cost_rejected=True,public_median_ratio=v2['median_ratio'],public_worst_round_ratio=v2['worst_round_ratio'],every_accepted_bits_identical=True,accepted_steps=ref['accepted_steps'],fine_endpoints=ref['fine_endpoints'],grid_states=12,duration_per_profile_s=.004,new_circuit_duration_s=0,inherited_independent_nonlinear_rows=inherited,new_independent_nonlinear_rows=0,new_audio=False,previous_native_audio_duration_s=.036004,heap_measured_this_block=False,deadline_measured=False,lab_stack_bytes=33554432,new_cargo_cache=False,new_spice_processes=0,inherited_test_count=255,covered_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,physical_fidelity=False,real_time=False,public_block_library_sha256=sha(ROOT/'references-local/voice-block-library02/librf_d_circuit.rlib'),local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
 for k in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference']:r[k]=old[k]
 return r

def main():
 try:r=audit()
 except Exception:
  first=traceback.format_exc()
  try:audit();second='unexpected pass'
  except Exception:second=traceback.format_exc()
  k=1
  while(ROOT/f'evidence/voice_block_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_block_qa_failure{k:02d}.json').write_text(json.dumps(dict(passed=False,failure=first,replay=second,failed_source_base64=base64.b64encode((ROOT/'tools/validate_voice_block.py').read_bytes()).decode()),indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('BLOCK_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
