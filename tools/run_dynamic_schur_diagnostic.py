"""Same J/b full-vs-Schur corrections and original LM741 port/memory observations."""
import json,os,subprocess,time,traceback,base64
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from prepare_dynamic_schur import maps
PROXY='''use super::{StepError,solve_linear_extent};
#[path="SOLVER_PATH"] mod original;
pub fn solve(j:[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{
 let d=original::solve(j,b)?;let full=solve_linear_extent(j,b)?;let mut ratio=0_f64;let mut backward=0_f64;
 for i in 0..458{ratio=ratio.max((d[i]-full[i]).abs()/if(98..133).contains(&(i%229)){2e-12}else{2e-9});let mut sum=0.;let mut low=0.;let mut denom=b[i].abs();for k in 0..458{let term=j[i][k]*d[k];let t=sum+term;low+=if sum.abs()>=term.abs(){(sum-t)+term}else{(term-t)+sum};sum=t;denom+=term.abs();}let error=((sum-b[i])+low).abs();let q=if denom==0.{assert_eq!(error,0.);0.}else{error/denom};backward=backward.max(q);}
 assert!(ratio<=1.,"correction difference {ratio}");assert!(backward<=1e-11,"full backward error {backward}");println!("LINEAR,{ratio:.17e},{backward:.17e}");Ok(d)
}
'''
MAIN='''fn main(){
 let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);let maps:[[usize;37];2]=MAPS;
 for(i,c)in cs.iter().enumerate(){let a=run_reference(c);let b=run_reuse(c);compare(&a,&b);
  for block in 2..4{for map in maps{let values=|q:&(Vec<u64>,usize,usize)|std::array::from_fn(|k|{let n=map[k];if n==usize::MAX{0.}else{f64::from_bits(q.0[block*458+n])+f64::from_bits(q.0[block*458+n+229])}});let x=values(&a);let y=values(&b);let old=rf_d_circuit::lm741::memory(&x);let new=rf_d_circuit::lm741::memory(&y);let mut error=0_f64;for k in 0..3{error=error.max((old.capacitor_v[k]-new.capacitor_v[k]).abs()/4e-6);}for k in 0..2{error=error.max((old.inductor_i_a[k]-new.inductor_i_a[k]).abs()/2e-9);}assert!(error<=1.,"memory {i}: {error}");let old=rf_d_circuit::lm741::linearize(x,rf_d_circuit::lm741::Mode::Dc).unwrap();let new=rf_d_circuit::lm741::linearize(y,rf_d_circuit::lm741::Mode::Dc).unwrap();let current=old.residual[..5].iter().chain(std::iter::once(&old.ground_current_a)).zip(new.residual[..5].iter().chain(std::iter::once(&new.ground_current_a))).map(|(x,y)|(x-y).abs()).fold(0_f64,f64::max);assert!(current<=2e-11,"port current {i}: {current}");println!("PORT,{i},{block},{error:.17e},{current:.17e}");}}
 }
 println!("DIAGNOSTIC_PASSED,84,336,1680,2016");
}
'''
def main():
 work=ROOT/'references-local/dynamic-schur-diagnostic01';require(not work.exists(),'exclusive diagnostic');work.mkdir();names=['tools/run_dynamic_schur_diagnostic.py','tools/joint_dynamic_schur_fast_kernel.rs','tools/dynamic_schur_fast_solver.rs','tools/dynamic_schur_fast_bench.rs','docs/SCHUR_DINAMICO_OBSERVACIONES.md'];sources={n:sha(ROOT/n) for n in names};packet='references-local/newton-reuse-inputs01/pairs.bin';lib='references-local/joint-startup01/librf_d_circuit.rlib';private={n:sha(ROOT/n) for n in [packet,lib]};compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');proxy=work/'proxy.rs';proxy.write_text(PROXY.replace('SOLVER_PATH',(ROOT/'tools/dynamic_schur_fast_solver.rs').as_posix()),encoding='utf8',newline='\n');s=(ROOT/'tools/joint_dynamic_schur_fast_kernel.rs').read_text(encoding='utf8');s=s.replace('path="dynamic_schur_fast_solver.rs"','path="'+proxy.as_posix()+'"').replace('path="latch_charge_driver.rs"','path="'+(ROOT/'tools/latch_charge_driver.rs').as_posix()+'"').replace('path="contour_closed_driver.rs"','path="'+(ROOT/'tools/contour_closed_driver.rs').as_posix()+'"');kp=work/'kernel.rs';kp.write_text(s,encoding='utf8',newline='\n');s=(ROOT/'tools/dynamic_schur_fast_bench.rs').read_text(encoding='utf8').split('fn main(){')[0];s=s.replace('path="joint_lu_extent_kernel.rs"','path="'+(ROOT/'tools/joint_lu_extent_kernel.rs').as_posix()+'"').replace('path="joint_dynamic_schur_fast_kernel.rs"','path="'+kp.as_posix()+'"').replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix());_,_,_,raw=maps();node=lambda k:('usize::MAX' if k==134 else str(k if k<108 else k-1));maptext='['+','.join('['+','.join(node(k) for k in row)+']' for row in raw)+']';p=work/'diagnostic.rs';p.write_text(s+MAIN.replace('MAPS',maptext),encoding='utf8',newline='\n');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler)
 def run(cmd,limit):
  t=time.perf_counter();q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);c=dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-t);commands.append(c);write(f'evidence/voice_dynamic_schur_diagnostic_command01-{len(commands):02d}.json',c);return c
 try:
  exe=work/'diagnostic.exe';q=run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(p),'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],120)
  if q['exit_code']:run(q['command'],120);require(False,'compile rejection')
  q=run([str(exe),str(ROOT/packet)],600)
  if q['exit_code']:run(q['command'],600);require(False,'direct correction rejection')
  r['passed']=True
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
 r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable diagnostic');write('evidence/voice_dynamic_schur_diagnostic01.json',r);print('SCHUR_DIRECT_DIAGNOSTIC',r['passed'],r.get('failure',''))
if __name__=='__main__':main()
