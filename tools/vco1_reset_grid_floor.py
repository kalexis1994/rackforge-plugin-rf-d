"""Diagnose the second frozen grid floor without another domain extension."""
import json,os,shutil,subprocess,time
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
import vco1_increment_circuit as oracle
from vco1_newton_reference import ROOT,sha,GATES

def main():
 out=ROOT/'evidence/voice_vco1_reset_grid_floor01.json';work=ROOT/'references-local/vco1-reset-grid-floor01'
 if out.exists() or work.exists():raise ValueError('preserve second floor')
 parent=json.loads((ROOT/'evidence/voice_vco1_reset_grid02.json').read_text());names=set(parent['source_sha256'])|{'tools/vco1_reset_grid_floor.py','docs/VCO1_RESET_SEGUNDO_PISO_PROTOCOLO.md','evidence/voice_vco1_reset_grid02.json'};before={n:sha(ROOT/n) for n in names};compiler=parent['compiler'];rustc=Path(compiler['path']);library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib';raw=np.memmap(ROOT/parent['failed_export']['path'],dtype='<f8').reshape(-1,274);history=raw[-1,6:].tolist();work.mkdir()
 for n in ('fine.rs','linear.rs','vco1_stamp_data.rs'):shutil.copy2(ROOT/'references-local/vco1-reset-grid02'/n,work/n)
 (work/'history.txt').write_text(' '.join(format(v,'.17e') for v in history)+'\n',encoding='utf8',newline='\n')
 code=r'''use rf_d_circuit::{vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton};
#[path="linear.rs"] mod output_conversion;
#[path="fine.rs"] mod fine;
use fine::State;use vco1_stamp::{Controls,N};
fn main() {
 let a:Vec<f64>=include_str!("history.txt").split_whitespace().map(|x|x.parse().unwrap()).collect();let old=State{high:a[..N].try_into().unwrap(),low:a[N..].try_into().unwrap()};let h=fine::MIN_DT_S;let c=Controls::default();let full=fine::solve(c,old,2.*h,vco1_newton::Budget::default()).unwrap();let mid=fine::solve(c,old,h,vco1_newton::Budget::default()).unwrap();let end=fine::solve(c,mid.candidate,h,vco1_newton::Budget::default()).unwrap();
 for (label,s) in [("full",full),("mid",mid),("end",end)] {print!("ROOT,{label},{:.17e},{:.17e}",s.residual_ratio,s.correction_ratio);for v in s.candidate.high.into_iter().chain(s.candidate.low) {print!(",{v:.17e}");}println!();}
}'''
 (work/'runner.rs').write_text(code,encoding='utf8',newline='\n');private={p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()};private[parent['failed_export']['path']]=parent['failed_export']['sha256'];private[library.relative_to(ROOT).as_posix()]=sha(library);private[oracle.op.MODEL]=sha(ROOT/oracle.op.MODEL);r=dict(passed=False,schema='rf-d/finer-grid-second-floor-diagnosis/v1',source_sha256=before,private_input_sha256=private,compiler=compiler,gates=GATES,commands=[],unchanged_replays=[],roots={},new_spice_processes=0,new_audio=False,extra_domain_extension=False,history_elapsed_ticks=int(raw[-1,0]),lab_stack_bytes=8388608)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();start=time.perf_counter();exe=work/'floor.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
 try:
  for cmd in ([str(rustc),'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021',str(work/'runner.rs'),'--extern','rf_d_circuit='+str(library),'-o',str(exe)],[str(exe)]):
   p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60);r['commands'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));save()
   if p.returncode:
    retry=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60);r['unchanged_replays'].append(dict(command=cmd,exit_code=retry.returncode,stdout=retry.stdout,stderr=retry.stderr));save();raise ValueError('second floor process')
  native={}
  for line in p.stdout.splitlines():
   v=line.split(',');native[v[1]]=dict(residual_ratio=float(v[2]),correction_ratio=float(v[3]),high=list(map(float,v[4:138])),low=list(map(float,v[138:])))
  with localcontext() as ctx:
   ctx.prec=100;old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(history[:134],history[134:])];c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)];tick=125e-9/65536;roots={}
   for label,previous,dt in [('full',old,2*tick),('mid',old,tick),('end',None,tick)]:
    root,it,res,g=oracle.solve(roots['mid'] if previous is None else previous,dt,c);roots[label]=root;n=native[label];candidate=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(n['high'],n['low'])];errors=[abs(a-b) for a,b in zip(root,candidate)];row=dict(native=n,independent_decimal=list(map(str,root)),iterations=it,max_kcl_a=float(max(map(abs,res[:98]))),max_constraint_v=float(max(map(abs,res[98:]))),ground_balance_a=float(abs(sum(res[:98])+g)),max_node_error_v=float(max(errors[:98])),max_branch_error_a=float(max(errors[98:])))
    row['passed']=row['max_kcl_a']<=2e-14 and row['max_constraint_v']<=2e-12 and row['ground_balance_a']<=1e-11 and row['max_node_error_v']<=2e-7 and row['max_branch_error_a']<=2e-10 and n['residual_ratio']<=1 and n['correction_ratio']<=1;r['roots'][label]=row;save();print('Second floor',label,row['passed'],row['max_node_error_v'],flush=True)
   ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(roots['full'],roots['end']))];k=max(range(134),key=lambda k:ratios[k]);r['independent_limit']=dict(index=k,error_ratio=float(ratios[k]),full_value_si=float(roots['full'][k]),endpoint_value_si=float(roots['end'][k]),difference_si=float(roots['full'][k]-roots['end'][k]));r['passed']=all(row['passed'] for row in r['roots'].values()) and max(ratios)>1;print('Second LIMIT',r['independent_limit'],flush=True)
 except Exception as exc:r['error']=repr(exc)
 r.update(source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()],wall_s=time.perf_counter()-start);r['passed']=r['passed'] and before==r['source_sha256_after'] and private==r['private_input_sha256_after'];save();print('Second floor diagnosis',r['passed'],r.get('error',''),flush=True)
if __name__=='__main__':main()
