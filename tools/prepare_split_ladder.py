"""Derive a parent without ladder DC and a kernel retaining its final stamp."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
def derive():
    audio=(ROOT/'crates/rf-d-circuit/src/prepared_audio_stamp.rs').read_text(encoding='utf8')
    a=audio.index('    // Ladder, Fig.9-11.');b=audio.index('    // Recovery Q8/Q6/Q7/Q5.',a)
    audio=audio[:a]+'    // Ladder DC belongs exclusively to the local reconstruction kernel.\n'+audio[b:]
    charge=(ROOT/'crates/rf-d-circuit/src/prepared_chain_charge.rs').read_text(encoding='utf8');charge=once(charge,'prepared_audio_stamp.rs','split_parent_audio.rs')
    parent=(ROOT/'crates/rf-d-circuit/src/prepared_voice_chain.rs').read_text(encoding='utf8');parent=once(parent,'prepared_chain_charge.rs','split_parent_charge.rs')
    parent=once(parent,'pub use contour::Controls;','pub use super::full::{State,Controls,Parts};')
    a=parent.index('#[derive(Clone,Copy,Debug,PartialEq)]\npub struct State');b=parent.index('pub fn sources(',a)
    parent=parent[:a]+'''// Use the original physical types directly; no intermediate 118x118 result adapter.
fn contour_state(s:State)->contour::State{contour::State{high:std::array::from_fn(|k|s.high[k]),low:std::array::from_fn(|k|s.low[k]),optional:s.optional}}
fn chain_state(s:State)->chain_charge::State{chain_charge::State{high:std::array::from_fn(|k|s.high[chain_index(k)]),low:std::array::from_fn(|k|s.low[chain_index(k)])}}
fn contour_controls(c:Controls)->contour::Controls{contour::Controls{key:c.key,short:c.short,optional:c.optional}}
'''+parent[b:]
    for name in ['old','delta','now']:
        parent=parent.replace(name+'.chain()','chain_state('+name+')').replace(name+'.contour()','contour_state('+name+')')
    parent=once(parent,'contour_state(delta),c,h,','contour_state(delta),contour_controls(c),h,')
    kernel=(ROOT/'crates/rf-d-circuit/src/ladder_algebraic.rs').read_text(encoding='utf8')
    a=kernel.index('pub fn covector(');b=kernel.index('#[derive(Clone,Copy)]\npub struct Model',a)
    kernel=kernel[:a]+'''// Immutable support of the declared coordinate transformation, never learned from a scene.
const SUPPORT:[[(usize,f64);2];16]={let mut out=[[(16,0.);2];16];let mut i=0;
    while i<16{let mut a=0;let mut n=0;while a<16{if T[a][i]!=0.{out[i][n]=(a,T[a][i]);n+=1;}a+=1;}i+=1;}out};
pub fn covector(f:&[f64;16])->[f64;16]{std::array::from_fn(|i|{
    let mut v=0.;for(a,s)in SUPPORT[i]{if a<16{v+=s*f[a];}}v
})}
pub fn congruence(j:&[[f64;16];16])->[[f64;16];16]{
    let right:[[f64;16];16]=std::array::from_fn(|a|std::array::from_fn(|i|{
        let mut v=0.;for(b,s)in SUPPORT[i]{if b<16{v+=j[a][b]*s;}}v
    }));
    std::array::from_fn(|i|std::array::from_fn(|k|{
        let mut v=0.;for(a,s)in SUPPORT[i]{if a<16{v+=s*right[a][k];}}v
    }))
}
'''+kernel[b:]
    kernel=once(kernel,'Ok(Evaluation{nodes,f,j,source:', 'Ok(Evaluation{nodes,f,j,dc:s.dc,physical_j:s.j,source:')
    kernel=once(kernel,'pub struct Evaluation{pub nodes:Nodes,','pub struct Evaluation{pub dc:[f64;16],pub physical_j:[[f64;16];16],pub nodes:Nodes,')
    kernel=once(kernel,'pub struct Solution{','pub struct Solution{\n    pub dc:[f64;16],pub physical_j:[[f64;16];16],')
    kernel=once(kernel,'Ok(Solution{z,nodes:e.nodes,','Ok(Solution{dc:e.dc,physical_j:e.physical_j,z,nodes:e.nodes,')
    voice=(ROOT/'crates/rf-d-circuit/src/ladder_voice.rs').read_text(encoding='utf8')
    voice=once(voice,'#[path="ladder_algebraic.rs"] pub mod ladder;','#[path="split_ladder_kernel.rs"] pub mod ladder;\n#[path="split_parent_voice.rs"] pub mod parent;\n#[path="split_ladder_binding.rs"] pub mod binding;')
    voice=once(voice,'pub struct Parameters{full:full::Parameters,','pub struct Parameters{parent:parent::Parameters,full:full::Parameters,')
    voice=once(voice,'Ok(Self{model:ladder::Model::new(p.circuit)?,','Ok(Self{parent:parent::Parameters::new(p)?,model:ladder::Model::new(p.circuit)?,')
    a=voice.index('    let physical=parts::<FULL>');b=voice.index('    Ok(Stage{physical,delta,j,mass,local})',a)
    voice=voice[:a]+'''    let mut physical=binding::parent_parts::<FULL>(p.parent,p.time,old,delta,c,h,t)?;
    binding::validate_parent::<FULL>(&physical)?;
    let mut j=[[0.;R];R];let mut mass=[[0.;R];R];
    if FULL{
        for a in 0..R{let row=RETAINED[a];let sr=sign(row);
            for b in 0..R{let col=RETAINED[b];j[a][b]=sr*sign(col)*physical.j[row][col];mass[a][b]=sr*sign(col)*physical.mass[row][col];}
        }
        for a in 0..9{for b in 0..9{j[Y[a]][Y[b]]+=local.reaction_j[a][b];}}
        if j.iter().flatten().chain(mass.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
    }
    binding::merge::<FULL>(&mut physical,&local)?;
'''+voice[b:]
    probe=(ROOT/'tools/ladder_voice_probe.rs').read_text(encoding='utf8');probe=once(probe,'src/ladder_voice.rs','src/split_ladder_voice.rs')
    return {'crates/rf-d-circuit/src/split_parent_audio.rs':audio,'crates/rf-d-circuit/src/split_parent_charge.rs':charge,
            'crates/rf-d-circuit/src/split_parent_voice.rs':parent,'crates/rf-d-circuit/src/split_ladder_kernel.rs':kernel,
            'crates/rf-d-circuit/src/split_ladder_voice.rs':voice,'tools/split_ladder_probe.rs':probe}
def main():
    out=derive();path=ROOT/'evidence/split_ladder_before01.json';assert not path.exists() and not any((ROOT/n).exists() for n in out)
    previous='evidence/ladder_voice_tests01.json';names=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write(path,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    for n,s in out.items():(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
