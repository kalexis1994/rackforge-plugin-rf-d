"""Exact rejected interval replay, instrumented Newton and residual merit variant."""
import json,os,shutil,subprocess,time
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
import vco1_radau_trace as trace
import vco1_radau_ports as ports
ROOT=ports.ROOT;sha=ports.sha;TICK=125e-9/65536

def main():
 out=ROOT/'evidence/voice_vco1_radau_newton01.json';work=ROOT/'references-local/vco1-radau-newton01'
 if out.exists() or work.exists():raise ValueError('preserve Newton probe')
 parent=json.loads((ROOT/'evidence/voice_vco1_radau_cycles03.json').read_text());base=json.loads((ROOT/'evidence/voice_vco1_radau_tests01.json').read_text());names=set(base['source_sha256'])|{'tools/vco1_radau_newton_probe.py','tools/vco1_radau_failure_runner.rs','docs/VCO1_RADAU_NEWTON_PROTOCOLO.md','evidence/voice_vco1_radau_cycles03.json'}
 before={n:sha(ROOT/n) for n in names};path=ROOT/'references-local/vco1-radau-cycles03/walk-65536.xor.gz';count=0
 for a in trace.blocks(path):count+=len(a)
 previous=a[-1];assert previous[0]==6381419552 and count==109373
 work.mkdir();checkpoint=work/'checkpoint.txt';checkpoint.write_text(' '.join(format(v,'.17e') for v in previous[6:274])+'\n',encoding='utf8',newline='\n');library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib';compiler=parent['compiler'];env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];original=(ROOT/'tools/vco1_radau_kernel.rs').read_bytes()
 r=dict(schema='rf-d/radau-rejected-newton-tuple-probe/v1',passed=False,source_sha256=before,compiler=compiler,previous_high=previous[6:140].tolist(),previous_low=previous[140:274].tolist(),elapsed_ticks=int(previous[0]),original_rows=count,methods=[],independent=[],production_kernel_changed=False,new_audio=False,new_spice_processes=0)
 private={path.relative_to(ROOT).as_posix():sha(path),checkpoint.relative_to(ROOT).as_posix():sha(checkpoint),library.relative_to(ROOT).as_posix():sha(library)}
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();start=time.perf_counter()
 try:
  for method in ('original','instrumented','residual'):
   folder=work/method;folder.mkdir()
   for n in ('fine.rs','linear.rs','vco1_stamp_data.rs'):shutil.copy2(ROOT/'references-local/vco1-radau-cycles03'/n,folder/n)
   shutil.copy2(ROOT/'tools/vco1_radau_failure_runner.rs',folder/'runner.rs');code=original
   if method=='instrumented':
    code=code.replace(b'let ratio=correction(&d);',b'let ratio=correction(&d);eprintln!("NEWTON,iteration={iteration},norm={norm:.17e},correction={ratio:.17e}");')
    code=code.replace(b'let next=correction(&dd);',b'let next=correction(&dd);eprintln!("TRIAL,power={power},norm={:.17e},correction={next:.17e}",merit(&t.residual));')
   if method=='residual':code=code.replace(b'next<ratio*(1.-1e-4*alpha)',b'merit(&t.residual)<norm*(1.-1e-4*alpha)')
   (folder/'radau.rs').write_bytes(code);exe=folder/'probe.exe';commands=[]
   def execute(cmd,tag):
    result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=60);(folder/(tag+'.stdout')).write_bytes(result.stdout);(folder/(tag+'.stderr')).write_bytes(result.stderr)
    return dict(command=cmd,exit_code=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace'))
   build=execute([compiler['path'],'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021',str(folder/'runner.rs'),'--extern','rf_d_circuit='+str(library),'-o',str(exe)],'compile');commands.append(build)
   if build['exit_code']:raise ValueError('probe build')
   run=execute([str(exe),str(checkpoint)],'probe');commands.append(run);replay=execute(run['command'],'replay');commands.append(replay)
   if run['exit_code'] or replay['exit_code'] or run['stdout']!=replay['stdout'] or run['stderr']!=replay['stderr']:raise ValueError('local deterministic replay')
   roots={};rejects=[]
   for line in run['stdout'].splitlines():
    w=line.split(',')
    if w[0]=='REJECT':rejects.append(dict(label=w[1],error=w[2]))
    elif w[0]=='ROOT':roots.setdefault(w[1],{})[w[2]]=dict(high=list(map(float,w[5:139])),low=list(map(float,w[139:])),residual_ratio=float(w[3]),correction_ratio=float(w[4]))
   r['methods'].append(dict(method=method,commands=commands,roots=roots,rejections=rejects,kernel_sha256=sha(folder/'radau.rs')));save();print('Radau tuple',method,'rejections',rejects,flush=True)
  inv=ports.ref.circuit.inventory(ports.ref.circuit.scenario(ports.C))
  with localcontext() as ctx:
   ctx.prec=100;old=ports.packed(r['previous_high'],r['previous_low'])
   for ticks in (8,16,32):
    h=ticks*TICK/2;mid=None;values={};item=dict(full_ticks=ticks,steps={},native_comparisons=[]);r['independent'].append(item)
    for label,dt in (('full',2*h),('mid',h),('end',h)):
     history=mid['endpoint'] if label=='end' else old;sol=ports.ref.solve(history,dt,ports.C);values[label]=sol['endpoint'];mid=sol if label=='mid' else mid;roots={p:dict(independent_decimal=list(map(str,sol[p]))) for p in ('stage','endpoint')};item['steps'][label]=dict(dt_s=dt,roots=roots,previous_decimal=list(map(str,history)),residual_ratio=sol['residual_ratio'],correction_ratio=sol['correction_ratio'])
     for method in r['methods']:
      native=method['roots'].get(f'{ticks}/{label}')
      if native:
       pair={p:dict(roots[p],native=native[p]) for p in roots};checked=ports.check(pair,history,dt,inv);item['native_comparisons'].append(dict(method=method['method'],label=label,ports=checked))
     save()
    error=max(abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(values['full'],values['end'])));item['independent_error_ratio']=str(error);item['local_error_admitted']=error<=1;save();print('Radau Decimal tuple',ticks,'error',float(error),flush=True)
  r['passed']=len(r['methods'])==3 and len(r['independent'])==3
 except Exception as exc:r['error']=repr(exc)
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_input_sha256=private,private_input_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.rglob('*') if p.is_file()],wall_s=time.perf_counter()-start)
 r['passed']=r['passed'] and before==r['source_sha256_after'] and private==r['private_input_sha256_after'];save();print('Radau Newton probe',r['passed'],r.get('error',''),flush=True)

if __name__=='__main__':main()
