"""Independent full/half reset roots; preserve all candidate states and gates."""
import json,os,subprocess,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_increment_circuit as oracle
from vco1_newton_reference import ROOT,sha,GATES
from vco1_increment_reference import SOURCES

def main():
 out=ROOT/'evidence/voice_vco1_increment_floor01.json';work=ROOT/'references-local/vco1-increment-floor01'
 if out.exists() or work.exists():raise ValueError('preserve floor diagnosis')
 parent=json.loads((ROOT/'evidence/voice_vco1_increment_cycles02.json').read_text());names=set(SOURCES)|set(parent['source_sha256'])|{'tools/vco1_increment_floor.py','tools/vco1_increment_floor.rs','evidence/voice_vco1_increment_floor_history01.txt','docs/VCO1_INCREMENTOS_RESET_PROTOCOLO.md'};before={n:sha(ROOT/n) for n in names}
 library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib';private={parent['failed_export']['path']:parent['failed_export']['sha256'],library.relative_to(ROOT).as_posix():sha(library),oracle.op.MODEL:sha(ROOT/oracle.op.MODEL)};compiler=parent['compiler'];rustc=Path(compiler['path']);work.mkdir();exe=work/'floor.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
 r=dict(passed=False,schema='rf-d/increment-reset-local-diagnosis/v1',source_sha256=before,private_input_sha256=private,compiler=compiler,gates=GATES,commands=[],unchanged_replays=[],roots={},new_spice_processes=0,new_audio=False,main_stack_reserve_bytes=8388608,history_time_s=79768392*125e-9/4096)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();start=time.perf_counter()
 try:
  for cmd in ([str(rustc),'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021','tools/vco1_increment_floor.rs','--extern','rf_d_circuit='+str(library),'-o',str(exe)],[str(exe)]):
   p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60);r['commands'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));save()
   if p.returncode:raise ValueError('native floor process')
  native={}
  for line in p.stdout.splitlines():
   if line.startswith('ROOT,'):
    v=line.split(',');native[v[1]]=dict(residual_ratio=float(v[2]),correction_ratio=float(v[3]),iterations=int(v[4]),trials=int(v[5]),high=list(map(float,v[6:140])),low=list(map(float,v[140:])))
   else:r['native_limit']=line
  values=list(map(float,(ROOT/'evidence/voice_vco1_increment_floor_history01.txt').read_text().split()));c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)];tick=125e-9/4096
  with localcontext() as ctx:
   ctx.prec=100;old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(values[:134],values[134:])];ind={}
   for label,history,dt in [('full',old,2*tick),('mid',old,tick),('end',None,tick)]:
    if history is None:history=ind['mid']
    root,it,res,g=oracle.solve(history,dt,c);ind[label]=root;n=native[label];candidate=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(n['high'],n['low'])];error=[abs(u-v) for u,v in zip(root,candidate)]
    row=dict(native=n,independent_decimal=list(map(str,root)),independent_iterations=it,max_kcl_a=float(max(map(abs,res[:98]))),max_constraint_v=float(max(map(abs,res[98:]))),ground_balance_a=float(abs(sum(res[:98])+g)),max_node_error_v=float(max(error[:98])),max_branch_error_a=float(max(error[98:])))
    row['passed']=row['max_kcl_a']<=2e-14 and row['max_constraint_v']<=2e-12 and row['ground_balance_a']<=1e-11 and row['max_node_error_v']<=2e-7 and row['max_branch_error_a']<=2e-10 and n['residual_ratio']<=1 and n['correction_ratio']<=1;r['roots'][label]=row;save();print('Independent floor',label,row['passed'],row['max_node_error_v'],row['max_branch_error_a'],flush=True)
   differences=[u-v for u,v in zip(ind['full'],ind['end'])];ratios=[abs(v)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,v in enumerate(differences)];k=max(range(134),key=lambda k:ratios[k]);r['independent_limit']=dict(index=k,error_ratio=float(ratios[k]),difference_si=float(differences[k]),change_from_previous_si=float(ind['end'][k]-old[k]),full_decimal=str(ind['full'][k]),endpoint_decimal=str(ind['end'][k]));r['independent_local_error_admitted']=max(ratios)<=1
  r['passed']=all(row['passed'] for row in r['roots'].values()) and not r['independent_local_error_admitted'];print('LIMIT',r['independent_limit'],flush=True)
 except Exception as exc:
  r['error']=repr(exc);save()
  # Repeat independent equations without modifying any inputs.
  if 'history' in locals():
   try:
    with localcontext() as ctx:ctx.prec=100;oracle.solve(history,dt,c)
   except Exception as e:r['unchanged_replays'].append(dict(error=repr(e),source_sha256={n:sha(ROOT/n) for n in before}))
 r.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]);r['passed']=r['passed'] and before==r['source_sha256_after'] and private==r['private_input_sha256_after'];save();print('Floor diagnosis',r['passed'],r.get('error',''),flush=True)
if __name__=='__main__':main()
