"""Assemble Radau in two initialized destinations; swap references after acceptance."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_schur_contour import replace_once
from joint_cycles_analysis import require
ATTR=b'\n/tools/joint_radau_inplace_kernel.rs text eol=lf\n/tools/joint_radau_inplace_runner.rs text eol=lf\n/tools/radau_inplace_bench.rs text eol=lf\n'
STAMP='''impl Stamp{
 pub const fn blank()->Self{Self{residual:[0.;M],jacobian:[[0.;M];M],candidates:[State{high:[0.;N],low:[0.;N]};2]}}
 pub fn initialize(&mut self,p:Parameters,old:State,delta:[State;2],h:f64)->Result<(),StepError>{
  let q=[parts(p,old,delta[0],h)?,parts(p,old,delta[1],h)?];
  for k in 0..M{let i=k/N;let a=k%N;self.residual[k]=q[i].dc[a]+B[i][0]*q[0].charge_over_h[a]+B[i][1]*q[1].charge_over_h[a];}
  for k in 0..M{let i=k/N;let a=k%N;for l in 0..M{let j=l/N;let b=l%N;self.jacobian[k][l]=B[i][j]*q[j].mass_over_h[a][b]+if i==j{q[i].dc_jacobian[a][b]}else{0.};}}
  self.candidates=[q[0].candidate,q[1].candidate];Ok(())
 }
}
pub fn linearize(p:Parameters,old:State,delta:[State;2],h:f64)->Result<Stamp,StepError>{let mut s=Stamp::blank();s.initialize(p,old,delta,h)?;Ok(s)}
'''

def kernel():
    s=(ROOT/'tools/joint_schur_chain_kernel.rs').read_text(encoding='utf8');a=s.index('pub fn linearize(');b=s.index('\nfn merit(',a);s=s[:a]+STAMP+s[b:]
    s=replace_once(s,' let mut s=linearize(p,old,delta,h)?;',' let mut first=Stamp::blank();let mut second=Stamp::blank();let(mut s,mut t)=(&mut first,&mut second);s.initialize(p,old,delta,h)?;')
    s=replace_once(s,'   if let Ok(t)=linearize(p,old,trial,h) {','   if t.initialize(p,old,trial,h).is_ok() {')
    s=replace_once(s,'accepted=Some((trial,t,dd));','accepted=Some((trial,dd));')
    s=replace_once(s,'Some((trial,next,correction))=>{delta=trial;s=next;d=correction;}','Some((trial,correction))=>{delta=trial;std::mem::swap(&mut s,&mut t);d=correction;}')
    return s

def caller():return (ROOT/'tools/joint_schur_chain_runner.rs').read_text(encoding='utf8').replace('joint_schur_chain_kernel.rs','joint_radau_inplace_kernel.rs')
def bench():
    s=(ROOT/'tools/schur_chain_bench.rs').read_text(encoding='utf8').replace('joint_schur_chain_kernel.rs','joint_radau_inplace_kernel.rs').replace('joint_schur_contour_kernel.rs','joint_schur_chain_kernel.rs')
    s=replace_once(s,'let error=compare(&raw,&b);compare(&a,&b);','let error=compare(&raw,&b);assert_eq!(a,b,"in-place candidate/increment/ratio/iteration/trial bits");')
    s=replace_once(s,'compare(e,&run_reuse(c));','assert_eq!(&run_reuse(c),e,"in-place timed root identity");')
    return s

def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='9b89edbb40888083545d81b5da75f220a155a980','base')
    previous='evidence/voice_schur_chain_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));require(old['passed'] and old['chain_schur_admitted'],'admitted control')
    write('evidence/voice_radau_inplace_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in [('tools/joint_radau_inplace_kernel.rs',kernel()),('tools/joint_radau_inplace_runner.rs',caller()),('tools/radau_inplace_bench.rs',bench())]:
        p=ROOT/n;require(not p.exists(),'exclusive candidate');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
    private={n:sha(ROOT/n) for n in ['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib','references-local/schur-refined-chainbank01/linear.bin']}
    for n,h in private.items():require(h==old['private_input_sha256'][n],'frozen private '+n)
    names=['tools/prepare_radau_inplace.py','tools/joint_radau_inplace_kernel.rs','tools/joint_radau_inplace_runner.rs','tools/radau_inplace_bench.rs','tools/dynamic_schur_chain_solver.rs','docs/RADAU_EN_SITIO_PROTOCOLO.md']
    write('evidence/voice_radau_inplace_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in names},private_used_sha256=private,seeds=json.loads((ROOT/'evidence/voice_schur_chain_inputs01.json').read_text(encoding='utf8'))['seeds']))
    print('RADAU_INPLACE_INPUTS',229,458,2)
if __name__=='__main__':main()
