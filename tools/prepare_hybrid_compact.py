"""Compact current DC/mass into sorted rows, preserving the electrical evaluator."""
from prepare_dual_chain import ROOT
from prepare_hybrid_stamp import once
def derive():
    s=(ROOT/'crates/rf-d-circuit/src/direct_hybrid_solver.rs').read_text(encoding='utf8')
    a=s.index('#[derive(Clone,Copy)]');b=s.index('// Physical partition',a)
    s=s[:a]+'''const STAGE_CAPACITY:usize=2048;
// Private, immutable sparse rows; rebuilt from all actual entries each stage.
pub struct Matrix{row:[usize;N+1],column:[u8;STAGE_CAPACITY],dc:[f64;STAGE_CAPACITY],mass:[f64;STAGE_CAPACITY]}
impl Matrix{
    #[inline(always)]
    pub fn new(dc:&[[f64;N];N],mass:&[[f64;N];N])->Result<Self,StepError>{
        let mut s=Self{row:[0;N+1],column:[0;STAGE_CAPACITY],dc:[0.;STAGE_CAPACITY],mass:[0.;STAGE_CAPACITY]};let mut count=0;
        for i in 0..N{s.row[i]=count;for k in 0..N{
            let g=dc[i][k];let m=mass[i][k];if !g.is_finite()||!m.is_finite(){return Err(StepError::InvalidInput);}
            if g==0.&&m==0.{continue;}if count==STAGE_CAPACITY{return Err(StepError::InvalidInput);}
            s.column[count]=k as u8;s.dc[count]=g;s.mass[count]=m;count+=1;
        }}s.row[N]=count;Ok(s)
    }
    #[cfg(laboratory)] pub fn coefficients(&self)->([[f64;N];N],[[f64;N];N]){
        let mut g=[[0.;N];N];let mut m=g;for i in 0..N{for z in self.row[i]..self.row[i+1]{let k=self.column[z] as usize;g[i][k]=self.dc[z];m[i][k]=self.mass[z];}}(g,m)
    }
    #[cfg(laboratory)] pub fn nonzeros(&self)->usize{self.row[N]}
}
'''+s[b:]
    s=s.replace('stages:[Stage;2]','stages:[&Matrix;2]').replace('s:[Stage;2]','s:[&Matrix;2]')
    a=s.index('            for jj in 0..2{let stage=&stages[jj];');b=s.index('                    if !value.is_finite()',a)
    s=s[:a]+'''            for jj in 0..2{let stage=stages[jj];let weight=weights[i][jj];
                for z in stage.row[a]..stage.row[a+1]{
                    let b=stage.column[z] as usize;
                    let value=weight*stage.mass[z]+if i==jj{stage.dc[z]}else{0.};
'''+s[b:]
    v=(ROOT/'crates/rf-d-circuit/src/direct_hybrid_voice.rs').read_text(encoding='utf8').replace('direct_hybrid_solver.rs','compact_hybrid_solver.rs')
    a=v.index('fn gaussian(');b=v.index('pub struct Pair',a)
    v=v[:a]+'''struct Prepared{dc:[f64;N],dq:[f64;N],now:State,matrix:solver::Matrix}
#[inline(always)]
fn prepare(s:&Parts)->Result<Prepared,StepError>{let matrix=solver::Matrix::new(&s.j,&s.mass)?;Ok(Prepared{dc:s.dc,dq:s.dq,now:s.now,matrix})}
fn gaussian(w:&mut Workspace,s:&[Prepared;2],r:[f64;M])->Result<[f64;M],StepError>{w.solve([&s[0].matrix,&s[1].matrix],B,r)}
'''+v[b:]
    v=once(v,'Result<[Parts;2],StepError>{\n        Ok([parts::<true>(p,old,d[0],c,h,p.time+h/3.)?,parts::<true>(p,old,d[1],c,h,p.time+h)?])','Result<[Prepared;2],StepError>{\n        Ok([prepare(&parts::<true>(p,old,d[0],c,h,p.time+h/3.)?)?,prepare(&parts::<true>(p,old,d[1],c,h,p.time+h)?)?])')
    v=once(v,'let residual = |s:&[Parts;2]|','let residual = |s:&[Prepared;2]|')
    p=(ROOT/'tools/hybrid_direct_probe.rs').read_text(encoding='utf8');p=once(p,'stage_hybrid_voice.rs','direct_hybrid_voice.rs')
    p=once(p,'#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"] mod circuit;\n#[path=','#[path="../crates/rf-d-circuit/src/compact_hybrid_voice.rs"] mod circuit;\n#[path=')
    return {'crates/rf-d-circuit/src/compact_hybrid_solver.rs':s,'crates/rf-d-circuit/src/compact_hybrid_voice.rs':v,'tools/hybrid_compact_probe.rs':p}
if __name__=='__main__':
    for n,s in derive().items():assert not (ROOT/n).exists();(ROOT/n).write_text(s,encoding='utf8',newline='\n')
