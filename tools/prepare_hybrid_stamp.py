"""Derive prepared chain stamping; preserve all admitted circuit sources."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
def once(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b)
def derive():
    c=(ROOT/'crates/rf-d-circuit/src/circuit66.rs').read_text(encoding='utf8')
    # Retain exact documentary ordering and device laws. No old Euler dynamics.
    order=c[c.index('const N: usize = 66;'):c.index('#[derive(Clone, Copy, Debug, PartialEq)]\npub struct State')]
    order=order[:order.index('// Numerical row/column numbering')]+'''const POSITION:[usize;N]={let mut a=[0;N];let mut i=0;while i<N{a[i]=i;i+=1;}a};
fn natural_jacobian(j:&[[f64;N];N])->[[f64;N];N]{*j}
'''
    stamp=c[c.index('#[derive(Clone, Copy)]\nenum Terminal'):c.index('#[cfg(test)]\nmod junction_tests')]
    prepare=c[c.index('fn valid_bjt('):c.index('fn r21_constraint(')]
    prepare=once(prepare,'    old: Option<&State>,\n','')
    a=prepare.index('    let mut i10 = 0.0;');b=prepare.index('    // Identify terminals AFTER',a);prepare=prepare[:a]+prepare[b:]
    a=prepare.index('    // Q26/Q28 and the reduced panel.');b=prepare.index('    // Recovery Q8/Q6/Q7/Q5.',a);prepare=prepare[:a]+prepare[b:]
    prepare=once(prepare,'        (32, vb.loudness_v, 68000.0),\n','')
    prepare=once(prepare,'Result<([f64; N], [[f64; N]; N], f64), StepError>', 'Result<([f64; N], [[f64; N]; N]), StepError>')
    prepare=once(prepare,'Ok((s.r, s.j, i10))','Ok((s.r, s.j))')
    tail=c[c.index('fn r21_constraint('):c.index('/// Offline DC residual/Jacobian diagnostic,')]
    # Only retain the endpoint equality helper, not earlier solver machinery.
    tail=tail[:tail.index('\n}\n')+3]
    out=(ROOT/'crates/rf-d-circuit/src/output.rs').read_text(encoding='utf8')
    load=out[out.index('#[derive(Clone, Copy)]\npub(crate) struct MainLoad'):out.index('pub fn initial_output_state(')]
    load=load.replace('pub(crate) ','')
    load='\n'.join(line for line in out.splitlines() if line.startswith(('const R20_OHM:', 'const R57_OHM:', 'const R58_OHM:')))+'\n'+load
    header='''//! Prepared audio graph, derived verbatim laws; HYBRID_STAMP_PROTOCOLO.
use rf_d_circuit::{cutoff_ladder_output,output_conversion::{Parameters as ConversionParameters},vca2_output::Parameters as Bjt,Parameters as HeadphoneParameters,SolverBudget,StepError,output::OutputBoundary};
pub use rf_d_circuit::cutoff_ladder_output::{Boundary,Parameters};
const K_B:f64=1.380_649e-23;const Q_E:f64=1.602_176_634e-19;
'''
    # ORDER already includes K_B/Q_E in the selected original prefix.
    header=header.replace('const K_B:f64=1.380_649e-23;const Q_E:f64=1.602_176_634e-19;\n','')
    end='''
#[derive(Clone,Copy)]
pub struct Prepared{p:Parameters,conversion:ConversionParameters,headphone:HeadphoneParameters,b:Boundary,metadata:(rf_d_circuit::cutoff::PanelEquivalent,MainLoad)}
impl Prepared{
 pub fn new(p:Parameters,conversion:ConversionParameters,headphone:HeadphoneParameters,b:Boundary)->Result<Self,StepError>{
  let metadata=prepare(p,conversion,headphone,b,SolverBudget::default())?;Ok(Self{p,conversion,headphone,b,metadata})
 }
 pub fn linearize(self,x:&[f64;N])->Result<([f64;N],[[f64;N];N]),StepError>{
  if x.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
  let(r,j)=evaluate(x,self.p,self.conversion,self.headphone,self.b,self.metadata)?;Ok((r,natural_jacobian(&j)))
 }
}
'''
    audio=(header+order+stamp+load+prepare+tail+end).replace('crate::cutoff::','rf_d_circuit::cutoff::')
    chain=(ROOT/'crates/rf-d-circuit/src/chain_charge.rs').read_text(encoding='utf8')
    chain=once(chain,'use crate::{circuit66, mixer_on::OnMixer,', 'use rf_d_circuit::{mixer_on::OnMixer,')
    chain=chain.replace('crate::vco1_engine::','rf_d_circuit::vco1_engine::')
    chain=once(chain,'pub const N: usize=68;', '#[path="prepared_audio_stamp.rs"] mod circuit66;\npub const N: usize=68;')
    chain=once(chain,'pub struct Parameters {','pub struct Parameters {\n audio:circuit66::Prepared,')
    marker='#[derive(Clone,Copy,Debug,PartialEq)]\npub struct State'
    construct='''impl Parameters{
 pub fn new(p:rf_d_circuit::chain_charge::Parameters)->Result<Self,StepError>{
  Ok(Self{audio:circuit66::Prepared::new(p.circuit,p.conversion,p.headphone,p.boundary)?,circuit:p.circuit,conversion:p.conversion,headphone:p.headphone,boundary:p.boundary,mixer:p.mixer})
 }
}
'''
    chain=once(chain,marker,construct+marker)
    chain=once(chain,'let(r,j)=circuit66::linearize_dc(p.circuit,p.conversion,p.headphone,p.boundary,&x)?;', 'let(r,j)=p.audio.linearize(&x)?;')
    chain=once(chain,'17]=[','16]=[')
    chain=once(chain,'(60,61,400e-6),(62,GROUND,100e-12)', '(60,61,400e-6)')
    chain=once(chain,'Same 17 incidences as circuit66::capacitors;', 'Sixteen audio incidences; shared C18 belongs to the contour;')
    chain=once(chain,'dc.iter().chain(jac.iter().flatten()).chain(q.iter()).chain(mass.iter().flatten())', 'dc.iter().chain(q.iter())')
    graph=(ROOT/'crates/rf-d-circuit/src/dual_voice_chain.rs').read_text(encoding='utf8')
    graph=once(graph,'use rf_d_circuit::{chain_charge, cutoff, mixer_on::OnMixer};','use rf_d_circuit::{cutoff,mixer_on::OnMixer};\n#[path="prepared_chain_charge.rs"] mod chain_charge;')
    graph=once(graph,'pub fn new(mut chain:chain_charge::Parameters)', 'pub fn new(mut chain:rf_d_circuit::chain_charge::Parameters)')
    graph=once(graph,'Ok(Self{chain,time:0.})', 'Ok(Self{chain:chain_charge::Parameters::new(chain)?,time:0.})')
    a=graph.index('    // Omit the old cutoff equations;');b=graph.index('    let mut s=Parts',a);graph=graph[:a]+graph[b:]
    graph=once(graph,'for b in 0..68 {let j=chain_index(b);s.j[i][j]+=audio.dc_jacobian[a][b];s.mass[i][j]+=audio.mass_over_h[a][b];}', 'for b in 0..68 {let j=chain_index(b);let g=audio.dc_jacobian[a][b];let m=audio.mass_over_h[a][b];if g!=0.{s.j[i][j]+=g;}if m!=0.{s.mass[i][j]+=m;}}')
    graph=once(graph,'s.j[a][b]=dual.j[a][b];s.mass[a][b]=dual.mass[a][b];', 'let g=dual.j[a][b];let m=dual.mass[a][b];if !g.is_finite()||!m.is_finite(){return Err(StepError::ExponentialDomain);}s.j[a][b]=g;s.mass[a][b]=m;')
    graph=once(graph,'if g!=0.{s.j[i][j]+=g;}if m!=0.{s.mass[i][j]+=m;}', 'if g!=0.{s.j[i][j]+=g;if !s.j[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}if m!=0.{s.mass[i][j]+=m;if !s.mass[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}')
    graph=once(graph,'s.dc.iter().chain(s.dq.iter()).chain(s.j.iter().flatten()).chain(s.mass.iter().flatten())', 's.dc.iter().chain(s.dq.iter())')
    voice=(ROOT/'crates/rf-d-circuit/src/hybrid_schur_voice.rs').read_text(encoding='utf8').replace('dual_voice_chain.rs','prepared_voice_chain.rs')
    probe=(ROOT/'tools/hybrid_schur_probe.rs').read_text(encoding='utf8').replace('hybrid_nominal_voice.rs','hybrid_schur_voice.rs')
    # Both controls use the Schur API; only their electrical graph differs.
    probe=probe.replace('#[cfg(condensed)]\n#[path="../crates/rf-d-circuit/src/hybrid_schur_voice.rs"]', '#[cfg(condensed)]\n#[path="../crates/rf-d-circuit/src/prepared_hybrid_voice.rs"]')
    probe=probe.replace('#[cfg(condensed)] type Workspace=circuit::Workspace;\n#[cfg(not(condensed))] type Workspace=();','type Workspace=circuit::Workspace;')
    probe=once(probe,'    #[cfg(condensed)] {circuit::advance(w,p,s,c,h)}\n    #[cfg(not(condensed))] {let _=w;circuit::advance(p,s,c,h)}','    circuit::advance(w,p,s,c,h)')
    probe=once(probe,'    #[cfg(condensed)] let mut workspace=Workspace::new();\n    #[cfg(not(condensed))] let mut workspace=();','    let mut workspace=Workspace::new();')
    probe=probe.replace('#[cfg(condensed)] {let z=workspace.statistics;', '{let z=workspace.statistics;')
    from refine_hybrid_stamp import transform
    audio,chain,graph,voice=transform(audio,chain,graph,voice)
    graph=once(graph,'dual_contour_loaded.rs','prepared_contour_residual.rs')
    graph=once(graph,'contour::parts(', 'contour::parts::<FULL>(')
    from prepare_contour_residual import derive as contours
    cs=contours();key='crates/rf-d-circuit/src/prepared_contour_residual.rs'
    from prepare_shared_candidate import transform as share
    chain,cs[key],graph=share(chain,cs[key],graph)
    from prepare_sparse_low import transform as low
    vk='crates/rf-d-circuit/src/prepared_volume_residual.rs';fk='crates/rf-d-circuit/src/prepared_filter_residual.rs'
    audio,chain,cs[key],cs[vk],cs[fk]=low(audio,chain,cs[key],cs[vk],cs[fk])
    return {**cs,'crates/rf-d-circuit/src/prepared_audio_stamp.rs':audio,'crates/rf-d-circuit/src/prepared_chain_charge.rs':chain,'crates/rf-d-circuit/src/prepared_voice_chain.rs':graph,'crates/rf-d-circuit/src/prepared_hybrid_voice.rs':voice,'tools/hybrid_stamp_probe.rs':probe}
def main():
    before=ROOT/'evidence/hybrid_stamp_before01.json';assert not before.exists();previous='evidence/hybrid_schur_tests01.json'
    write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in derive().items():
        p=ROOT/n;assert not p.exists();p.write_text(s,encoding='utf8',newline='\n')
    print('PREPARED_STAMP_GENERATED')
if __name__=='__main__':main()
