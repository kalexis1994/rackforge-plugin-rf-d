"""Condense the downstream dynamic chain, retaining shared BUS/VCA terminals."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_dynamic_schur import maps
from prepare_schur_contour import replace_once,INNER as CONTOUR
from joint_cycles_analysis import require
ATTR=b'\n/tools/dynamic_schur_chain_solver.rs text eol=lf\n/tools/joint_schur_chain_kernel.rs text eol=lf\n/tools/joint_schur_chain_runner.rs text eol=lf\n/tools/schur_chain_bench.rs text eol=lf\n'
INNER=[k+stage*229 for stage in range(2) for k in range(133,200) if k!=165]
PORTS=[12,165,241,394]
EXTERNAL=[k for k in maps()[2] if k not in CONTOUR and k not in INNER]

def solver():
    s=(ROOT/'tools/dynamic_schur_contour_solver.rs').read_text(encoding='utf8')
    require(len(INNER)==132 and len(EXTERNAL)==140 and set(PORTS)<=set(EXTERNAL),'full partition')
    a=s.index('const EXTERNAL:');b=s.index('\npub const MAX_REFINEMENTS',a)
    s=s[:a]+'const CHAIN:[usize;132]='+str(INNER).replace(' ','')+';\nconst CHAIN_PORTS:[usize;4]=[12,165,241,394];\nconst EXTERNAL:[usize;140]='+str(EXTERNAL).replace(' ','')+';'+s[b:]
    s=replace_once(s,'outer:Lu<272>','outer:Lu<140>,chain:Lu<132>,chain_response:[[f64;4];132]')
    s=replace_once(s,'outer:Lu{a:[[0.;272];272],perm:[0;272]}','outer:Lu{a:[[0.;140];140],perm:[0;140]},chain:Lu{a:[[0.;132];132],perm:[0;132]},chain_response:[[0.;4];132]')
    anchor='  for r in 0..58{for c in 0..58'
    inserted='''  let mut allowed=[false;458];for &k in CHAIN.iter().chain(CHAIN_PORTS.iter()){allowed[k]=true;}for &i in &CHAIN{for k in 0..458{if !allowed[k]&&(j[i][k]!=0.||j[k][i]!=0.){return Err(StepError::SingularJacobian);}}}
  for r in 0..132{for c in 0..132{self.chain.a[r][c]=j[CHAIN[r]][CHAIN[c]];}}self.chain.factor_in_place()?;
  for k in 0..4{let p=CHAIN_PORTS[k];let w=self.chain.solve(CHAIN.map(|i|j[i][p]))?;for i in 0..132{self.chain_response[i][k]=w[i];}}
'''
    s=replace_once(s,anchor,inserted+anchor).replace('0..272','0..140')
    s=replace_once(s,'  self.outer.factor_in_place()?;', '''  for &p in &CHAIN_PORTS{let row=self.position[p];for i in 0..132{let factor=j[p][CHAIN[i]];if factor==0.{continue;}for k in 0..4{self.outer.a[row][self.position[CHAIN_PORTS[k]]]-=factor*self.chain_response[i][k];}}}
  self.outer.factor_in_place()?;''')
    s=replace_once(s,'let mut rhs=EXTERNAL.map(|k|b[k]);','let ua=self.chain.solve(CHAIN.map(|k|b[k]))?;let mut rhs=EXTERNAL.map(|k|b[k]);')
    s=replace_once(s,'  let de=self.outer.solve(rhs)?;', '''  for &p in &CHAIN_PORTS{for i in 0..132{let factor=j[p][CHAIN[i]];if factor!=0.{rhs[self.position[p]]-=factor*ua[i];}}}
  let de=self.outer.solve(rhs)?;''')
    s=replace_once(s,'  if d.iter().any(|v|!v.is_finite())', '''  for i in 0..132{let mut v=ua[i];for k in 0..4{v-=self.chain_response[i][k]*d[CHAIN_PORTS[k]];}d[CHAIN[i]]=v;}
  if d.iter().any(|v|!v.is_finite())''')
    return s.replace('//! Three dynamic blocks: two LM741s and the loaded contour; complete reconstruction.','//! Four dynamic blocks: two LM741s, contour and loaded chain; shared terminals retained.')

def kernel():return (ROOT/'tools/joint_schur_contour_kernel.rs').read_text(encoding='utf8').replace('dynamic_schur_contour_solver.rs','dynamic_schur_chain_solver.rs')
def caller():return (ROOT/'tools/joint_schur_contour_runner.rs').read_text(encoding='utf8').replace('joint_schur_contour_kernel.rs','joint_schur_chain_kernel.rs')
def bench():
    s=(ROOT/'tools/schur_contour_bench.rs').read_text(encoding='utf8').replace('joint_schur_contour_kernel.rs','joint_schur_chain_kernel.rs')
    return s.replace('joint_schur_inplace_kernel.rs','joint_schur_contour_kernel.rs')

def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='75455066583b01a41ed960113c34d7de8579e1be','base')
    previous='evidence/voice_schur_contour_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));require(old['passed'] and old['contour_schur_admitted'],'admitted control')
    f=json.loads((ROOT/'evidence/voice_schur_chain_frontier01.json').read_text(encoding='utf8'));require(f['passed'] and f['proposed_interiors']==INNER and f['remaining_exterior']==EXTERNAL and f['proposed_ports']==PORTS,'inspected frontier')
    write('evidence/voice_schur_chain_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in [('tools/dynamic_schur_chain_solver.rs',solver()),('tools/joint_schur_chain_kernel.rs',kernel()),('tools/joint_schur_chain_runner.rs',caller()),('tools/schur_chain_bench.rs',bench())]:
        p=ROOT/n;require(not p.exists(),'exclusive candidate');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
    private={n:sha(ROOT/n) for n in ['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib']}
    for n,h in private.items():require(h==old['private_input_sha256'][n],'frozen private '+n)
    names=['tools/prepare_schur_chain.py','tools/dynamic_schur_chain_solver.rs','tools/joint_schur_chain_kernel.rs','tools/joint_schur_chain_runner.rs','tools/schur_chain_bench.rs','crates/rf-d-circuit/src/joint_voice.rs','evidence/voice_schur_chain_frontier01.json','docs/SCHUR_CADENA_PROTOCOLO.md']
    write('evidence/voice_schur_chain_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in names},private_used_sha256=private,chain_interiors=INNER,chain_ports=PORTS,external=EXTERNAL,seeds=json.loads((ROOT/'evidence/voice_schur_contour_inputs01.json').read_text(encoding='utf8'))['seeds']))
    print('SCHUR_CHAIN_INPUTS',132,4,140)
if __name__=='__main__':main()
