"""Disambiguate the frozen SDIRK floor using exact private kernel copies."""
import json,os,shutil,subprocess,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_sdirk_reference as oracle
from vco1_newton_reference import ROOT,sha

def main():
 out=ROOT/'evidence/voice_vco1_sdirk_floor4_01.json';work=ROOT/'references-local/vco1-sdirk-floor4-01'
 if out.exists() or work.exists():raise ValueError('preserve SDIRK floor')
 parent=json.loads((ROOT/'evidence/voice_vco1_sdirk_probe4_01.json').read_text());before={n:sha(ROOT/n) for n in set(parent['source_sha256'])|{'tools/vco1_sdirk_floor4.py','docs/VCO1_SDIRK_PISO4_PROTOCOLO.md','evidence/voice_vco1_sdirk_probe4_01.json'}};raw=np.memmap(ROOT/parent['failed_export']['path'],dtype='<f8').reshape(-1,542);values=raw[-1,6:274].tolist();compiler=parent['compiler'];rustc=Path(compiler['path']);library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib';work.mkdir()
 for n in ('fine.rs','linear.rs','vco1_stamp_data.rs','sdirk.rs'):shutil.copy2(ROOT/'references-local/vco1-sdirk-probe4-01'/n,work/n)
 (work/'history.txt').write_text(' '.join(format(v,'.17e') for v in values),encoding='utf8');source=(ROOT/'tools/vco1_sdirk_runner.rs').read_text();report=source[source.index('fn report'):source.index('fn emit')];code=source[:source.index('const TICK')]+report+r'''
fn main()->Result<(),Box<dyn std::error::Error>> {
 let a:Vec<f64>=include_str!("history.txt").split_whitespace().map(|s|s.parse().unwrap()).collect();let old=State{high:a[..N].try_into().unwrap(),low:a[N..].try_into().unwrap()};let c=Controls::default();let h=4.*125e-9/65536.;
 let full=sdirk::step(c,old,2.*h).map_err(|e|format!("full:{e:?}"))?;report(2,-1,"full",&full);
 let mid=sdirk::step(c,old,h).map_err(|e|format!("mid:{e:?}"))?;report(2,-1,"mid",&mid);
 let end=sdirk::step(c,mid.endpoint.candidate,h).map_err(|e|format!("end:{e:?}"))?;report(2,-1,"end",&end);Ok(())
}'''
 (work/'runner.rs').write_text(code,encoding='utf8',newline='\n');private={p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()};private[parent['failed_export']['path']]=parent['failed_export']['sha256'];private[library.relative_to(ROOT).as_posix()]=sha(library);private[oracle.circuit.op.MODEL]=sha(ROOT/oracle.circuit.op.MODEL);r=dict(passed=False,schema='rf-d/SDIRK-floor-disambiguation/v1',source_sha256=before,private_input_sha256=private,compiler=compiler,commands=[],unchanged_replays=[],steps={},previous_high=values[:134],previous_low=values[134:],new_spice_processes=0,new_audio=False,lab_stack_bytes=8388608)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();start=time.perf_counter();exe=work/'floor.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
 try:
  for cmd in ([str(rustc),'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021',str(work/'runner.rs'),'--extern','rf_d_circuit='+str(library),'-o',str(exe)],[str(exe)]):
   p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60);r['commands'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));save()
   if p.returncode:
    retry=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60);r['unchanged_replays'].append(dict(command=cmd,exit_code=retry.returncode,stdout=retry.stdout,stderr=retry.stderr));save();raise ValueError('SDIRK floor process')
  native={}
  for line in p.stdout.splitlines():
   v=line.split(',')
   if v[0]=='ROOT':native[(v[3],v[4])]=dict(residual_ratio=float(v[5]),correction_ratio=float(v[6]),high=list(map(float,v[9:143])),low=list(map(float,v[143:])))
  with localcontext() as ctx:
   ctx.prec=100;old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(values[:134],values[134:])];c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)];h=4*125e-9/65536;roots={}
   for label,previous,dt in [('full',old,2*h),('mid',old,h),('end',None,h)]:
    pair=oracle.step(roots['mid']['endpoint'] if previous is None else previous,dt,c);roots[label]=pair;rows={}
    for part in ('stage','endpoint'):
     n=native[(label,part)];candidate=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(n['high'],n['low'])];error=[abs(a-b) for a,b in zip(pair[part],candidate)];res=pair[part+'_residual'];g=pair[part+'_ground'];row=dict(native=n,independent_decimal=list(map(str,pair[part])),max_node_error_v=float(max(error[:98])),max_branch_error_a=float(max(error[98:])),max_kcl_a=float(max(map(abs,res[:98]))),max_constraint_v=float(max(map(abs,res[98:]))),ground_balance_a=float(abs(sum(res[:98])+g)));row['passed']=row['max_node_error_v']<=2e-7 and row['max_branch_error_a']<=2e-10 and row['max_kcl_a']<=2e-14 and row['max_constraint_v']<=2e-12 and row['ground_balance_a']<=1e-11 and n['residual_ratio']<=1 and n['correction_ratio']<=1;rows[part]=row
    r['steps'][label]=rows;save()
   ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(roots['full']['endpoint'],roots['end']['endpoint']))];k=max(range(134),key=lambda k:ratios[k]);r['independent_limit']=dict(index=k,error_ratio=float(ratios[k]),difference_si=float(roots['full']['endpoint'][k]-roots['end']['endpoint'][k]));r['passed']=all(row['passed'] for rows in r['steps'].values() for row in rows.values()) and max(ratios)>1;r['failure_cause_confirmed']='local error' if r['passed'] else 'unadmitted';print('SDIRK floor',r['passed'],r['independent_limit'],flush=True)
 except Exception as exc:r['error']=repr(exc)
 r.update(source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()],wall_s=time.perf_counter()-start);r['passed']=r['passed'] and before==r['source_sha256_after'] and private==r['private_input_sha256_after'];save()
if __name__=='__main__':main()
