"""Coupled Radau charge roots and prerequisite-gated conditional continuation."""
import argparse,json,os,shutil,subprocess,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_radau_reference as oracle
from vco1_newton_reference import ROOT,sha,GATES
NEW=['tools/vco1_radau_kernel.rs','tools/vco1_radau_runner.rs','tools/vco1_radau_reference.py','tools/vco1_radau_probe.py','docs/VCO1_RADAU_PROTOCOLO.md']
COLS=542;TICK=125e-9/65536

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 out=ROOT/f'evidence/voice_vco1_radau_probe{a:02d}.json';work=ROOT/f'references-local/vco1-radau-probe{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve Radau attempt')
 q=json.loads((ROOT/'evidence/voice_vco1_741_condensation_tests01.json').read_text());before={n:sha(ROOT/n) for n in set(q['source_sha256'])|set(NEW)|{'evidence/voice_vco1_741_condensation_tests01.json'}};compiler=json.loads((ROOT/'evidence/voice_vco1_increment_native02.json').read_text())['compiler'];rustc=Path(compiler['path']);library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib';p0=json.loads((ROOT/'evidence/voice_vco1_sdirk_floor01.json').read_text());p1=json.loads((ROOT/'evidence/voice_vco1_sdirk_floor4_01.json').read_text());history0=p0['previous_high']+p0['previous_low'];history1=p1['previous_high']+p1['previous_low'];c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]
 r=dict(passed=False,schema='rf-d/charge-radau-local-probe/v1',source_sha256=before,compiler=compiler,gates=GATES,inverse_tableau=[[str(v) for v in row] for row in oracle.B],walk_dispatched=False,commands=[],unchanged_replays=[],cases=[],actual_intervals=[],native_roots_admitted=False,conditional_continuation_admitted=False,production_kernel_changed=False,new_spice_processes=0,new_audio=False,resource_passed=shutil.disk_usage(ROOT).free>2*1024**3+128*1024**2,lab_stack_bytes=8388608)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save()
 if not r['resource_passed']:return
 work.mkdir()
 for n in ('fine.rs','linear.rs','vco1_stamp_data.rs'):shutil.copy2(ROOT/'references-local/vco1-reset-grid02'/n,work/n)
 shutil.copy2(ROOT/'tools/vco1_radau_kernel.rs',work/'radau.rs');shutil.copy2(ROOT/'tools/vco1_radau_runner.rs',work/'runner.rs')
 for k,h in enumerate((history0,history1)):(work/f'history{k}.txt').write_text(' '.join(format(v,'.17e') for v in h)+'\n',encoding='utf8',newline='\n')
 private={p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()};private[library.relative_to(ROOT).as_posix()]=sha(library);private[oracle.circuit.op.MODEL]=sha(ROOT/oracle.circuit.op.MODEL);r['private_input_sha256']=private;save();env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];exe=work/'radau.exe';start=time.perf_counter()
 def execute(cmd,tag):
  with open(work/(tag+'.stdout'),'w',encoding='utf8') as so,open(work/(tag+'.stderr'),'w',encoding='utf8') as se:
   p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=so,stderr=se);began=time.monotonic();reason=None
   while p.poll() is None:
    if shutil.disk_usage(ROOT).free<2*1024**3:reason='disk reserve'
    if time.monotonic()-began>180:reason='process budget'
    if reason:p.terminate();p.wait();break
    time.sleep(.25)
  return dict(command=cmd,exit_code=p.returncode,stdout=(work/(tag+'.stdout')).read_text(),stderr=(work/(tag+'.stderr')).read_text()+('RESOURCE_REJECT:'+reason if reason else ''))
 def command(cmd,tag,export=None):
  p=execute(cmd,tag);r['commands'].append(p);save()
  if p['exit_code']:
   if export and export.exists():
    original=export.with_suffix('.failed-original.bin');shutil.copy2(export,original);r['failed_export']=dict(path=original.relative_to(ROOT).as_posix(),sha256=sha(original),bytes=original.stat().st_size)
   save();rp=execute(cmd,tag+'-replay');rp.update(source_sha256={n:sha(ROOT/n) for n in before},export_sha256=sha(export) if export and export.exists() else None);r['unchanged_replays'].append(rp);save()
  return p
 def packed(h,l):return [Decimal.from_float(v)+Decimal.from_float(w) for v,w in zip(h,l)]
 def compare(reference,native):
  n=packed(native['high'],native['low']);error=[abs(a-b) for a,b in zip(reference,n)];return dict(max_node_error_v=float(max(error[:98])),max_branch_error_a=float(max(error[98:])),native=native,independent_decimal=list(map(str,reference)))
 def rows(p,n):
  result={}
  for part in ('stage','endpoint'):
   row=compare(p[part],n[part]);i=0 if part=='stage' else 1;res=p['residual'][i*134:(i+1)*134];ground=p['ground'][i];row.update(max_kcl_a=float(max(map(abs,res[:98]))),max_constraint_v=float(max(map(abs,res[98:]))),ground_balance_a=float(abs(sum(res[:98])+ground)));row['passed']=row['max_node_error_v']<=2e-7 and row['max_branch_error_a']<=2e-10 and row['max_kcl_a']<=2e-14 and row['max_constraint_v']<=2e-12 and row['ground_balance_a']<=1e-11 and n[part]['residual_ratio']<=1 and n[part]['correction_ratio']<=1;result[part]=row
  return result
 try:
  p=command([str(rustc),'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021',str(work/'runner.rs'),'--extern','rf_d_circuit='+str(library),'-o',str(exe)],'compile')
  if p['exit_code']:raise ValueError('compile rejected')
  p=command([str(exe),'roots'],'roots')
  if p['exit_code']:raise ValueError('native roots rejected')
  native={};dynamic={}
  for line in p['stdout'].splitlines():
   v=line.split(',');key=(int(v[1]),int(v[2]),v[3])
   if v[0]=='ROOT':native[(*key,v[4])]=dict(residual_ratio=float(v[5]),correction_ratio=float(v[6]),iterations=int(v[7]),trials=int(v[8]),high=list(map(float,v[9:143])),low=list(map(float,v[143:])))
   else:dynamic[key]=dict(ground=float(v[4]),values=list(map(float,v[5:])))
  with localcontext() as ctx:
   ctx.prec=100
   for scene,values in enumerate((history0,history1)):
    old=packed(values[:134],values[134:])
    for power in range(4):
     h=4*TICK*2**power;roots={};case=dict(scene=scene,power=power,half_dt_s=h,previous_high=values[:134],previous_low=values[134:],steps={});r['cases'].append(case);save()
     for label,previous,dt in [('full',old,2*h),('mid',old,h),('end',None,h)]:
      pair=oracle.solve(roots['mid']['endpoint'] if previous is None else previous,dt,c);roots[label]=pair;n={part:native[(scene,power,label,part)] for part in ('stage','endpoint')};case['steps'][label]=dict(roots=rows(pair,n));save()
     ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(roots['full']['endpoint'],roots['end']['endpoint']))];k=max(range(134),key=lambda k:ratios[k]);case.update(error_ratio=float(ratios[k]),limiting_index=k,local_error_admitted=ratios[k]<=1,roots_passed=all(row['passed'] for s in case['steps'].values() for row in s['roots'].values()));save();print('Radau scene',scene,power,'roots',case['roots_passed'],'local ratio',float(ratios[k]),flush=True)
  r['native_roots_admitted']=len(r['cases'])==8 and all(case['roots_passed'] for case in r['cases']);save()
  if not r['native_roots_admitted']:raise ValueError('48-stage-root contrast rejected')
  if not all(case['local_error_admitted'] for case in r['cases'] if case['power']==0):raise ValueError('minimum local errors rejected; continuation not dispatched')
  r['walk_dispatched']=True
  export=work/'walk.bin';p=command([str(exe),'walk',str(export)],'walk',export)
  trace=np.memmap(export,dtype='<f8').reshape(-1,COLS);r['coverage']=dict(rows=len(trace),accepted_steps=len(trace)-1,elapsed_s=float(trace[-1,0]*TICK),minimum_actual_dt_s=float(trace[1:,1].min()*TICK),maximum_actual_dt_s=float(trace[1:,1].max()*TICK),maximum_error_ratio=float(trace[:,4].max()),max_attempts=int(trace[:,5].max()),path=export.relative_to(ROOT).as_posix(),sha256=sha(export));save()
  if not np.isfinite(trace).all() or not np.array_equal(np.diff(trace[:,0]),trace[1:,1]) or np.max(trace[:,2:5])>1 or np.min(trace[1:,1])<4 or np.max(trace[1:,1])>262144 or not np.array_equal(trace[:,6:140]+trace[:,140:274],trace[:,6:140]) or not np.array_equal(trace[:,274:408]+trace[:,408:],trace[:,274:408]):raise ValueError('trace memory/clock/gates')
  changes=np.max(np.abs(np.diff(trace[:,6:104],axis=0)),axis=1);indices=sorted(set([1,len(trace)-1,*list(np.argsort(changes)[-2:]+1)]))
  with localcontext() as ctx:
   ctx.prec=100
   for k in indices:
    previous=trace[k-1];now=trace[k];old=packed(previous[6:140],previous[140:274]);dt=float(now[1]*TICK);pair=oracle.solve(old,dt,c);n={part:dict(high=now[a:a+134].tolist(),low=now[a+134:a+268].tolist(),residual_ratio=float(now[2]),correction_ratio=float(now[3])) for part,a in [('stage',274),('endpoint',6)]};item=dict(row_index=int(k),dt_s=dt,elapsed_ticks=int(now[0]),previous_high=previous[6:140].tolist(),previous_low=previous[140:274].tolist(),roots=rows(pair,n));r['actual_intervals'].append(item);save();print('Radau actual interval',k,'passed',all(row['passed'] for row in item['roots'].values()),flush=True)
  r['conditional_continuation_admitted']=p['exit_code']==0 and abs(r['coverage']['elapsed_s']-1e-6)<1e-17 and all(row['passed'] for item in r['actual_intervals'] for row in item['roots'].values());r['passed']=r['native_roots_admitted'] and r['conditional_continuation_admitted']
 except Exception as exc:
  r['error']=repr(exc);save()
 r.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()],native_full_period_admitted=False,physical_fidelity=False,real_time=False)
 r['passed']=r['passed'] and before==r['source_sha256_after'] and private==r['private_input_sha256_after'];save();print('Radau probe',r['passed'],r.get('error',''),flush=True)
if __name__=='__main__':main()
