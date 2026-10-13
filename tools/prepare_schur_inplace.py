"""Derive an in-place workspace from the frozen exact-support Schur implementation."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/dynamic_schur_inplace_solver.rs text eol=lf\n/tools/joint_schur_inplace_kernel.rs text eol=lf\n/tools/joint_schur_inplace_runner.rs text eol=lf\n/tools/schur_inplace_bench.rs text eol=lf\n'
BLANK='''Self{inner:[Lu{a:[[0.;64];64],perm:[0;64]},Lu{a:[[0.;64];64],perm:[0;64]}],outer:Lu{a:[[0.;330];330],perm:[0;330]},response:[[[0.;10];64];2],position:[usize::MAX;458],sparse:Sparse{row:[0;459],column:[0;CAPACITY],value:[0.;CAPACITY],floor:[0.;458]}}'''
INIT=''' fn initialize(&mut self,j:&[[f64;458];458])->Result<(),StepError>{
  self.sparse.initialize(j)?;self.position.fill(usize::MAX);for(i,&k)in EXTERNAL.iter().enumerate(){self.position[k]=i;}
  for block in 0..2{let mut allowed=[false;458];for &k in INNER[block].iter().chain(PORTS[block].iter()){if k!=usize::MAX{allowed[k]=true;}}for &i in &INNER[block]{for k in 0..458{if !allowed[k]&&(j[i][k]!=0.||j[k][i]!=0.){return Err(StepError::SingularJacobian);}}}}
  for block in 0..2{for r in 0..64{for c in 0..64{self.inner[block].a[r][c]=j[INNER[block][r]][INNER[block][c]];}}self.inner[block].factor_in_place()?;}
  for block in 0..2{for k in 0..10{let p=PORTS[block][k];let b=std::array::from_fn(|i|if p==usize::MAX{0.}else{j[INNER[block][i]][p]});let w=self.inner[block].solve(b)?;for i in 0..64{self.response[block][i][k]=w[i];}}}
  for r in 0..330{for c in 0..330{self.outer.a[r][c]=j[EXTERNAL[r]][EXTERNAL[c]];}}
  for block in 0..2{for &p in &PORTS[block]{if p==usize::MAX{continue;}let row=self.position[p];for i in 0..64{let factor=j[p][INNER[block][i]];if factor==0.{continue;}for k in 0..10{let q=PORTS[block][k];if q!=usize::MAX{self.outer.a[row][self.position[q]]-=factor*self.response[block][i][k];}}}}}
  self.outer.factor_in_place()?;Ok(())
 }
'''
def solver():
    s=(ROOT/'tools/dynamic_schur_refined_sparse_solver.rs').read_text(encoding='utf8');s=s.replace(' fn factor(mut a:[[f64;N];N])->Result<Self,StepError>{\n  let mut perm=std::array::from_fn(|k|k);',' fn factor_in_place(&mut self)->Result<(),StepError>{\n  let a=&mut self.a;self.perm=std::array::from_fn(|k|k);let perm=&mut self.perm;',1).replace('Ok(Self{a,perm})','Ok(())',1)
    a=s.index(' fn new(',s.index('impl Prepared{'));b=s.index(' fn correction(',a);s=s[:a]+' const fn blank()->Self{'+BLANK+'}\n'+INIT+s[b:]
    a=s.index(' fn new(',s.index('impl Sparse{'));b=s.index('\n}\nfn residual',a);part=s[a:b];part=part.replace(' fn new(j:&[[f64;458];458])->Result<Self,StepError>{',' fn initialize(&mut self,j:&[[f64;458];458])->Result<(),StepError>{',1).replace('  let mut out=Self{row:[0;459],column:[0;CAPACITY],value:[0.;CAPACITY],floor:[0.;458]};let mut n=0;','  self.floor.fill(0.);let mut n=0;',1).replace('out.','self.').replace('Ok(out)','Ok(())');s=s[:a]+part+s[b:]
    require('let p=Prepared::new(&j)?;' in s,'original lifetime');s=s.replace('let p=Prepared::new(&j)?;','let mut p=Prepared::blank();p.initialize(&j)?;',1);require(' fn new(' not in s and ' fn factor(' not in s,'no aggregate constructors');return s
def kernel():return (ROOT/'tools/joint_schur_refined_sparse_kernel.rs').read_text(encoding='utf8').replace('dynamic_schur_refined_sparse_solver.rs','dynamic_schur_inplace_solver.rs')
def caller():return (ROOT/'tools/joint_schur_refined_sparse_runner.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_inplace_kernel.rs')
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='cf79a8d63e5ccc2d6dbc89dc489a57baf2059d3a','base');old_name='evidence/voice_schur_cost_tests01.json';old=json.loads((ROOT/old_name).read_text(encoding='utf8'));require(old['passed'] and old['numeric_bank_passed'] and not old['cost_utility_passed'],'base scope');write('evidence/voice_schur_inplace_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/old_name),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in [('tools/dynamic_schur_inplace_solver.rs',solver()),('tools/joint_schur_inplace_kernel.rs',kernel()),('tools/joint_schur_inplace_runner.rs',caller()),('tools/schur_inplace_bench.rs',(ROOT/'tools/schur_refined_sparse_bench.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_inplace_kernel.rs'))]:
        p=ROOT/n;require(not p.exists(),'exclusive candidate');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);private={n:sha(ROOT/n) for n in ['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib','references-local/schur-refined-bank01/linear.bin']}
    for n,h in private.items():require(h==old['private_input_sha256'][n],'frozen private '+n)
    write('evidence/voice_schur_inplace_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_schur_inplace.py','tools/dynamic_schur_inplace_solver.rs','tools/joint_schur_inplace_kernel.rs','tools/joint_schur_inplace_runner.rs','tools/schur_inplace_bench.rs','docs/SCHUR_EN_SITIO_PROTOCOLO.md']},private_used_sha256=private,mixed_backward_gate=1e-11,maximum_refinements=3,nonzero_capacity=4096,seeds=json.loads((ROOT/'evidence/voice_lu_extent_inputs01.json').read_text(encoding='utf8'))['seeds']))
if __name__=='__main__':main()
