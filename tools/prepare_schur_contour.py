"""Condense the reviewed loaded board2 contour, retaining both Radau stages."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_dynamic_schur import maps
from joint_cycles_analysis import require
ATTR=b'\n/tools/dynamic_schur_contour_solver.rs text eol=lf\n/tools/joint_schur_contour_kernel.rs text eol=lf\n/tools/joint_schur_contour_runner.rs text eol=lf\n/tools/schur_contour_bench.rs text eol=lf\n'
INNER=list(range(200,229))+list(range(429,458))
PORTS=[165,394]

def replace_once(s,a,b):
    require(s.count(a)==1,'unique recipe anchor '+a[:50]);return s.replace(a,b,1)

def solver():
    s=(ROOT/'tools/dynamic_schur_inplace_solver.rs').read_text(encoding='utf8')
    external=[k for k in maps()[2] if k not in INNER]
    require(len(external)==272 and len(set(INNER))==58 and set(PORTS)<=set(external),'complete partition')
    start=s.index('const EXTERNAL:');end=s.index('\npub const MAX_REFINEMENTS',start)
    s=s[:start]+'const CONTOUR:[usize;58]='+str(INNER).replace(' ','')+';\nconst CONTOUR_PORTS:[usize;2]=[165,394];\nconst EXTERNAL:[usize;272]='+str(external).replace(' ','')+';'+s[end:]
    s=replace_once(s,'outer:Lu<330>','outer:Lu<272>,contour:Lu<58>,contour_response:[[f64;2];58]')
    s=replace_once(s,'outer:Lu{a:[[0.;330];330],perm:[0;330]}','outer:Lu{a:[[0.;272];272],perm:[0;272]},contour:Lu{a:[[0.;58];58],perm:[0;58]},contour_response:[[0.;2];58]')
    anchor='  for block in 0..2{for r in 0..64'
    inserted='''  let mut allowed=[false;458];for &k in CONTOUR.iter().chain(CONTOUR_PORTS.iter()){allowed[k]=true;}for &i in &CONTOUR{for k in 0..458{if !allowed[k]&&(j[i][k]!=0.||j[k][i]!=0.){return Err(StepError::SingularJacobian);}}}
  for r in 0..58{for c in 0..58{self.contour.a[r][c]=j[CONTOUR[r]][CONTOUR[c]];}}self.contour.factor_in_place()?;
  for k in 0..2{let p=CONTOUR_PORTS[k];let w=self.contour.solve(CONTOUR.map(|i|j[i][p]))?;for i in 0..58{self.contour_response[i][k]=w[i];}}
'''
    s=replace_once(s,anchor,inserted+anchor).replace('0..330','0..272')
    s=replace_once(s,'  self.outer.factor_in_place()?;', '''  for &p in &CONTOUR_PORTS{let row=self.position[p];for i in 0..58{let factor=j[p][CONTOUR[i]];if factor==0.{continue;}for k in 0..2{self.outer.a[row][self.position[CONTOUR_PORTS[k]]]-=factor*self.contour_response[i][k];}}}
  self.outer.factor_in_place()?;''')
    s=replace_once(s,'let mut rhs=EXTERNAL.map(|k|b[k]);','let uc=self.contour.solve(CONTOUR.map(|k|b[k]))?;let mut rhs=EXTERNAL.map(|k|b[k]);')
    s=replace_once(s,'  let de=self.outer.solve(rhs)?;', '''  for &p in &CONTOUR_PORTS{for i in 0..58{let factor=j[p][CONTOUR[i]];if factor!=0.{rhs[self.position[p]]-=factor*uc[i];}}}
  let de=self.outer.solve(rhs)?;''')
    s=replace_once(s,'  if d.iter().any(|v|!v.is_finite())', '''  for i in 0..58{let mut v=uc[i];for k in 0..2{v-=self.contour_response[i][k]*d[CONTOUR_PORTS[k]];}d[CONTOUR[i]]=v;}
  if d.iter().any(|v|!v.is_finite())''')
    return s.replace('//! Reuse dynamic interior/exterior factors; bounded compensated iterative refinement.','//! Three dynamic blocks: two LM741s and the loaded contour; complete reconstruction.')

def kernel():return (ROOT/'tools/joint_schur_inplace_kernel.rs').read_text(encoding='utf8').replace('dynamic_schur_inplace_solver.rs','dynamic_schur_contour_solver.rs')
def caller():return (ROOT/'tools/joint_schur_inplace_runner.rs').read_text(encoding='utf8').replace('joint_schur_inplace_kernel.rs','joint_schur_contour_kernel.rs')
def bench():
    s=(ROOT/'tools/schur_inplace_bench.rs').read_text(encoding='utf8').replace('joint_schur_inplace_kernel.rs','joint_schur_contour_kernel.rs')
    # The current admitted Schur is the paired cost control. Original LU is
    # retained independently to verify the frozen packet and candidate gate.
    s=replace_once(s,'#[path="joint_lu_extent_kernel.rs"] mod reference;','#[path="joint_lu_extent_kernel.rs"] mod original;\n#[path="joint_schur_inplace_kernel.rs"] mod reference;')
    s=replace_once(s,'execute!(run_reference,reference);','execute!(run_original,original);execute!(run_reference,reference);')
    s=replace_once(s,'let a=run_reference(c);assert_eq!(a.0,stored(c),"reference stored bits");','let raw=run_original(c);assert_eq!(raw.0,stored(c),"original stored bits");let a=run_reference(c);compare(&raw,&a);')
    s=replace_once(s,'let error=compare(&a,&b);','let error=compare(&raw,&b);compare(&a,&b);')
    s=replace_once(s,' for round in 0..5{',' for c in &cs{std::hint::black_box(run_reference(c));std::hint::black_box(run_reuse(c));}\n for round in 0..5{')
    return s

def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='919cde53e3177e508f4a3b11232b0c2e57b227d2','base')
    previous='evidence/voice_schur_inplace_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));require(old['passed'] and old['dynamic_schur_admitted'],'admitted control')
    write('evidence/voice_schur_contour_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in [('tools/dynamic_schur_contour_solver.rs',solver()),('tools/joint_schur_contour_kernel.rs',kernel()),('tools/joint_schur_contour_runner.rs',caller()),('tools/schur_contour_bench.rs',bench())]:
        p=ROOT/n;require(not p.exists(),'exclusive candidate');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
    private={n:sha(ROOT/n) for n in ['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib']}
    for n,h in private.items():require(h==old['private_input_sha256'][n],'frozen private '+n)
    names=['tools/prepare_schur_contour.py','tools/dynamic_schur_contour_solver.rs','tools/joint_schur_contour_kernel.rs','tools/joint_schur_contour_runner.rs','tools/schur_contour_bench.rs','tools/contour_closed_driver.rs','docs/SCHUR_CONTORNO_PROTOCOLO.md']
    write('evidence/voice_schur_contour_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in names},private_used_sha256=private,contour_interiors=INNER,contour_ports=PORTS,external=[k for k in maps()[2] if k not in INNER],seeds=json.loads((ROOT/'evidence/voice_schur_inplace_inputs01.json').read_text(encoding='utf8'))['seeds']))
    print('SCHUR_CONTOUR_INPUTS',58,2,272)
if __name__=='__main__':main()
