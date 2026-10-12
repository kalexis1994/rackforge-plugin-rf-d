"""Generate a pure accepted-trial cache and separately instrumented lab kernels."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/joint_newton_reuse_kernel.rs text eol=lf\n/tools/joint_newton_reuse_runner.rs text eol=lf\n/tools/newton_reuse_bench.rs text eol=lf\n'
def kernel():
 s=(ROOT/'tools/joint_contour_cycle_kernel.rs').read_text(encoding='utf8')
 s=s.replace(' let mut delta=[State::from_nodes(seed);2];let mut trials=0;',' let mut delta=[State::from_nodes(seed);2];let mut trials=0;\n let mut s=linearize(p,old,delta,h)?;let mut d=solve_linear_sparse(s.jacobian,std::array::from_fn(|k|-s.residual[k]))?;')
 s=s.replace('  let s=linearize(p,old,delta,h)?;let norm=merit(p,&s.residual);let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|k|-s.residual[k]))?;let ratio=correction(&d);','  let norm=merit(p,&s.residual);let ratio=correction(&d);')
 s=s.replace('  let mut accepted=false;','  let mut accepted=None;').replace('{delta=trial;accepted=true;break;}','{accepted=Some((trial,t,dd));break;}').replace('  if !accepted {return Err(StepError::NoDecrease);}','  match accepted {Some((trial,next,correction))=>{delta=trial;s=next;d=correction;},None=>return Err(StepError::NoDecrease)}')
 return s
def caller():return (ROOT/'tools/joint_contour_cycle_runner.rs').read_text(encoding='utf8').replace('path="joint_contour_cycle_kernel.rs"','path="joint_newton_reuse_kernel.rs"')
def instrument(s):
 start=s.index('pub fn step(');end=s.index('\nmod fine',start);piece=s[start:end].replace('linearize(p,','profile_linearize(p,').replace('solve_linear_sparse(','profile_solve(');s=s[:start]+piece+s[end:]
 return s+'''\nuse std::sync::atomic::{AtomicU64,Ordering::Relaxed};
static ASSEMBLY:AtomicU64=AtomicU64::new(0);static SOLVE:AtomicU64=AtomicU64::new(0);static ASSEMBLY_NS:AtomicU64=AtomicU64::new(0);static SOLVE_NS:AtomicU64=AtomicU64::new(0);
pub fn reset_profile(){for c in [&ASSEMBLY,&SOLVE,&ASSEMBLY_NS,&SOLVE_NS]{c.store(0,Relaxed);}}
pub fn profile()->[u64;4]{[ASSEMBLY.load(Relaxed),SOLVE.load(Relaxed),ASSEMBLY_NS.load(Relaxed),SOLVE_NS.load(Relaxed)]}
fn profile_linearize(p:Parameters,old:State,delta:[State;2],h:f64)->Result<Stamp,StepError>{let t=std::time::Instant::now();let r=linearize(p,old,delta,h);ASSEMBLY.fetch_add(1,Relaxed);ASSEMBLY_NS.fetch_add(t.elapsed().as_nanos() as u64,Relaxed);r}
fn profile_solve(j:[[f64;M];M],r:[f64;M])->Result<[f64;M],StepError>{let t=std::time::Instant::now();let q=solve_linear_sparse(j,r);SOLVE.fetch_add(1,Relaxed);SOLVE_NS.fetch_add(t.elapsed().as_nanos() as u64,Relaxed);q}
'''
def main():
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='f8b89c9790bc7bc07f358903a1d6bfdfb0270330','base');old=json.loads((ROOT/'evidence/voice_contour_cycle_tests01.json').read_text(encoding='utf8'));require(old['passed'],'QA');write('evidence/newton_reuse_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_contour_cycle_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 work=ROOT/'references-local/newton-reuse-inputs01';require(not work.exists(),'exclusive input');work.mkdir();rows=[];used={};profiles=json.loads((ROOT/'evidence/voice_contour_cycle_native02.json').read_text(encoding='utf8'))['profiles']
 for p in profiles:
  path=__import__('pathlib').Path(p['command'][2])/'selected.txt';used[path.relative_to(ROOT).as_posix()]=sha(path);lines=path.read_text(encoding='utf8').splitlines();phase=0
  for i,line in enumerate(lines):
   if line.startswith('BOUNDARY,'):phase=int(line.split(',')[1])
   if line.startswith('JOINT_ROOT,'):
    header=line.split(',');states=[list(map(float,x.split(',')[1:])) for x in lines[i+1:i+6]];require(all(len(x)==458 for x in states),'state dimensions');rows.append((int(p['final_decay']),phase,float(header[2]),float(header[3]),float(header[4]),states))
 require(len(rows)==84,'selected pairs');raw=struct.pack('<Q',len(rows))
 for on,phase,h,res,corr,states in rows:raw+=struct.pack('<2I3d2290d',on,phase,h,res,corr,*[x for state in states for x in state])
 packet=work/'pairs.bin';packet.write_bytes(raw)
 for n,s in [('tools/joint_newton_reuse_kernel.rs',kernel()),('tools/joint_newton_reuse_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 for name,s in [('reference_profile.rs',instrument((ROOT/'tools/joint_contour_cycle_kernel.rs').read_text(encoding='utf8'))),('reuse_profile.rs',instrument(kernel()))]:
  s=s.replace('path="latch_charge_driver.rs"','path="'+(ROOT/'tools/latch_charge_driver.rs').as_posix()+'"').replace('path="contour_closed_driver.rs"','path="'+(ROOT/'tools/contour_closed_driver.rs').as_posix()+'"');(work/name).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);write('evidence/newton_reuse_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_newton_reuse.py','tools/joint_newton_reuse_kernel.rs','tools/joint_newton_reuse_runner.rs','tools/joint_contour_cycle_kernel.rs','docs/NEWTON_REUSO_PROTOCOLO.md']},private_used_sha256={**used,**{p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()}},selected_pairs=84,seeds=json.loads((ROOT/'evidence/voice_contour_cycle_inputs02.json').read_text(encoding='utf8'))['seeds']));print('REUSE_INPUTS',len(rows))
if __name__=='__main__':main()
