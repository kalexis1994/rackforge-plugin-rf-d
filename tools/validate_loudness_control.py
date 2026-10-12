"""Release exact source changes, phase checkpoints, charge ledgers and unchanged gates."""
import base64,hashlib,json,struct,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_loudness_control import ATTR,caller,native_finals,START,SPAN,SOURCES
from check_loudness_control import CODEC
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_loudness_control_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_loudness_tests01.json';old=read(previous);before=read('evidence/voice_loudness_control_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base')
 saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR and (ROOT/'tools/joint_loudness_control_runner.rs').read_bytes()==caller().encode(),'declared lab extension')
 inp=read('evidence/voice_loudness_control_inputs01.json');require(inp['passed'] and inp['sources']==SOURCES and inp['start_ticks']==START and inp['phase_span_ticks']==SPAN,'predeclared recipe')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared input source')
 finals=native_finals()
 for s in inp['seeds']:
  raw=(ROOT/s['path']).read_bytes();require(sha(ROOT/s['path'])==s['sha256'] and raw==CODEC.pack(b'RFLCTL01',START,s['half_ticks'],0,3.2,.7,*finals[s['source_h_s']]),'own native seed exact');private[s['path']]=s['sha256']
 bad=read('evidence/voice_loudness_control_reference01.json');ref=read('evidence/voice_loudness_control_reference02.json');native=read('evidence/voice_loudness_control_native01.json')
 require(not bad['passed'] and bad['source_sha256']==bad['source_sha256_after'] and bad['failure'].splitlines()[-1]==bad['replay'].splitlines()[-1]=="TypeError: 'float' object is not subscriptable",'preserved identical summary failure')
 failed=bad['failed_source_text'];require(hashlib.sha256(failed.encode()).hexdigest()==bad['source_sha256']['tools/check_loudness_control.py'],'failed source exact');current=(ROOT/'tools/check_loudness_control.py').read_text(encoding='utf8');repair=failed.split('def main():')[0].replace('import json,math,re,struct,sys,time,traceback','import argparse,json,math,re,struct,sys,time,traceback').replace('ob[-1][','obs[-1][');require(current.split('def main():')[0]==repair,'only observation container repaired, same auditor/gates')
 require(bad['source_sha256']['evidence/voice_loudness_control_native01.json']==ref['source_sha256']['evidence/voice_loudness_control_native01.json'],'same native data')
 for obj in [native,ref]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable passed campaign')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'private/compiler identity')
 for n,h in native['private_used_sha256'].items():require(private[n]==h,'protected/new declared private input')
 for f in native['outputs']:require(sha(ROOT/f['path'])==f['sha256'],'native artifact');private[f['path']]=f['sha256']
 require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and len(native['profiles'])==2 and all(p['exit_code']==0 and p['wall_s']<=300 for p in native['profiles']) and not native['replays'] and native['wall_s']<=750,'native budget');require(native['minimum_free_bytes']>=native['reserve_bytes']==1024**3 and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and sum(f['bytes'] for f in native['outputs'])<=native['estimated_output_bytes']==16*1024**2,'disk budget')
 counts=dict(independent_candidates=40,independent_nonlinear_rows=8200,native_port_endpoint_vectors=20,native_port_current_values=60,new_steps=240,restore_phase_replays=20,replayed_steps=360,rejected_corruptions=8,source_change_bit_coordinates=410)
 for k,v in counts.items():require(ref[k]==v,'coverage '+k)
 require(ref['wall_s']<=300 and ref['temporal_follower_controls_admitted'] and len(ref['profiles'])==2 and len(ref['same_clock_refinement'])==6 and all(p['gate_ratio']<=1 for p in ref['same_clock_refinement']),'control/refinement admission')
 for p in ref['profiles']:
  require(len(p['phases'])==5 and len(p['root_checks'])==10 and len(p['port_checks'])==10,'complete phase coverage')
  for n,h in p['input_sha256'].items():require(private[n]==h,'audited native input')
  for c in p['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent equations')
  for l in [p['total_ledger'],*[phase['ledger'] for phase in p['phases']]]:
   require(l['source_integrals_are_not_c2_capacitor_charge'] and l['not_independent_all_stage_quadrature'],'ledger scope')
   for c in l['capacitors']:require(__import__('decimal').Decimal(c['error_c'])<=__import__('decimal').Decimal(c['gate_c']),'charge balance')
 require(not any(ref[k] for k in ['full_contour_admitted','adaptive_controller_admitted','new_audio','physical_fidelity','real_time']),'scope')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged release');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/loudness-control-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,temporal_follower_controls_admitted=True,full_contour_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_loudness_control.py').read_text(encoding='utf8'))
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  n=1
  while (ROOT/f'evidence/voice_loudness_control_qa_failure{n:02d}.json').exists():n+=1
  (ROOT/f'evidence/voice_loudness_control_qa_failure{n:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('LOUDNESS_CONTROL_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
