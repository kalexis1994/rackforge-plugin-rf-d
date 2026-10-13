"""Separate operation counts and solver regressions from paired timing."""
import base64,json,os,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def counted(s,optimized):
 if optimized:s=s.replace('   rhs[row]-=factor*rhs[col];','   UPDATES.fetch_add((end-col-1) as u64,std::sync::atomic::Ordering::Relaxed);rhs[row]-=factor*rhs[col];')
 else:s=s.replace('            rhs[row] -= factor * rhs[col];','            UPDATES.fetch_add((M-col-1) as u64,std::sync::atomic::Ordering::Relaxed);rhs[row] -= factor * rhs[col];')
 return s+'''\nstatic UPDATES:std::sync::atomic::AtomicU64=std::sync::atomic::AtomicU64::new(0);
pub fn reset_updates(){UPDATES.store(0,std::sync::atomic::Ordering::Relaxed);}
pub fn updates()->u64{UPDATES.load(std::sync::atomic::Ordering::Relaxed)}
'''
MAIN='''fn main(){
 for case in 0..8{
  let mut j=[[0.;8];8];let mut rhs=std::array::from_fn(|k|(k+1) as f64);
  match case{
   0=>{for k in 0..8{j[k][k]=1.;}},
   1=>{for k in 0..8{j[k][(k+1)%8]=1.;}},
   2=>{for k in 0..8{j[k][k]=3.;if k<7{j[k][k+1]=0.25;j[k+1][k]=-0.5;}}j[0][7]=0.125;},
   3=>{for k in 0..8{j[k][k]=1.;if k<7{j[k][k+1]=1e-200;}}},
   4=>{for k in 0..8{j[k][k]=1.;}j[7]=[0.;8];},
   5=>{for k in 0..8{j[k][k]=1.;}j[1]=j[0];},
   6=>{for k in 0..8{j[k][k]=1.;}j[0][7]=-0.;rhs[0]=-0.;},
   _=>{for k in 0..8{j[k][k]=1.;}j[0][0]=f64::INFINITY;}
  }
  let a=reference::solve_linear_sparse(j,rhs).map(|v|v.map(f64::to_bits)).map_err(|e|format!("{e:?}"));let b=reuse::solve_linear_extent(j,rhs).map(|v|v.map(f64::to_bits)).map_err(|e|format!("{e:?}"));assert_eq!(a,b,"solver regression {case}");println!("REGRESSION,{case},{:?}",a);
 }
 let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);reference::reset_updates();reuse::reset_updates();
 for c in &cs{let a=run_reference(c);let b=run_reuse(c);assert_eq!(a,b);assert_eq!(a.0,stored(c));}
 println!("UPDATES,{},{},84",reference::updates(),reuse::updates());
 println!("DIAGNOSTIC_PASSED,8,84");
}
'''
def main():
 work=ROOT/'references-local/lu-extent-diagnostic01';require(not work.exists(),'exclusive diagnostic');work.mkdir();compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');names=['tools/run_lu_extent_diagnostic.py','tools/joint_newton_reuse_kernel.rs','tools/joint_lu_extent_kernel.rs','tools/lu_extent_bench.rs','docs/LU_EXTENSION_PROTOCOLO.md'];sources={n:sha(ROOT/n) for n in names};packet='references-local/newton-reuse-inputs01/pairs.bin';lib='references-local/joint-startup01/librf_d_circuit.rlib';private={n:sha(ROOT/n) for n in [packet,lib]}
 for name,n,opt in [('reference.rs','tools/joint_newton_reuse_kernel.rs',False),('extent.rs','tools/joint_lu_extent_kernel.rs',True)]:
  s=counted((ROOT/n).read_text(encoding='utf8'),opt).replace('path="latch_charge_driver.rs"','path="'+(ROOT/'tools/latch_charge_driver.rs').as_posix()+'"').replace('path="contour_closed_driver.rs"','path="'+(ROOT/'tools/contour_closed_driver.rs').as_posix()+'"');(work/name).write_text(s,encoding='utf8',newline='\n')
 s=(ROOT/'tools/lu_extent_bench.rs').read_text(encoding='utf8').split('fn main(){')[0];s=s.replace('../references-local/lu-extent-inputs01/reference_profile.rs',(work/'reference.rs').as_posix()).replace('../references-local/lu-extent-inputs01/reuse_profile.rs',(work/'extent.rs').as_posix()).replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix());source=work/'diagnostic.rs';source.write_text(s+MAIN,encoding='utf8',newline='\n');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler)
 def run(cmd,limit):
  t=time.perf_counter();q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);c=dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-t);commands.append(c);write(f'evidence/voice_lu_extent_diagnostic_command01-{len(commands):02d}.json',c);return c
 try:
  exe=work/'diagnostic.exe';q=run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(source),'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],120)
  if q['exit_code']:run(q['command'],120);require(False,'diagnostic compile')
  q=run([str(exe),str(ROOT/packet)],300)
  if q['exit_code']:run(q['command'],300);require(False,'diagnostic rejection')
  r['passed']=True
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
 r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable diagnostic');write('evidence/voice_lu_extent_diagnostic01.json',r);print('LU_DIAGNOSTIC',r['passed'],r.get('failure',''))
if __name__=='__main__':main()
