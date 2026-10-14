"""Derive a workspace-bound Schur variant, leaving the admitted voice intact."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
def generate():
    before=ROOT/'evidence/hybrid_schur_before01.json';assert not before.exists()
    previous='evidence/hybrid_voice_tests01.json'
    write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    source=(ROOT/'crates/rf-d-circuit/src/hybrid_nominal_voice.rs').read_text(encoding='utf8')
    source=source.replace('//! Derived solver substitutions: tools/prepare_hybrid_voice.py.', '//! Exact dynamic Schur variant: tools/prepare_hybrid_schur.py.\n#[path="hybrid_schur_solver.rs"] pub mod solver;\npub use solver::Workspace;')
    source=source.replace('fn gaussian<const S:usize>(a:[[f64;S];S],r:[f64;S])->Result<[f64;S],StepError>{\n    rf_d_circuit::block_decay_voice::solve_linear_extent(a,r)\n}', 'fn gaussian(w:&mut Workspace,a:[[f64;M];M],r:[f64;M])->Result<[f64;M],StepError>{w.solve(a,r)}')
    source=source.replace('pub fn radau(p:', 'pub fn radau(w:&mut Workspace,p:').replace('pub fn advance(p:', 'pub fn advance(w:&mut Workspace,p:')
    source=source.replace('gaussian(j,','gaussian(w,j,').replace('gaussian(jj,','gaussian(w,jj,')
    source=source.replace('= radau(p,','= radau(w,p,').replace('= radau({','= radau(w,{')
    from refine_hybrid_schur import transform
    source=transform(source)
    target=ROOT/'crates/rf-d-circuit/src/hybrid_schur_voice.rs';assert not target.exists();target.write_text(source,encoding='utf8',newline='\n')
    probe=(ROOT/'tools/hybrid_voice_probe.rs').read_text(encoding='utf8')
    probe=probe.replace('#[path="../crates/rf-d-circuit/src/hybrid_nominal_voice.rs"] mod circuit;', '#[cfg(not(condensed))]\n#[path="../crates/rf-d-circuit/src/hybrid_nominal_voice.rs"] mod circuit;\n#[cfg(condensed)]\n#[path="../crates/rf-d-circuit/src/hybrid_schur_voice.rs"] mod circuit;')
    probe=probe.replace('fn main()->Result<(),String>{', '''#[cfg(condensed)] type Workspace=circuit::Workspace;
#[cfg(not(condensed))] type Workspace=();
fn step(w:&mut Workspace,p:Parameters,s:&mut State,c:Controls,h:f64)->Result<Accepted,StepError>{
    #[cfg(condensed)] {circuit::advance(w,p,s,c,h)}
    #[cfg(not(condensed))] {let _=w;circuit::advance(p,s,c,h)}
}
fn main()->Result<(),String>{
    #[cfg(condensed)] let mut workspace=Workspace::new();
    #[cfg(not(condensed))] let mut workspace=();''')
    probe=probe.replace('advance(p','step(&mut workspace,p')
    # Undo replacement inside the baseline wrapper introduced above.
    probe=probe.replace('circuit::step(&mut workspace,p,s,c,h)', 'circuit::advance(p,s,c,h)')
    probe=probe.replace('assert_eq!(heap,0);', '''#[cfg(condensed)] {let z=workspace.statistics;write!(w,"SOLVER,{},{},{}",z.solves,z.refinements,z.max_nonzeros).unwrap();vals(&mut w,[z.max_initial_backward,z.max_final_backward]);writeln!(w).unwrap();}
    assert_eq!(heap,0);''')
    target=ROOT/'tools/hybrid_schur_probe.rs';assert not target.exists();target.write_text(probe,encoding='utf8',newline='\n')
    print('HYBRID_SCHUR_GENERATED')
if __name__=='__main__':generate()
