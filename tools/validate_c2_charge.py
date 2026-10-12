"""Release the new capacitor and documentary charge network without promoting the latch."""
import base64,hashlib,json,struct,subprocess,traceback
from decimal import Decimal
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_c2_charge import ATTR,kernel,caller,START,SPAN,SOURCES
from check_c2_charge import CODEC
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_c2_charge_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_loudness_control_tests01.json';old=read(previous);before=read('evidence/voice_c2_charge_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR and (ROOT/'tools/joint_c2_kernel.rs').read_bytes()==kernel().encode() and (ROOT/'tools/joint_c2_runner.rs').read_bytes()==caller().encode(),'declared217 extension')
 bad=read('evidence/voice_c2_charge_native01.json');snapshot=read('evidence/voice_c2_charge_failure_source_bytes01.json');require(not bad['passed'] and len(bad['commands'])==len(bad['replays'])==1 and bad['commands'][0]['exit_code']!=0 and bad['commands'][0]['stderr']==bad['replays'][0]['stderr'] and bad['source_sha256']==bad['source_sha256_after'],'preserved compile rejection/replay')
 raw={n:base64.b64decode(v) for n,v in snapshot['source_base64'].items()}
 for n,b in raw.items():require(hashlib.sha256(b).hexdigest()==bad['source_sha256'][n] and b.decode('utf8').replace('\r\n','\n')==bad['failed_source_text'][n],'exact failed bytes/logical source')
 oldk=raw['tools/joint_c2_kernel.rs'].decode();module='#[path="c2_charge_driver.rs"] pub mod c2_charge_driver;\n';require(oldk.startswith(module),'old declaration');plain=oldk[len(module):];index=plain.index('use rf_d_circuit');require((ROOT/'tools/joint_c2_kernel.rs').read_text(encoding='utf8')==plain[:index]+module+plain[index:],'only module declaration moved after doc comments');require((ROOT/'tools/joint_c2_body.rs').read_text(encoding='utf8')==raw['tools/joint_c2_body.rs'].decode().replace('let source=|k|','let source=|k:usize|'),'only source index typing repaired')
 inp=read('evidence/voice_c2_charge_inputs02.json');require(inp['passed'] and inp['start_ticks']==START and inp['phase_span_ticks']==SPAN and inp['sources']==SOURCES,'recipe')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared input '+n)
 for s in inp['seeds']:
  b=(ROOT/s['path']).read_bytes();row=CODEC.unpack(b);origin=struct.unpack('<8sQII2d410d',(ROOT/s['origin_path']).read_bytes());v=row[9:];require(sha(ROOT/s['path'])==s['sha256'] and private[s['origin_path']]==s['origin_sha256'] and struct.pack('<410d',*v[:205],*v[217:422])==struct.pack('<410d',*origin[6:]),'own inherited205 memory');require(v[205]==3.2 and v[422]==0 and s['new_c2_initial_charge_c']==3.2e-5,'C2 initial hypothesis');private[s['path']]=s['sha256']
 native=read('evidence/voice_c2_charge_native02.json');ref=read('evidence/voice_c2_charge_reference01.json')
 for obj in [native,ref]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable admitted campaign')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'private/compiler identity')
 for n,h in native['private_used_sha256'].items():require(private[n]==h,'private recipe')
 for f in native['outputs']:require(sha(ROOT/f['path'])==f['sha256'],'output artifact');private[f['path']]=f['sha256']
 require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and len(native['profiles'])==4 and all(p['exit_code']==0 and p['wall_s']<=300 for p in native['profiles']) and native['wall_s']<=1500 and not native['replays'],'native budget');require(native['minimum_free_bytes']>=native['reserve_bytes']==1024**3 and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and sum(f['bytes'] for f in native['outputs'])<=native['estimated_output_bytes']==32*1024**2,'disk budget')
 counts=dict(independent_candidates=80,independent_nonlinear_rows=17360,native_current_endpoint_vectors=40,native_current_values=280,new_steps=2400,restore_phase_replays=40,replayed_steps=3600,rejected_corruptions=16,inherited_bit_coordinates=410,source_boundary_bit_coordinates=434)
 for k,v in counts.items():require(ref[k]==v,'coverage '+k)
 require(ref['wall_s']<=300 and ref['dynamic_c2_admitted'] and len(ref['profiles'])==4 and len(ref['same_clock_refinement'])==12 and all(p['gate_ratio']<=1 for p in ref['same_clock_refinement']),'C2/refinement')
 for p in ref['profiles']:
  require(len(p['phases'])==5 and len(p['root_checks'])==10 and len(p['port_checks'])==10,'complete coverage')
  for n,h in p['input_sha256'].items():require(private[n]==h,'reference input')
  for c in p['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent equations')
  for l in [p['total_ledger'],*[v['ledger'] for v in p['phases']]]:
   require(l['not_independent_all_stage_quadrature'],'native quadrature scope')
   for c in l['capacitors']:require(Decimal(c['error_c'])<=Decimal(c['gate_c']),'charge balance')
   if p['final_decay']:require(l['c2_branch_integrals_c']['fast']==0.,'ON omits CR4 current')
 require(not any(ref[k] for k in ['full_contour_admitted','adaptive_controller_admitted','new_audio','physical_fidelity','real_time']),'scope')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged release');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/c2-charge-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,dynamic_c2_admitted=True,initial_c2_condition_not_preexisting_dynamic_charge=True,full_contour_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_c2_charge.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_c2_charge_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_c2_charge_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('C2_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
