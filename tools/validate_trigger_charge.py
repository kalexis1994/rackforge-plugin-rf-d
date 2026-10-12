"""Release a physically loaded trigger, preserve failures and limit causal claims."""
import base64,hashlib,json,struct,subprocess,traceback
from decimal import Decimal
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_trigger_charge import ATTR,kernel,caller,START,SPAN,SOURCES,SHORT
from repair_trigger_seed import PREDICTOR
from check_trigger_charge import CODEC
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_trigger_charge_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_c2_charge_tests01.json';old=read(previous);before=read('evidence/voice_trigger_charge_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR and (ROOT/'tools/joint_trigger_kernel.rs').read_bytes()==kernel().encode() and (ROOT/'tools/joint_trigger_runner.rs').read_bytes()==caller().encode(),'declared225 extension')
 bad=read('evidence/voice_trigger_charge_native01.json');snap=read('evidence/voice_trigger_charge_failure_bytes01.json');raw={n:base64.b64decode(v) for n,v in snap['source_base64'].items()};require(not bad['passed'] and bad['source_sha256']==bad['source_sha256_after'] and bad['private_used_sha256']==bad['private_used_sha256_after'] and bad['profiles'][0]['stderr']==bad['replays'][0]['stderr']=='FAILURE,step,phase=2,k=0:IterationBudget\n','same rejected step/replay')
 for n,b in raw.items():require(hashlib.sha256(b).hexdigest()==bad['source_sha256'][n] and b.decode('utf8').replace('\r\n','\n')==bad['failed_source_text'][n],'original failed bytes')
 failed_kernel=raw['tools/joint_trigger_kernel.rs'].decode();require((ROOT/'tools/joint_trigger_kernel.rs').read_text(encoding='utf8')==failed_kernel.replace(' let mut delta=[State::from_nodes(seed);2];',PREDICTOR+' let mut delta=[State::from_nodes(seed);2];'),'only storage-free predictor added')
 diag=read('evidence/voice_trigger_charge_diagnostic01.json');require(diag['passed'] and diag['source_sha256']==diag['source_sha256_after'] and not diag['arithmetic_and_gates_changed'] and 'RESULT,Some(IterationBudget)' in diag['commands'][-1]['stderr'],'diagnostic reproduces rejection')
 for n,h in diag['source_sha256'].items():require(hashlib.sha256(raw[n] if n in raw else (ROOT/n).read_bytes()).hexdigest()==h,'diagnostic source')
 inp=read('evidence/voice_trigger_charge_inputs02.json');require(inp['passed'] and inp['sources']==SOURCES and inp['short_states']==SHORT and inp['start_ticks']==START and inp['phase_span_ticks']==SPAN and inp['predictor_substitution']==PREDICTOR,'predeclared recipe')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared source '+n)
 for s in inp['seeds']:
  b=(ROOT/s['path']).read_bytes();r=CODEC.unpack(b);origin=struct.unpack('<8sQII3dII434d',(ROOT/s['origin_path']).read_bytes());v=r[10:];require(sha(ROOT/s['path'])==s['sha256'] and private[s['origin_path']]==s['origin_sha256'] and struct.pack('<434d',*v[:217],*v[225:442])==struct.pack('<434d',*origin[9:]),'own inherited217');require(v[221]==0 and v[446]==0 and v[223]-.01==s['new_c4_initial_v'],'new C7/C4 hypotheses');private[s['path']]=s['sha256']
 native=read('evidence/voice_trigger_charge_native02.json');ref=read('evidence/voice_trigger_charge_reference02.json');adapter=read('evidence/voice_trigger_charge_observer_adapter01.json');rejected=read('evidence/voice_trigger_charge_reference01.json');require(not rejected['passed'] and rejected['source_sha256']==rejected['source_sha256_after'] and rejected['failure'].splitlines()[-1]==rejected['replay'].splitlines()[-1]=='ValueError: actual native currents/voltages','preserved observer rejection')
 failed=rejected['failed_source_text'];require(hashlib.sha256(failed.encode()).hexdigest()==rejected['source_sha256']['tools/check_trigger_charge.py'] and (ROOT/'tools/check_trigger_charge.py').read_text(encoding='utf8')==failed.replace('float(x[223]-D(.01))','float(x[223])-float(D(.01))'),'ordered-float adapter only');require(adapter['passed'] and not adapter['numerical_gates_changed'] and not adapter['native_reexecuted'] and adapter['native_data_receipt_sha256']==sha(ROOT/'evidence/voice_trigger_charge_native02.json') and adapter['maximum_current_error_a']<=1e-9 and adapter['absolute_difference_v']<1e-15,'adapter proof')
 for obj in [native,ref]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable admitted measurement')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler/input identity')
 for n,h in native['private_used_sha256'].items():require(private[n]==h,'declared private')
 for attempt in [bad,diag,native]:
  for f in attempt['outputs']:require(sha(ROOT/f['path'])==f['sha256'],'artifact');private[f['path']]=f['sha256']
 for n,h in adapter['private_input_sha256'].items():require(private[n]==h,'adapter same data')
 for name in ['selected.txt','checkpoints.bin']:
  require((ROOT/'references-local/trigger-charge02/1-65536'/name).read_bytes().startswith((ROOT/'references-local/trigger-charge01/1-65536'/name).read_bytes()),'unchanged accepted prefix')
 require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and len(native['profiles'])==4 and all(p['exit_code']==0 and p['wall_s']<=300 for p in native['profiles']) and native['wall_s']<=1500 and not native['replays'],'native budget');require(native['minimum_free_bytes']>=native['reserve_bytes']==1024**3 and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and sum(f['bytes'] for f in native['outputs'])<=native['estimated_output_bytes']==32*1024**2,'disk budget')
 counts=dict(independent_candidates=80,independent_nonlinear_rows=18000,native_current_endpoint_vectors=40,native_current_values=400,new_steps=480,restore_phase_replays=40,replayed_steps=720,rejected_corruptions=16,inherited_bit_coordinates=434,source_boundary_bit_coordinates=450)
 for k,v in counts.items():require(ref[k]==v,'coverage '+k)
 require(ref['wall_s']<=300 and ref['loaded_trigger_admitted'] and ref['old_nominal_prefix_bit_equal'] and len(ref['profiles'])==4 and len(ref['same_clock_refinement'])==12 and all(p['gate_ratio']<=1 for p in ref['same_clock_refinement']),'trigger/refinement')
 for p in ref['profiles']:
  require(len(p['phases'])==5 and len(p['root_checks'])==10 and len(p['port_checks'])==10,'phase coverage')
  for n,h in p['input_sha256'].items():require(private[n]==h,'reference artifact')
  for c in p['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent equations')
  for l in [p['total_ledger'],*[v['ledger'] for v in p['phases']]]:
   require(l['not_independent_all_stage_quadrature'],'quadrature scope')
   for c in l['capacitors']:require(Decimal(c['error_c'])<=Decimal(c['gate_c']),'charge balance')
 require(not any(ref[k] for k in ['full_contour_admitted','causal_latch_admitted','adaptive_controller_admitted','new_audio','physical_fidelity','real_time']),'scope')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged release');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/trigger-charge-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,loaded_trigger_admitted=True,old_nominal_prefix_bit_equal=True,new_capacitor_initial_conditions_declared=True,full_contour_admitted=False,causal_latch_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_trigger_charge.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_trigger_charge_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_trigger_charge_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('TRIGGER_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
