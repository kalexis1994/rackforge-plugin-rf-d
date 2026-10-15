"""Fuse current Radau assembly, structural inspection and Schur extraction."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once

def derive():
    s=(ROOT/'crates/rf-d-circuit/src/hybrid_schur_solver.rs').read_text(encoding='utf8')
    a=s.index('    fn initialize(&mut self,j:',s.index('impl<const N:usize> Block'))
    b=s.index('        self.lu.perm=',a)
    s=s[:a]+'''    fn factor(&mut self,outer:&mut [[f64;4];4])->Result<(),StepError>{
'''+s[b:]
    a=s.index('    fn initialize(&mut self,j:',s.index('impl Sparse'))
    b=s.index('    fn residual(',a);s=s[:a]+s[b:]
    s=once(s,'pub const M:usize=236;', '''pub const M:usize=236;
pub const N:usize=118;
#[derive(Clone,Copy)]
pub struct Stage<'a>{pub dc:&'a [[f64;N];N],pub mass:&'a [[f64;N];N]}
// Physical partition only. Every coefficient is inspected on every solve.
const OWNER:[usize;M]=std::array::from_fn_const_placeholder;
'''.replace('std::array::from_fn_const_placeholder', '{let mut x=[0;M];let mut k=0;while k<M{x[k]=match k%N{0..=53=>1,54..=55=>0,_=>2};k+=1;}x}'))
    s=once(s,'const CONTOUR:', '''const LOCAL:[usize;M]={let mut x=[0;M];let mut k=0;while k<M{let a=k%N;let stage=k/N;x[k]=match a{0..=53=>a+54*stage,54..=55=>a-54+2*stage,_=>a-56+62*stage};k+=1;}x};
const CONTOUR:''')
    a=s.index('    fn initialize(&mut self,j:',s.index('impl Workspace'))
    b=s.index('    fn correction(',a)
    s=s[:a]+'''    fn initialize(&mut self,stages:[Stage;2],weights:[[f64;2];2])->Result<(),StepError>{
        self.contour.lu.a=[[0.;108];108];self.contour.border=[[0.;4];108];self.contour.cross=[[0.;108];4];
        self.audio.lu.a=[[0.;124];124];self.audio.border=[[0.;4];124];self.audio.cross=[[0.;124];4];
        self.outer.a=[[0.;4];4];let mut count=0;
        for i in 0..2{for a in 0..N{
            let row=i*N+a;self.sparse.row[row]=count;self.sparse.floor[row]=0.;
            for jj in 0..2{let stage=&stages[jj];let mass=&stage.mass[a];let dc=&stage.dc[a];let weight=weights[i][jj];
                for b in 0..N{
                    let value=weight*mass[b]+if i==jj{dc[b]}else{0.};
                    if !value.is_finite(){return Err(StepError::InvalidInput);}if value==0.{continue;}
                    let col=jj*N+b;let ri=LOCAL[row];let ci=LOCAL[col];
                    match (OWNER[row],OWNER[col]){
                        (1,1)=>self.contour.lu.a[ri][ci]=value,
                        (2,2)=>self.audio.lu.a[ri][ci]=value,
                        (0,0)=>self.outer.a[ri][ci]=value,
                        (1,0)=>self.contour.border[ri][ci]=value,
                        (2,0)=>self.audio.border[ri][ci]=value,
                        (0,1)=>self.contour.cross[ri][ci]=value,
                        (0,2)=>self.audio.cross[ri][ci]=value,
                        _=>return Err(StepError::InvalidInput),
                    }
                    if count==CAPACITY{return Err(StepError::InvalidInput);}
                    self.sparse.column[count]=col as u16;self.sparse.value[count]=value;
                    self.sparse.floor[row]+=value.abs()*2e-9;count+=1;
                }
            }
        }}self.sparse.row[M]=count;
        self.contour.factor(&mut self.outer.a)?;self.audio.factor(&mut self.outer.a)?;self.outer.factor()
    }
    // Read the actual retained coefficients, after the same production initializer.
    #[cfg(laboratory)]
    pub fn coefficients(&mut self,s:[Stage;2],w:[[f64;2];2])->Result<[[f64;M];M],StepError>{
        self.initialize(s,w)?;let mut j=[[0.;M];M];
        for i in 0..M{for z in self.sparse.row[i]..self.sparse.row[i+1]{j[i][self.sparse.column[z] as usize]=self.sparse.value[z];}}Ok(j)
    }
'''+s[b:]
    s=once(s,'fn correction(&self,j:&[[f64;M];M],b:', 'fn correction(&self,b:')
    s=once(s,'let _=j;let mut rhs=', 'let mut rhs=')
    s=once(s,'pub fn solve(&mut self,j:&[[f64;M];M],b:', 'pub fn solve(&mut self,stages:[Stage;2],weights:[[f64;2];2],b:')
    s=once(s,'self.initialize(j)?;', 'self.initialize(stages,weights)?;')
    s=s.replace('self.correction(j,','self.correction(')
    v=(ROOT/'crates/rf-d-circuit/src/stage_hybrid_voice.rs').read_text(encoding='utf8')
    v=once(v,'hybrid_schur_solver.rs','direct_hybrid_solver.rs')
    v=once(v,'fn gaussian(w:&mut Workspace,a:&[[f64;M];M],r:[f64;M])->Result<[f64;M],StepError>{w.solve(a,r)}', '''fn gaussian(w:&mut Workspace,s:&[Parts;2],r:[f64;M])->Result<[f64;M],StepError>{
    w.solve([solver::Stage{dc:&s[0].j,mass:&s[0].mass},solver::Stage{dc:&s[1].j,mass:&s[1].mass}],B,r)
}''')
    a=v.index('    let jacobian = ');b=v.index('    let evaluate_residual = ',a);v=v[:a]+v[b:]
    v=once(v,'let (r, j, stages) = system(d)?;\n        let direction = gaussian(w,&j, r.map(|v| -v))?;', 'let s=evaluate(d)?;let r=residual(&s);let stages=[s[0].now,s[1].now];\n        let direction = gaussian(w,&s, r.map(|v| -v))?;')
    v=once(v,'gaussian(w,&jacobian(&ss),','gaussian(w,&ss,')
    probe=(ROOT/'tools/hybrid_stage_probe.rs').read_text(encoding='utf8')
    probe=once(probe,'prepared_hybrid_voice.rs','stage_hybrid_voice.rs')
    probe=once(probe,'#[path="../crates/rf-d-circuit/src/stage_hybrid_voice.rs"] mod circuit;\n#[path=', '#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"] mod circuit;\n#[path=')
    from refine_hybrid_direct import transform,prepared_scales
    s=prepared_scales(transform(s))
    return {'crates/rf-d-circuit/src/direct_hybrid_solver.rs':s,'crates/rf-d-circuit/src/direct_hybrid_voice.rs':v,'tools/hybrid_direct_probe.rs':probe}

def main():
    before=ROOT/'evidence/hybrid_direct_before01.json';assert not before.exists()
    sources=derive();assert not any((ROOT/n).exists() for n in sources)
    previous='evidence/hybrid_stage_tests01.json'
    write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in sources.items():(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
