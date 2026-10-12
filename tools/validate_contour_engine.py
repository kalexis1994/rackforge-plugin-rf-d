"""Release the scoped229 adaptive controller and held-contact trajectory."""
import base64,hashlib,json,struct,subprocess,traceback
from decimal import Decimal,localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_contour_engine import ATTR,START,BOUNDARIES,KEY,SHORT,engine,caller
from check_contour_engine import checkpoint
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
from joint_cycles_analysis import require
OUT='evidence/voice_contour_engine_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 previous='evidence/voice_latch_charge_tests01.json';old=read(previous);before=read('evidence/voice_contour_engine_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR and (ROOT/'tools/contour_engine.rs').read_text(encoding='utf8')==engine() and (ROOT/'tools/joint_contour_runner.rs').read_text(encoding='utf8')==caller(),'declared controller binding')
 inp=read('evidence/voice_contour_engine_inputs01.json');native=read('evidence/voice_contour_engine_native01.json');ref=read('evidence/voice_contour_engine_reference01.json');require(inp['passed'] and inp['start_ticks']==START and inp['boundaries_relative_ticks']==BOUNDARIES and inp['keyboard']==KEY and inp['short_states']==SHORT,'frozen recipe')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared source '+n)
 for s in inp['seeds']:
  cp=checkpoint((ROOT/s['path']).read_bytes());origin=struct.unpack('<8sQ6IdQ458d',(ROOT/s['path']).read_bytes())[10:];old_values=struct.unpack('<8sQII2dII458d',(ROOT/s['origin_path']).read_bytes())[8:];require(struct.pack('<458d',*origin)==struct.pack('<458d',*old_values) and cp['ticks']==START and cp['maximum']==s['maximum_half_ticks'] and cp['limit']==20 and cp['next_full']==2*s['maximum_half_ticks'] and cp['phase']==0 and cp['key']==0 and cp['on']==s['final_decay'],'own229 seed');require(sha(ROOT/s['path'])==s['sha256'] and private[s['origin_path']]==s['origin_sha256'],'seed identity');private[s['path']]=s['sha256']
 for obj in [native,ref]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'],'stable measurements')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
 require(native['private_used_sha256']==native['private_used_sha256_after'] and sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'native inputs/compiler')
 for n,h in native['private_used_sha256'].items():require(private[n]==h,'declared private')
 for f in native['outputs']:require(sha(ROOT/f['path'])==f['sha256'],'output');private[f['path']]=f['sha256']
 require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and len(native['profiles'])==4 and all(p['exit_code']==0 and p['wall_s']<=300 for p in native['profiles']) and native['wall_s']<=1500 and not native['replays'],'native budgets');require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['minimum_free_bytes']>=native['reserve_bytes']==1024**3 and sum(f['bytes'] for f in native['outputs'])<=native['estimated_output_bytes']==32*1024**2,'disk budget')
 counts=dict(independent_candidates=144,independent_nonlinear_rows=32976,native_current_endpoint_vectors=48,native_current_values=144,restores=20,rejected_corruptions=16,atomic_rollbacks=8,inherited_bit_coordinates=458,source_boundary_bit_coordinates=458)
 for k,v in counts.items():require(ref[k]==v,'coverage '+k)
 require(ref['wall_s']<=300 and len(ref['profiles'])==4 and len(ref['same_clock_refinement'])==24 and all(p['gate_ratio']<=1 for p in ref['same_clock_refinement']) and ref['adaptive229_window_admitted'],'admission scope')
 for p in ref['profiles']:
  require(len(p['grids'])==12 and len(p['phases'])==3 and len(p['root_checks'])==18 and len(p['port_checks'])==12 and len(p['selected_lte'])==6 and p['restores']==5 and p['corruptions']==4 and p['rollbacks']==2,'profile coverage')
  for c in p['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent equations')
  for c in p['selected_lte']:require(c['independent_ratio']<=1 and c['native_ratio']<=1,'selected LTE')
  for c in p['port_checks']:require(max(c['current_errors_a'])<=1e-9 and max(c['motor_current_errors_a'])<=2e-11,'actual current observations')
  require(p['fine_steps']==2*p['accepted_steps']==2*sum(v['accepted_steps'] for v in p['phases']) and sum(p['half_tick_histogram'].values())==p['accepted_steps']==sum(p['attempt_histogram'].values()),'all accepted steps')
  for l in [p['total_ledger'],*[v['ledger'] for v in p['phases']]]:
   require(l['not_independent_all_stage_quadrature'],'quadrature scope')
   for c in l['rows']:require(Decimal(c['error_c'])<=Decimal(c['gate_c']),'charge balance')
  for n,h in p['input_sha256'].items():require(private[n]==h,'oracle same outputs')
 require(ref['accepted_steps']==sum(p['accepted_steps'] for p in ref['profiles']) and ref['fine_steps']==2*ref['accepted_steps'] and ref['replayed_accepted_steps']==sum(p['replayed_accepted_steps'] for p in ref['profiles']),'total counts');require(not any(ref[k] for k in ['full_contour_trajectory_admitted','all_board2_junction_charge_admitted','new_audio','physical_fidelity','real_time']),'physical/RT scope')
 staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
 for n in staged:
  if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 return dict(schema='rf-d/contour-engine-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,accepted_steps=ref['accepted_steps'],fine_steps=ref['fine_steps'],replayed_accepted_steps=ref['replayed_accepted_steps'],adaptive229_window_admitted=True,full_contour_trajectory_admitted=False,all_board2_junction_charge_admitted=False,new_audio=False,physical_fidelity=False,real_time=False,new_library_compile=False,new_spice_processes=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
 try:
  with localcontext() as ctx:ctx.prec=100;r=audit()
 except Exception:
  r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_contour_engine.py').read_text(encoding='utf8'))
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
  k=1
  while (ROOT/f'evidence/voice_contour_engine_qa_failure{k:02d}.json').exists():k+=1
  (ROOT/f'evidence/voice_contour_engine_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
 (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CONTOUR_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
