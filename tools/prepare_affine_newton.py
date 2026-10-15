"""One borrowed preparation; eliminate the actual seven algebraic rows per stage."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
def derive():
    solver=(ROOT/'crates/rf-d-circuit/src/ladder_voice_solver.rs').read_text(encoding='utf8')
    solver=once(solver,'    pub fn solve(&mut self,stages:[Stage;2],weights:[[f64;2];2],b:[f64;M])->Result<[f64;M],StepError>{\n        if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}self.initialize(stages,weights)?;', '''    pub fn prepare(&mut self,stages:[Stage;2],weights:[[f64;2];2])->Result<Prepared<'_>,StepError>{
        self.initialize(stages,weights)?;Ok(Prepared{workspace:self})
    }
    pub fn solve(&mut self,stages:[Stage;2],weights:[[f64;2];2],b:[f64;M])->Result<[f64;M],StepError>{
        let mut prepared=self.prepare(stages,weights)?;prepared.solve(b)
    }
    fn solve_rhs(&mut self,b:[f64;M])->Result<[f64;M],StepError>{
        if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}''')
    solver=once(solver,'            r[i]=-(high+low);let error=', '            if !high.is_finite()||!low.is_finite()||!scale.is_finite(){return Err(StepError::InvalidInput);}\n            r[i]=-(high+low);let error=')
    solver+='''
/// Exclusive borrow prevents another initialization while this matrix is in use.
pub struct Prepared<'a>{workspace:&'a mut Workspace}
impl Prepared<'_>{
    pub fn solve(&mut self,b:[f64;M])->Result<[f64;M],StepError>{self.workspace.solve_rhs(b)}
    #[cfg(laboratory)]pub fn coefficients(&self)->[[f64;M];M]{let mut j=[[0.;M];M];for i in 0..M{for z in self.workspace.sparse.row[i]..self.workspace.sparse.row[i+1]{j[i][self.workspace.sparse.column[z]as usize]=self.workspace.sparse.value[z];}}j}
}
'''
    voice=(ROOT/'crates/rf-d-circuit/src/split_ladder_voice.rs').read_text(encoding='utf8')
    voice=once(voice,'#[path="ladder_voice_solver.rs"] pub mod solver;', '#[path="affine_newton_solver.rs"] pub mod solver;\n#[path="affine_newton_frame.rs"] pub mod affine;')
    voice=once(voice,'pub struct Stage{pub physical:Parts,pub delta:State,pub j:[[f64;R];R],pub mass:[[f64;R];R],pub local:ladder::Solution}', 'pub struct Stage{pub physical:Parts,pub delta:State,pub local:ladder::Solution}')
    a=voice.index('    let mut j=[[0.;R];R];');b=voice.index('    binding::merge::<FULL>',a)
    voice=voice[:a]+voice[b:];voice=once(voice,'Ok(Stage{physical,delta,j,mass,local})','Ok(Stage{physical,delta,local})')
    a=voice.index('pub struct Workspace{');b=voice.index('pub fn radau(',a)
    voice=voice[:a]+'''pub struct Workspace{
    pub reduced:solver::Workspace,pub statistics:solver::Statistics,pub affine_statistics:affine::Statistics,
    dc:[[[f64;R];R];2],mass:[[[f64;R];R];2],physical:affine::Sparse,
    #[cfg(laboratory)]pub original:full::Workspace,
}
impl Workspace{
    pub const fn new()->Self{Self{reduced:solver::Workspace::new(),statistics:solver::Statistics{solves:0,refinements:0,max_initial_backward:0.,max_final_backward:0.,max_nonzeros:0},affine_statistics:affine::Statistics::new(),dc:[[[0.;R];R];2],mass:[[[0.;R];R];2],physical:affine::Sparse::new(),#[cfg(laboratory)]original:full::Workspace::new()}}
    pub fn prepare<'w,'s>(&'w mut self,s:&'s[Stage;2])->Result<affine::Frame<'w,'s>,StepError>{
        self.physical.initialize(s,B)?;
        let local=[affine::Local::new(&s[0].physical.j,&s[0].physical.mass)?,affine::Local::new(&s[1].physical.j,&s[1].physical.mass)?];
        for i in 0..2{local[i].coefficients(&s[i].physical.j,&s[i].physical.mass,&mut self.dc[i],&mut self.mass[i])?;}
        let reduced=self.reduced.prepare([solver::Stage{dc:&self.dc[0],mass:&self.mass[0]},solver::Stage{dc:&self.dc[1],mass:&self.mass[1]}],B)?;
        Ok(affine::Frame::new(reduced,local,&self.physical,s,&mut self.affine_statistics))
    }
}
pub fn direction(w:&mut Workspace,s:&[Stage;2],rhs:[f64;M])->Result<([f64;RM],[f64;M]),StepError>{
    let result={let mut prepared=w.prepare(s)?;prepared.solve(rhs)};w.statistics=w.reduced.statistics;result
}
#[cfg(laboratory)]
pub fn original_direction(w:&mut Workspace,s:&[Stage;2],rhs:[f64;M])->Result<[f64;M],StepError>{
    w.original.solve([full::solver::Stage{dc:&s[0].physical.j,mass:&s[0].physical.mass},full::solver::Stage{dc:&s[1].physical.j,mass:&s[1].physical.mass}],B,rhs)
}
'''+voice[b:]
    a=voice.index('        let(dy,dx)=direction(');b=voice.index('        let mut found=false;',a)
    voice=voice[:a]+'''        let(dy,dx)=direction(w,&s,r.map(|v|-v))?;let correction=norm(dx);
        if magnitude<=1e-12&&correction<=2e-9{return Ok(Pair{delta:[s[0].delta,s[1].delta],stages:[s[0].physical.now,s[1].physical.now],residual_a:magnitude,correction_v:correction,iterations:iteration});}
'''+voice[b:]
    voice=once(voice,'norm(original_direction(w,&ss,rr.map(|v|-v))?)','norm(direction(w,&ss,rr.map(|v|-v))?.1)')
    probe=(ROOT/'tools/split_ladder_probe.rs').read_text(encoding='utf8');probe=once(probe,'src/split_ladder_voice.rs','src/affine_newton_voice.rs')
    probe=once(probe,'    assert_eq!(heap,0);', '''    #[cfg(condensed)]{let a=workspace.affine_statistics;write!(w,"AFFINE,{},{},{},{},{}",a.preparations,a.physical_solves,a.reduced_rhs,a.physical_refinements,a.maximum_nonzeros).unwrap();vals(&mut w,[a.maximum_initial_backward,a.maximum_final_backward]);writeln!(w).unwrap();}
    assert_eq!(heap,0);''')
    return {'crates/rf-d-circuit/src/affine_newton_solver.rs':solver,'crates/rf-d-circuit/src/affine_newton_voice.rs':voice,'tools/affine_newton_probe.rs':probe}
def main():
    path=ROOT/'evidence/affine_newton_before01.json';out=derive();assert not path.exists() and not any((ROOT/n).exists() for n in out)
    previous='evidence/split_ladder_tests01.json';names=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write(path,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    for n,s in out.items():(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
