"""Private finer-grid reset probe and independent Decimal100 roots."""
import argparse,hashlib,json,os,shutil,subprocess,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_increment_circuit as oracle
from vco1_newton_reference import ROOT,sha,GATES

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 if not 1<=a<=99:raise ValueError('attempt')
 out=ROOT/f'evidence/voice_vco1_reset_grid{a:02d}.json';work=ROOT/f'references-local/vco1-reset-grid{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve grid attempt')
 q=json.loads((ROOT/'evidence/voice_vco1_increment_tests01.json').read_text());names=set(q['source_sha256'])|{'tools/vco1_reset_grid.py','tools/vco1_reset_grid.rs','docs/VCO1_RESET_GRILLA_PROTOCOLO.md','docs/VCO1_RESET_GRILLA_ADAPTADOR.md','evidence/voice_vco1_increment_tests01.json'};before={n:sha(ROOT/n) for n in names};compiler=json.loads((ROOT/'evidence/voice_vco1_increment_native02.json').read_text())['compiler'];rustc=Path(compiler['path']);library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib'
 fine=(ROOT/'crates/rf-d-circuit/src/vco1_increment.rs').read_text().replace('pub const MIN_DT_S:f64=125e-9/4096.;','pub const MIN_DT_S:f64=125e-9/65536.;');adaptive=(ROOT/'crates/rf-d-circuit/src/vco1_increment_adaptive.rs').read_text().replace('vco1_increment','fine').replace('maximum_half_ticks>32768','maximum_half_ticks>524288').replace('for attempts in 1..=16','for attempts in 1..=20')
 r=dict(passed=False,schema='rf-d/private-finer-grid-reset/v1',source_sha256=before,compiler=compiler,gates=GATES,copy_changes=['kernel MIN_DT:125ns/4096 to 125ns/65536','controller module binding to private kernel','maximum_half_ticks:32768 to 524288','attempt_limit:16 to 20'],physical_parameters_changed=False,production_kernel_changed=False,main_stack_bytes=8388608,commands=[],unchanged_replays=[],trios={},intervals=[],new_spice_processes=0,new_audio=False,resource_passed=shutil.disk_usage(ROOT).free>2*1024**3+64*1024**2,estimates_are_not_bounds=True)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save()
 if not r['resource_passed']:return
 work.mkdir();source=(ROOT/'crates/rf-d-circuit/src/output_conversion.rs').read_text(encoding='utf8');maxabs=source[source.index('pub(crate) fn max_abs'):source.index('\n}',source.index('pub(crate) fn max_abs'))+2];linear=source[source.index('pub(crate) fn solve_linear_sparse'):source.index('/// Scaled-pivot elimination for several')];(work/'linear.rs').write_text('use rf_d_circuit::StepError;\n'+maxabs+'\n'+linear,encoding='utf8',newline='\n');(work/'fine.rs').write_text(fine,encoding='utf8',newline='\n');(work/'adaptive.rs').write_text(adaptive,encoding='utf8',newline='\n');shutil.copy2(ROOT/'crates/rf-d-circuit/src/vco1_stamp_data.rs',work/'vco1_stamp_data.rs');shutil.copy2(ROOT/'tools/vco1_reset_grid.rs',work/'runner.rs');shutil.copy2(ROOT/'evidence/voice_vco1_increment_floor_history01.txt',work/'history.txt')
 private={p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()};private[library.relative_to(ROOT).as_posix()]=sha(library);private[oracle.op.MODEL]=sha(ROOT/oracle.op.MODEL);r['private_input_sha256']=private;save();env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];exe=work/'grid.exe';export=work/'reset.bin';start=time.perf_counter()
 def execute(cmd):
  with open(work/'stdout.log','w',encoding='utf8') as so,open(work/'stderr.log','w',encoding='utf8') as se:
   p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=so,stderr=se);began=time.monotonic();reason=None
   while p.poll() is None:
    if shutil.disk_usage(ROOT).free<2*1024**3:reason='disk reserve crossed'
    if time.monotonic()-began>180:reason='process budget'
    if reason:p.terminate();p.wait();break
    time.sleep(.25)
  return dict(command=cmd,exit_code=p.returncode,stdout=(work/'stdout.log').read_text(),stderr=(work/'stderr.log').read_text()+('RESOURCE_REJECT:'+reason if reason else ''))
 try:
  p=execute([str(rustc),'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021',str(work/'runner.rs'),'--extern','rf_d_circuit='+str(library),'-o',str(exe)]);r['commands'].append(p);save()
  if p['exit_code']:
   retry=execute(p['command']);retry['source_sha256']={n:sha(ROOT/n) for n in before};r['unchanged_replays'].append(retry);save();raise ValueError('private probe compile')
  cmd=[str(exe),str(export)];p=execute(cmd);r['commands'].append(p);save()
  if p['exit_code']:
   original=work/'reset.failed-original.bin'
   if export.exists():shutil.copy2(export,original);r['failed_export']=dict(path=original.relative_to(ROOT).as_posix(),sha256=sha(original),bytes=original.stat().st_size)
   save();retry=execute(cmd);retry['export_sha256']=sha(export) if export.exists() else None;retry['source_sha256']={n:sha(ROOT/n) for n in before};r['unchanged_replays'].append(retry);save()
  native={}
  for line in p['stdout'].splitlines():
   if line.startswith('ROOT,'):
    v=line.split(',');native[(int(v[1]),v[2])]=dict(residual_ratio=float(v[3]),correction_ratio=float(v[4]),iterations=int(v[5]),trials=int(v[6]),high=list(map(float,v[7:141])),low=list(map(float,v[141:])))
   if line.startswith('COMPLETE,'):r['completion']=line
  values=list(map(float,(work/'history.txt').read_text().split()));c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)];tick=125e-9/65536
  def compare(old,dt,n):
   root,it,res,g=oracle.solve(old,dt,c);candidate=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(n['high'],n['low'])];errors=[abs(a-b) for a,b in zip(root,candidate)];row=dict(native=n,independent_decimal=list(map(str,root)),iterations=it,max_kcl_a=float(max(map(abs,res[:98]))),max_constraint_v=float(max(map(abs,res[98:]))),ground_balance_a=float(abs(sum(res[:98])+g)),max_node_error_v=float(max(errors[:98])),max_branch_error_a=float(max(errors[98:])))
   row['passed']=row['max_kcl_a']<=2e-14 and row['max_constraint_v']<=2e-12 and row['ground_balance_a']<=1e-11 and row['max_node_error_v']<=2e-7 and row['max_branch_error_a']<=2e-10 and n['residual_ratio']<=1 and n['correction_ratio']<=1
   return root,row
  with localcontext() as ctx:
   ctx.prec=100;old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(values[:134],values[134:])]
   for power in range(5):
    h=125e-9/4096/(2**power);roots={};rows={}
    for label,history,dt in [('full',old,2*h),('mid',old,h),('end',None,h)]:
     root,row=compare(roots['mid'] if history is None else history,dt,native[(power,label)]);roots[label]=root;rows[label]=row
    ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(roots['full'],roots['end']))];k=max(range(134),key=lambda k:ratios[k]);r['trios'][str(power)]=dict(half_dt_s=h,roots=rows,index=k,error_ratio=float(ratios[k]),local_error_admitted=ratios[k]<=1);save();print('Finer-grid trio',power,'ratio',float(ratios[k]),'index',k,flush=True)
   if not export.exists():raise ValueError('missing reset trace')
   raw=np.memmap(export,dtype='<f8').reshape(-1,274);steps=raw[1:,1];r['coverage']=dict(rows=len(raw),elapsed_s=float(raw[-1,0]*tick),minimum_actual_dt_s=float(steps.min()*tick),maximum_actual_dt_s=float(steps.max()*tick),maximum_error_ratio=float(raw[:,4].max()),max_attempts=int(raw[:,5].max()),first_history_identical=raw[0,6:].tolist()==values,complete_50us=p['exit_code']==0 and abs(raw[-1,0]*tick-50e-6)<1e-17)
   if not np.isfinite(raw).all() or not np.array_equal(raw[:,6:140]+raw[:,140:],raw[:,6:140]) or np.max(raw[:,2:5])>1 or not np.array_equal(np.diff(raw[:,0]),steps) or np.min(steps)<1 or np.max(steps)>262144 or not r['coverage']['first_history_identical']:raise ValueError('reset trace clock/memory/gates')
   changes=np.max(np.abs(np.diff(raw[:,6:104],axis=0)),axis=1);indices=sorted(set([1,len(raw)-1,*list(np.argsort(changes)[-2:]+1)]))
   for k in indices:
    previous=raw[k-1];now=raw[k];history=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(previous[6:140],previous[140:])];n=dict(high=now[6:140].tolist(),low=now[140:].tolist(),residual_ratio=float(now[2]),correction_ratio=float(now[3]));root,row=compare(history,float(now[1]*tick),n);row.update(row_index=int(k),elapsed_ticks=int(now[0]),interval_ticks=int(now[1]),conditional_previous_high=previous[6:140].tolist(),conditional_previous_low=previous[140:].tolist());r['intervals'].append(row);save();print('Reset actual interval',k,row['passed'],row['max_node_error_v'],flush=True)
  r['passed']=r['coverage']['complete_50us'] and all(row['passed'] for trio in r['trios'].values() for row in trio['roots'].values()) and all(row['passed'] for row in r['intervals']) and not r['trios']['0']['local_error_admitted'] and all(r['trios'][str(k)]['local_error_admitted'] for k in range(1,5))
 except Exception as exc:
  r['error']=repr(exc);save()
  if 'history' in locals() and history is not None:
   try:
    with localcontext() as ctx:ctx.prec=100;oracle.solve(history,dt,c)
   except Exception as e:r['unchanged_replays'].append(dict(stage='Decimal root',error=repr(e)))
 r.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()],physical_fidelity=False,real_time=False,native_full_period_admitted=False)
 r['passed']=r['passed'] and before==r['source_sha256_after'] and private==r['private_input_sha256_after'];save();print('Private reset grid',r['passed'],r.get('error',''),flush=True)
if __name__=='__main__':main()
