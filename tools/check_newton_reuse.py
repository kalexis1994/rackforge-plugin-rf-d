"""Admit scoped operation reuse by paired timing and byte-identical trajectories."""
import argparse,base64,hashlib,json,re,shutil,statistics,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_newton_reuse import kernel,caller,ATTR,instrument
from joint_cycles_analysis import require
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
 old=read('evidence/voice_contour_cycle_tests01.json');before=read('evidence/newton_reuse_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/'evidence/voice_contour_cycle_tests01.json'),'base QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
 private=dict(old['private_input_sha256'])
 for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR and (ROOT/'tools/joint_newton_reuse_kernel.rs').read_text(encoding='utf8')==kernel() and (ROOT/'tools/joint_newton_reuse_runner.rs').read_text(encoding='utf8')==caller(),'declared numerical-only cache')
 inp=read('evidence/newton_reuse_inputs01.json');bench=read('evidence/newton_reuse_bench_native01.json');native=read('evidence/newton_reuse_native01.json');previous=read('evidence/voice_contour_cycle_native02.json');old_ref=read('evidence/voice_contour_cycle_reference01.json');require(inp['passed'] and bench['passed'] and native['passed'] and previous['passed'] and old_ref['passed'],'measured scopes')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared inputs')
 for obj in [bench,native]:
  require(obj['source_sha256']==obj['source_sha256_after'] and obj['private_used_sha256']==obj['private_used_sha256_after'],'stable measurements')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'measured source')
  require(sha(Path(obj['compiler']['path']))==obj['compiler']['sha256'],'compiler identity')
  for n,h in obj['private_used_sha256'].items():require(sha(ROOT/n)==h,'measured private');private[n]=h
  for f in obj['outputs']:require(sha(ROOT/f['path'])==f['sha256'],'measured output');private[f['path']]=f['sha256']
 for n,h in inp['private_used_sha256'].items():require(sha(ROOT/n)==h,'declared private');private[n]=h
 for name,text in [('reference_profile.rs',(ROOT/'tools/joint_contour_cycle_kernel.rs').read_text(encoding='utf8')),('reuse_profile.rs',kernel())]:
  expected=instrument(text).replace('path="latch_charge_driver.rs"','path="'+(ROOT/'tools/latch_charge_driver.rs').as_posix()+'"').replace('path="contour_closed_driver.rs"','path="'+(ROOT/'tools/contour_closed_driver.rs').as_posix()+'"');require((ROOT/'references-local/newton-reuse-inputs01'/name).read_text(encoding='utf8')==expected,'instrumentation binding')
 require(len(bench['commands'])==2 and all(q['exit_code']==0 for q in bench['commands']) and bench['commands'][0]['wall_s']<=120 and bench['commands'][1]['wall_s']<=300,'benchmark budget')
 lines=bench['commands'][1]['stdout'].splitlines();require(lines[-1]=='PASSED,84,5,stored_and_candidate_bits','benchmark identity scope');cases=[x.split(',') for x in lines if x.startswith('CASE,')];rounds=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('ROUND,')];require(len(cases)==84 and [int(x[1]) for x in cases]==list(range(84)) and len(rounds)==5 and [r[0] for r in rounds]==list(range(5)),'five paired rounds')
 iterations=sum(int(x[5]) for x in cases);trials=sum(int(x[6]) for x in cases);saved_calls=iterations-84;speedup=statistics.median(r[1]/r[2] for r in rounds)
 for r in rounds:require(r[1]>0 and r[2]>0 and r[3]==iterations+trials and r[3]-r[7]==r[4]-r[8]==saved_calls>0 and min(r[5:7]+r[9:11])>0 and r[5]+r[6]<=r[1] and r[9]+r[10]<=r[2],'operation accounting and nested timers')
 require(speedup>1,'paired benchmark utility')
 require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and len(native['profiles'])==4 and all(p['exit_code']==0 and p['wall_s']<=990 for p in native['profiles']) and native['wall_s']<=4000 and not native['replays'],'campaign budget/status');require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['minimum_free_bytes']>=1024**3 and sum(f['bytes'] for f in native['outputs'])<=64*1024**2,'native resource budget')
 profiles=[];files=0;bytes_equal=0
 for p in native['profiles']:
  prior=next(q for q in previous['profiles'] if q['final_decay']==p['final_decay'] and q['maximum_half_ticks']==p['maximum_half_ticks']);a,b=Path(prior['command'][2]),Path(p['command'][2]);original={x.name:x for x in a.iterdir() if x.is_file()};current={x.name:x for x in b.iterdir() if x.is_file()};require(set(original)==set(current),'full artifact set')
  for n,f in original.items():require(f.read_bytes()==current[n].read_bytes(),'complete trajectory bytes '+n);files+=1;bytes_equal+=f.stat().st_size
  def summary(s):
   q=re.search(r'COMPLETED,on=(\d+),max=(\d+),accepted=(\d+),restores=(\d+),replays=(\d+),corruptions=(\d+),rollbacks=(\d+),crossings=(\d+),wall_s=([0-9.]+)',s);require(q is not None,'summary');return tuple(map(int,q.groups()[:-1])),float(q.group(9))
  x,t=summary(p['stderr']);y,pt=summary(prior['stderr']);require(x==y and t<=900,'same controller/replay counts');profiles.append(dict(final_decay=p['final_decay'],maximum_half_ticks=p['maximum_half_ticks'],equal_files=len(original),accepted_steps=x[2],restores=x[3],replayed_accepted_steps=x[4],corruptions=x[5],rollbacks=x[6],resets=x[7],current_wall_s=t,historical_wall_s=pt,historical_ratio_not_paired=pt/t))
 added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'combined new private/reserve budget')
 return dict(paired_rounds=[dict(round=r[0],reference_ns=r[1],reuse_ns=r[2],reference_assemblies=r[3],reference_solves=r[4],reference_assembly_ns=r[5],reference_solve_ns=r[6],reuse_assemblies=r[7],reuse_solves=r[8],reuse_assembly_ns=r[9],reuse_solve_ns=r[10],speedup=r[1]/r[2]) for r in rounds],median_paired_speedup=speedup,selected_pairs=84,selected_bit_coordinates_per_pair=1834,selected_iterations=iterations,selected_trials=trials,saved_calls_per_round=saved_calls,profiles=profiles,full_profile_equal_files=files,full_profile_equal_bytes=bytes_equal,new_private_bytes=size,private_input_sha256=private,accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_steps=2*sum(p['accepted_steps'] for p in profiles),restores=sum(p['restores'] for p in profiles),replayed_accepted_steps=sum(p['replayed_accepted_steps'] for p in profiles),inherited_independent_nonlinear_rows=old_ref['independent_nonlinear_rows'],independent_equations_reexecuted=False,operation_reuse_admitted=True,full_observation_identity=True,new_duration_s=0,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);a=parser.parse_args();names=['tools/check_newton_reuse.py','tools/prepare_newton_reuse.py','evidence/newton_reuse_inputs01.json','evidence/newton_reuse_bench_native01.json','evidence/newton_reuse_native01.json','evidence/voice_contour_cycle_reference01.json','docs/NEWTON_REUSO_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names};t=time.perf_counter();r=dict(passed=False,source_sha256=before)
 try:r.update(audit());r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
  try:audit();r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},wall_s=time.perf_counter()-t);require(before==r['source_sha256_after'],'stable auditor');write(f'evidence/newton_reuse_reference{a.attempt:02d}.json',r);print('REUSE_REFERENCE',r['passed'],r.get('median_paired_speedup'),r.get('failure',''),flush=True)
if __name__=='__main__':main()
