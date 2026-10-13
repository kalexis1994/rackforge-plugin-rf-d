"""Keep the passed-but-slower dense residual; cache its exact nonzero support."""
import json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'/tools/dynamic_schur_refined_sparse_solver.rs text eol=lf\n/tools/joint_schur_refined_sparse_kernel.rs text eol=lf\n/tools/joint_schur_refined_sparse_runner.rs text eol=lf\n/tools/schur_refined_sparse_bench.rs text eol=lf\n'
SPARSE='''const CAPACITY:usize=4096;
struct Sparse{row:[usize;459],column:[u16;CAPACITY],value:[f64;CAPACITY],floor:[f64;458]}
impl Sparse{
 fn new(j:&[[f64;458];458])->Result<Self,StepError>{
  let mut out=Self{row:[0;459],column:[0;CAPACITY],value:[0.;CAPACITY],floor:[0.;458]};let mut n=0;
  for i in 0..458{out.row[i]=n;for k in 0..458{let a=j[i][k];if !a.is_finite(){return Err(StepError::InvalidInput);}if a==0.{continue;}if n==CAPACITY{return Err(StepError::InvalidInput);}out.column[n]=k as u16;out.value[n]=a;out.floor[i]+=a.abs()*tau(k);n+=1;}}out.row[458]=n;Ok(out)
 }
}
fn residual(s:&Sparse,b:&[f64;458],d:&[f64;458])->Result<([f64;458],f64),StepError>{
 let mut r=[0.;458];let mut worst=0_f64;
 for i in 0..458{let mut sum=-b[i];let mut low=0.;let mut scale=b[i].abs()+s.floor[i];for entry in s.row[i]..s.row[i+1]{let k=s.column[entry] as usize;let a=s.value[entry];let p=a*d[k];let t=sum+p;low+=if sum.abs()>=p.abs(){(sum-t)+p}else{(p-t)+sum};low+=a.mul_add(d[k],-p);sum=t;scale+=p.abs();}r[i]=-(sum+low);let q=if scale==0.{if r[i]!=0.{return Err(StepError::NoDecrease);}0.}else{r[i].abs()/scale};if !q.is_finite()||!r[i].is_finite(){return Err(StepError::InvalidInput);}worst=worst.max(q);}
 Ok((r,worst))
}
'''
def solver():
    s=(ROOT/'tools/dynamic_schur_refined_solver.rs').read_text(encoding='utf8');s=s.replace('floor:[f64;458]}','sparse:Sparse}',1).replace('  if j.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}','  let sparse=Sparse::new(j)?;',1)
    old='  let floor=std::array::from_fn(|i|(0..458).map(|k|j[i][k].abs()*tau(k)).sum());Ok(Self{inner,outer:Lu::factor(s)?,response,position,floor})';require(old in s,'floor extraction');s=s.replace(old,'  Ok(Self{inner,outer:Lu::factor(s)?,response,position,sparse})');a=s.index('fn residual(');b=s.index('pub struct Observation',a);s=s[:a]+SPARSE+s[b:];return s.replace('residual(&j,&b,&d,&p.floor)','residual(&p.sparse,&b,&d)')
def kernel():return (ROOT/'tools/joint_schur_refined_kernel.rs').read_text(encoding='utf8').replace('dynamic_schur_refined_solver.rs','dynamic_schur_refined_sparse_solver.rs')
def caller():return (ROOT/'tools/joint_schur_refined_runner.rs').read_text(encoding='utf8').replace('joint_schur_refined_kernel.rs','joint_schur_refined_sparse_kernel.rs')
def main():
    bench=json.loads((ROOT/'evidence/voice_schur_refined_bench01.json').read_text(encoding='utf8'));bank=json.loads((ROOT/'evidence/voice_schur_refined_bank01.json').read_text(encoding='utf8'));require(bench['passed'] and not bench['utility_passed'] and bank['passed'],'first scope');write('evidence/voice_schur_refined_sparse_decision01.json',dict(passed=True,numerical_gates_changed=False,dense_bench_sha256=sha(ROOT/'evidence/voice_schur_refined_bench01.json'),dense_bank_sha256=sha(ROOT/'evidence/voice_schur_refined_bank01.json'),dense_source_sha256={n:sha(ROOT/n) for n in ['tools/dynamic_schur_refined_solver.rs','tools/joint_schur_refined_kernel.rs','tools/schur_refined_bench.rs','tools/check_schur_refined_bank.py']},maximum_observed_nnz=max(x['nnz'] for x in bank['exact_linear_checks']),capacity=4096))
    for n,s in [('tools/dynamic_schur_refined_sparse_solver.rs',solver()),('tools/joint_schur_refined_sparse_kernel.rs',kernel()),('tools/joint_schur_refined_sparse_runner.rs',caller()),('tools/schur_refined_sparse_bench.rs',(ROOT/'tools/schur_refined_bench.rs').read_text(encoding='utf8').replace('joint_schur_refined_kernel.rs','joint_schur_refined_sparse_kernel.rs'))]:
        p=ROOT/n;require(not p.exists(),'exclusive sparse source');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);write('evidence/voice_schur_refined_inputs02.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_schur_refined_sparse.py','tools/dynamic_schur_refined_sparse_solver.rs','tools/joint_schur_refined_sparse_kernel.rs','tools/joint_schur_refined_sparse_runner.rs','tools/schur_refined_sparse_bench.rs','docs/SCHUR_REFINADO_SOPORTE.md']},private_used_sha256=json.loads((ROOT/'evidence/voice_schur_refined_inputs01.json').read_text(encoding='utf8'))['private_used_sha256'],maximum_refinements=3,mixed_backward_gate=1e-11,nonzero_capacity=4096))
if __name__=='__main__':main()
