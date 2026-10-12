"""Publish a bounded229 closure without inheriting vintage/RT admission."""
import base64,hashlib,json,struct,subprocess,traceback
from decimal import Decimal,localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_latch_charge import ATTR,kernel,caller,driver,NEW
from repair_latch_seed import PREDICTOR as KEY_SEED
from repair_latch_contact import PREDICTOR as CONTACT_SEED
from repair_latch_auditor import OLD as EMPTY_OLD,NEW as EMPTY_NEW
from repair_latch_alias import OLD as ALIAS_OLD,NEW as ALIAS_NEW
from refine_latch_charge import BODY_OLD,BODY_NEW,oracle
from check_latch_charge import checkpoint
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_latch_charge_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def rawmap(n):return {k:base64.b64decode(v) for k,v in read(n)['source_base64'].items()}
def audit():
 previous='evidence/voice_trigger_charge_tests01.json';old=read(previous);before=read('evidence/voice_latch_charge_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'attributes');require((ROOT/'tools/contour_closed_driver.rs').read_text(encoding='utf8')==driver(),'full original graph');expected=kernel().replace(' let seed=[0.;N];\n',KEY_SEED).replace(' let mut delta=[State::from_nodes(seed);2];',CONTACT_SEED+' let mut delta=[State::from_nodes(seed);2];');require((ROOT/'tools/joint_latch_kernel.rs').read_text(encoding='utf8')==expected and (ROOT/'tools/joint_latch_runner.rs').read_text(encoding='utf8')==caller(),'declared229 equation/seed assembly')
 failures=[];maps=[]
 for attempt,end in [(1,'phase=1,k=0:ExponentialDomain'),(2,'phase=2,k=0:IterationBudget')]:
  bad=read(f'evidence/voice_latch_charge_native{attempt:02d}.json');raw=rawmap(f'evidence/voice_latch_charge_failure_bytes{attempt:02d}.json');require(not bad['passed'] and bad['source_sha256']==bad['source_sha256_after'] and bad['private_used_sha256']==bad['private_used_sha256_after'] and bad['profiles'][0]['stderr']==bad['replays'][0]['stderr']==f'FAILURE,step,{end}\n','identical native rejection')
  for n,b in raw.items():require(hashlib.sha256(b).hexdigest()==bad['source_sha256'][n] and b.decode('utf8').replace('\r\n','\n')==bad['failed_source_text'][n],'failed source bytes')
  failures.append(bad);maps.append(raw)
 require(maps[1]['tools/joint_latch_kernel.rs']==maps[0]['tools/joint_latch_kernel.rs'].replace(b' let seed=[0.;N];\n',KEY_SEED.encode()),'only KEY seed');require((ROOT/'tools/joint_latch_kernel.rs').read_bytes()==maps[1]['tools/joint_latch_kernel.rs'].replace(b' let mut delta=[State::from_nodes(seed);2];',CONTACT_SEED.encode()+b' let mut delta=[State::from_nodes(seed);2];'),'only storage-free contact seed')
 rejected=[read(f'evidence/voice_latch_charge_reference{k:02d}.json') for k in [1,2,3,4]]
 for obj,end in zip(rejected,['numpy.linalg.LinAlgError: Singular matrix','numpy.linalg.LinAlgError: Singular matrix',"KeyError: 'EXTERNAL_S_TRIGGER'",'ValueError: 229 refinement']):
  require(not obj['passed'] and obj['source_sha256']==obj['source_sha256_after'] and obj['failure'].splitlines()[-1]==obj['replay'].splitlines()[-1]==end,'same oracle rejection');require(hashlib.sha256(obj['failed_source_text'].encode()).hexdigest()==obj['source_sha256']['tools/check_latch_charge.py'],'failed oracle bytes')
 require(rejected[0]['failed_source_text']==rejected[1]['failed_source_text'],'unchanged second oracle');require(rejected[2]['failed_source_text']==rejected[1]['failed_source_text'].replace(EMPTY_OLD,EMPTY_NEW),'only dead row adapter');require(rejected[3]['failed_source_text']==rejected[2]['failed_source_text'].replace(ALIAS_OLD,ALIAS_NEW),'only contact alias');require((ROOT/'tools/check_latch_charge.py').read_text(encoding='utf8')==oracle(rejected[3]['failed_source_text']),'only mesh recipe')
 diagnostic=read('evidence/voice_latch_charge_adapter_rejection01.json');b=base64.b64decode(diagnostic['source_base64']);require(hashlib.sha256(b).hexdigest()==diagnostic['source_sha256']==diagnostic['source_sha256_after'] and diagnostic['commands'][0]['stderr']==diagnostic['commands'][1]['stderr'] and all(c['exit_code']==1 for c in diagnostic['commands']),'preserved diagnostic');require((ROOT/diagnostic['source']).read_bytes()==b.replace(b'zeros==[84]',b'zeros==[66,84]'),'only diagnostic expectation')
 mesh=rawmap('evidence/voice_latch_charge_mesh_before01.json');require(mesh['tools/check_latch_charge.py'].decode()==rejected[3]['failed_source_text'] and (ROOT/'tools/joint_latch_body.rs').read_bytes()==mesh['tools/joint_latch_body.rs'].replace(BODY_OLD.encode(),BODY_NEW.encode()),'only codec mesh edit')
 native3=read('evidence/voice_latch_charge_native03.json');native=read('evidence/voice_latch_charge_native04.json');ref=read('evidence/voice_latch_charge_reference05.json');inp=read('evidence/voice_latch_charge_inputs04.json')
 for obj in [native3,native,ref]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable admitted measurements')
  for n,h in obj['source_sha256'].items():require(hashlib.sha256(mesh[n] if obj is native3 and n in mesh else (ROOT/n).read_bytes()).hexdigest()==h,'measured source '+n)
 for attempt in [*failures,native3,native]:
  require(attempt['private_used_sha256']==attempt['private_used_sha256_after'] and sha(Path(attempt['compiler']['path']))==attempt['compiler']['sha256'],'compiler/private identity')
  for n,h in attempt['private_used_sha256'].items():require(sha(ROOT/n)==h,'used private');private[n]=h
  for f in attempt['outputs']:require(sha(ROOT/f['path'])==f['sha256'],'artifact');private[f['path']]=f['sha256']
 for adapter in ['evidence/voice_latch_charge_auditor_adapter01.json','evidence/voice_latch_charge_alias_adapter01.json']:
  obj=read(adapter);require(obj['passed'] and not obj['native_reexecuted'] and not obj['numerical_gates_changed'],'adapter scope')
  for n,h in obj['private_input_sha256'].items():require(private[n]==h,'same native adapter data')
 for attempt in [1,2,3,4]:
  obj=read(f'evidence/voice_latch_charge_inputs{attempt:02d}.json');require(obj['passed'],'inputs')
  for s in obj['seeds']:require(sha(ROOT/s['path'])==s['sha256'],'seed');private[s['path']]=s['sha256']
 require(inp['predictor_substitution']==KEY_SEED and inp['contact_predictor_substitution']==CONTACT_SEED,'frozen predictors')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared inputs '+n)
 for s in inp['seeds']:
  cp=checkpoint((ROOT/s['path']).read_bytes());v=cp['values'];origin=struct.unpack('<8sQII4dII450d',(ROOT/s['origin_path']).read_bytes())[10:];require(struct.pack('<450d',*v[:225],*v[229:454])==struct.pack('<450d',*origin) and v[225:229]==NEW and v[454:]==[0.]*4,'own225 history/new bias');b=bytearray((ROOT/s['previous_seed_path']).read_bytes());b[16:20]=struct.pack('<I',s['half_ticks']);require(bytes(b)==(ROOT/s['path']).read_bytes(),'only seed step field')
 for on in [1,0]:
  for name in ['selected.txt','checkpoints.bin']:require((ROOT/f'references-local/latch-charge03/{on}-8192'/name).read_bytes()==(ROOT/f'references-local/latch-charge04/{on}-8192'/name).read_bytes(),'complete8192 repeat by bits')
 for k in [1,2]:
  for name in ['selected.txt','checkpoints.bin']:require((ROOT/'references-local/latch-charge03/1-16384'/name).read_bytes().startswith((ROOT/f'references-local/latch-charge{k:02d}/1-16384'/name).read_bytes()),'unchanged accepted prefixes')
 require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and len(native['profiles'])==4 and all(p['exit_code']==0 and p['wall_s']<=300 for p in native['profiles']) and native['wall_s']<=1500 and not native['replays'],'native budget');require(native['minimum_free_bytes']>=native['reserve_bytes']==1024**3 and sum(f['bytes'] for f in native['outputs'])<=native['estimated_output_bytes']==32*1024**2,'disk budget')
 counts=dict(independent_candidates=80,independent_nonlinear_rows=18320,native_current_endpoint_vectors=40,native_current_values=120,new_steps=3840,restore_phase_replays=40,replayed_steps=5760,rejected_corruptions=16,inherited_bit_coordinates=450,source_boundary_bit_coordinates=458)
 for k,v in counts.items():require(ref[k]==v,'coverage '+k)
 require(ref['wall_s']<=300 and ref['board2_local_closure_admitted'] and ref['old_nominal_prefix_bit_equal'] and len(ref['profiles'])==4 and len(ref['same_clock_refinement'])==12 and all(p['gate_ratio']<=1 for p in ref['same_clock_refinement']),'229 refinement')
 for p in ref['profiles']:
  require(len(p['phases'])==5 and len(p['root_checks'])==10 and len(p['port_checks'])==10,'phase coverage')
  for n,h in p['input_sha256'].items():require(private[n]==h,'oracle artifact')
  for c in p['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent equations')
  for l in [p['total_ledger'],*[v['ledger'] for v in p['phases']]]:
   require(l['not_independent_all_stage_quadrature'],'quadrature scope')
   for c in l['rows']:require(Decimal(c['error_c'])<=Decimal(c['gate_c']),'charge balance')
 require(not any(ref[k] for k in ['full_contour_trajectory_admitted','all_board2_junction_charge_admitted','adaptive_controller_admitted','new_audio','physical_fidelity','real_time']),'scope')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/latch-charge-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,board2_local_closure_admitted=True,full_contour_trajectory_admitted=False,all_board2_junction_charge_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:
  with localcontext() as ctx:ctx.prec=100;r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_latch_charge.py').read_text(encoding='utf8'))
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_latch_charge_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_latch_charge_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('LATCH_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
