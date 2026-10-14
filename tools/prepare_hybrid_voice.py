"""Freeze the previous admission and derive a laboratory hybrid integration."""
import base64,json,subprocess
from prepare_dual_chain import ROOT,sha,write

def generate():
    before=ROOT/'evidence/hybrid_voice_before01.json'
    if not before.exists():
        previous='evidence/vco_phase_tests01.json'
        write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    source=(ROOT/'crates/rf-d-circuit/src/dual_chain.rs').read_text(encoding='utf8')
    body=source[source.index('pub struct Pair {'):]
    body=body.replace('if let Ok((rr, _, _)) = system(trial) {\n                if max(rr) < norm {', 'if let Ok((rr, jj, _)) = system(trial) {\n                let weak = norm <= 1e-12 && max(rr) <= 1e-12\n                    && max(gaussian(jj, rr.map(|v| -v))?) < corr;\n                if max(rr) < norm || weak {')
    body=body.replace('(2e-7 + 2e-7 * fine.high[k].abs())','(500e-6 + 1e-4 * fine.high[k].abs())')
    body=body.replace('h <= 0. || !old.valid()', 'h <= 0. || h > 1e-3 || !old.valid()')
    body=body.replace('Parameters{time:p.time+h/2.,..p}', '{let mut next=p;next.time+=h/2.;next}')
    header='''//! Laboratory nominal phase VCO joined to the complete 118-node loaded chain.
//! HYBRID_VOZ_PROTOCOLO: branch at 40 ms, unchanged contour/filter/VCA charges.
//! Derived solver substitutions: tools/prepare_hybrid_voice.py.
use crate::StepError;
use rf_d_circuit::chain_charge;
#[path="dual_voice_chain.rs"] mod graph;
#[path="hybrid_phase_source.rs"] pub mod phase;
pub use graph::{Parameters,State,Controls,Parts,N,M,B,currents};
pub fn parts(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{
    let mut s=graph::parts(p,old,delta,c,h,t)?;
    // All old mixer branches are OFF. R6/R45 belong once to this VCO port.
    let port=phase::observe(t,s.now.high[116]).map_err(|_|StepError::InvalidInput)?;
    let y=port.admittance_s[3][3];
    s.dc[116]+=port.current_a[3]+y*s.now.low[116];
    s.j[116][116]+=y;
    Ok(s)
}
fn max<const S:usize>(x:[f64;S])->f64{x.into_iter().fold(0.,|a,v|a.max(v.abs()))}
fn gaussian<const S:usize>(a:[[f64;S];S],r:[f64;S])->Result<[f64;S],StepError>{
    rf_d_circuit::block_decay_voice::solve_linear_extent(a,r)
}
'''
    target=ROOT/'crates/rf-d-circuit/src/hybrid_nominal_voice.rs'
    assert not target.exists()
    target.write_text(header+body,encoding='utf8',newline='\n')
    print('HYBRID_SOURCE',sha(target))
if __name__=='__main__':generate()
