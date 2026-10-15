"""Replace global stage matrices with current component incidences; unchanged laws."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
def derive():
    prefix='crates/rf-d-circuit/src/'
    graph=(ROOT/(prefix+'prepared_voice_chain.rs')).read_text(encoding='utf8')
    graph=once(graph,'use crate::StepError;','use crate::StepError;\nuse super::incidence::{Row,Tangent};')
    graph=once(graph,'pub struct Parts{pub dc:[f64;N],pub j:[[f64;N];N],pub dq:[f64;N],pub mass:[[f64;N];N],pub now:State}', 'pub struct Parts{pub dc:[f64;N],pub dq:[f64;N],pub now:State,pub tangent:Tangent}')
    a=graph.index('    let mut s=Parts{');b=graph.index('    if s.dc.iter()',a)
    graph=graph[:a]+'''    let mut s=Parts{dc:[0.;N],dq:[0.;N],now,tangent:Tangent::new()};
    for a in 0..56{s.dc[a]=dual.dc[a];s.dq[a]=dual.dq[a];}
    for a in 0..68{if(62..66).contains(&a){continue;}let i=chain_index(a);s.dc[i]+=audio.dc[a];s.dq[i]+=audio.charge_over_h[a];}
    if FULL{
        // Source map, not measured support. Every actual component entry is read.
        const AUDIO_ROW:[usize;N]={let mut ids=[68;N];let mut k=0;while k<68{if k<62||k>=66{ids[chain_index(k)]=k;}k+=1;}ids};
        for a in 0..N{let mut row=Row::new();
            if a<56{for b in 0..56{row.set(b,dual.j[a][b],dual.mass[a][b])?;}}
            let audio_row=AUDIO_ROW[a];if audio_row<68{for b in 0..68{row.add(chain_index(b),audio.dc_jacobian[audio_row][b],audio.mass_over_h[audio_row][b])?;}}
            s.tangent.push_row(a,&mut row)?;
        }
    }
'''+graph[b:]
    voice=(ROOT/(prefix+'direct_hybrid_voice.rs')).read_text(encoding='utf8')
    voice=once(voice,'#[path="direct_hybrid_solver.rs"]','#[path="incidence_hybrid_solver.rs"]');voice=once(voice,'#[path="prepared_voice_chain.rs"]','#[path="incidence_voice_chain.rs"]')
    voice=once(voice,'use crate::StepError;','use crate::StepError;\n#[path="incidence_matrix.rs"]pub mod incidence;')
    voice=once(voice,'if FULL{s.j[116][116]+=y;}','if FULL{s.tangent.add(116,116,y,0.)?;}')
    voice=once(voice,'solver::Stage{dc:&s[0].j,mass:&s[0].mass},solver::Stage{dc:&s[1].j,mass:&s[1].mass}', 'solver::Stage{tangent:&s[0].tangent},solver::Stage{tangent:&s[1].tangent}')
    solver=(ROOT/(prefix+'direct_hybrid_solver.rs')).read_text(encoding='utf8')
    solver=once(solver,"pub struct Stage<'a>{pub dc:&'a [[f64;N];N],pub mass:&'a [[f64;N];N]}","pub struct Stage<'a>{pub tangent:&'a super::incidence::Tangent}")
    solver=once(solver,'if weights.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}', 'if weights.iter().flatten().any(|v|!v.is_finite())||stages.iter().any(|s|!s.tangent.complete()){return Err(StepError::InvalidInput);}')
    a=solver.index('            for jj in 0..2{let stage=');b=solver.index('                    let col=jj*N+b;',a)
    solver=solver[:a]+'''            for jj in 0..2{let weight=weights[i][jj];
                for(b,dc,mass)in stages[jj].tangent.entries(a){
                    if mass==0.&&(i!=jj||dc==0.){continue;}
                    let value=weight*mass+if i==jj{dc}else{0.};
                    if !value.is_finite(){return Err(StepError::InvalidInput);}if value==0.{continue;}
'''+solver[b:]
    # Keep the original matrix coefficients and arithmetic, including strict finite scales.
    solver=once(solver,'            r[i]=-(high+low);let error=', '            if !high.is_finite()||!low.is_finite()||!scale.is_finite(){return Err(StepError::InvalidInput);}\n            r[i]=-(high+low);let error=')
    solver+='''
#[cfg(laboratory)]impl Workspace{pub fn check_direction(&mut self,s:[Stage;2],w:[[f64;2];2],b:[f64;M],d:[f64;M])->Result<f64,StepError>{self.initialize(s,w)?;Ok(self.sparse.residual(&b,&d)?.1)}}
'''
    probe=(ROOT/'tools/split_ladder_probe.rs').read_text(encoding='utf8');probe=once(probe,'src/split_ladder_voice.rs','src/incidence_hybrid_voice.rs')
    return {prefix+'incidence_voice_chain.rs':graph,prefix+'incidence_hybrid_voice.rs':voice,prefix+'incidence_hybrid_solver.rs':solver,'tools/incidence_voice_probe.rs':probe}
def main():
    path=ROOT/'evidence/incidence_voice_before01.json';assert not path.exists();previous='evidence/execution_cost_tests01.json'
    write(path,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in derive().items():assert not (ROOT/n).exists();(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
