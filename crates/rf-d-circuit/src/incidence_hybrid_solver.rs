//! Exact two-stage dynamic condensation, HYBRID_SCHUR_PROTOCOLO.
//! 108 contour + 124 audio interior unknowns, four shared port unknowns.
use crate::StepError;
pub const M:usize=236;
pub const N:usize=118;
#[derive(Clone,Copy)]
pub struct Stage<'a>{pub tangent:&'a super::incidence::Tangent}
// Physical partition only. Every coefficient is inspected on every solve.
const OWNER:[usize;M]={let mut x=[0;M];let mut k=0;while k<M{x[k]=match k%N{0..=53=>1,54..=55=>0,_=>2};k+=1;}x};

pub const PORTS:[usize;4]=[54,55,172,173];
const LOCAL:[usize;M]={let mut x=[0;M];let mut k=0;while k<M{let a=k%N;let stage=k/N;x[k]=match a{0..=53=>a+54*stage,54..=55=>a-54+2*stage,_=>a-56+62*stage};k+=1;}x};
const CONTOUR:[usize;108]={let mut x=[0;108];let mut i=0;while i<108{x[i]=if i<54{i}else{i+64};i+=1;}x};
const AUDIO:[usize;124]={let mut x=[0;124];let mut i=0;while i<124{x[i]=if i<62{i+56}else{i+112};i+=1;}x};
pub const BACKWARD_GATE:f64=1e-11;
pub const MAX_REFINEMENTS:usize=3;
struct Lu<const N:usize>{a:[[f64;N];N],perm:[usize;N]}
impl<const N:usize> Lu<N>{
    const fn new()->Self{Self{a:[[0.;N];N],perm:[0;N]}}
    fn factor(&mut self)->Result<(),StepError>{
        self.perm=std::array::from_fn(|i|i);let mut scale=[0_f64;N];
        for i in 0..N{scale[i]=self.a[i].iter().fold(0_f64,|s,x|s.max(x.abs()));if scale[i]==0.{return Err(StepError::SingularJacobian);}}
        for col in 0..N{
            let mut pivot=col;let mut best=0.;for row in col..N{let value=self.a[row][col];if value==0.{continue;}let q=value.abs()/scale[row];if q>best{best=q;pivot=row;}}
            if best<1e-12{return Err(StepError::SingularJacobian);}self.a.swap(col,pivot);self.perm.swap(col,pivot);scale.swap(col,pivot);
            let end=self.a[col].iter().rposition(|v|*v!=0.).unwrap()+1;
            let(head,tail)=self.a.split_at_mut(col+1);let current=&head[col];
            for row in tail{if row[col]==0.{continue;}let f=row[col]/current[col];row[col]=f;
                for k in col+1..end{row[k]-=f*current[k];}
            }
        }
        if self.a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(())
    }
    fn solve(&self,b:[f64;N])->Result<[f64;N],StepError>{
        let mut x=[0.;N];for i in 0..N{let mut v=b[self.perm[i]];for k in 0..i{v-=self.a[i][k]*x[k];}x[i]=v;}
        for i in (0..N).rev(){let mut v=x[i];for k in i+1..N{v-=self.a[i][k]*x[k];}x[i]=v/self.a[i][i];}
        if x.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(x)
    }
}
// Store the triangular border rather than solving four response RHS per block.
// Cross is the exterior elimination factor in column order; history is in RHS.
struct Block<const N:usize>{scale:[f64;N],lu:Lu<N>,border:[[f64;4];N],cross:[[f64;N];4]}
impl<const N:usize> Block<N>{
    const fn new()->Self{Self{scale:[0.;N],lu:Lu::new(),border:[[0.;4];N],cross:[[0.;N];4]}}
    fn factor(&mut self,outer:&mut [[f64;4];4])->Result<(),StepError>{
        self.lu.perm=std::array::from_fn(|i|i);let mut scale=self.scale;
        if scale.iter().any(|v|*v==0.){return Err(StepError::SingularJacobian);}
        for col in 0..N{
            let mut pivot=col;let mut best=0.;for row in col..N{let value=self.lu.a[row][col];if value==0.{continue;}let q=value.abs()/scale[row];if q>best{best=q;pivot=row;}}
            if best<1e-12{return Err(StepError::SingularJacobian);}self.lu.a.swap(col,pivot);self.lu.perm.swap(col,pivot);self.border.swap(col,pivot);scale.swap(col,pivot);
            let end=self.lu.a[col].iter().rposition(|v|*v!=0.).unwrap()+1;let diagonal=self.lu.a[col][col];
            let(head,tail)=self.lu.a.split_at_mut(col+1);let row=&head[col];let upper=self.border[col];
            for (offset,current) in tail.iter_mut().enumerate(){if current[col]==0.{continue;}let factor=current[col]/diagonal;current[col]=factor;
                for k in col+1..end{current[k]-=factor*row[k];}for p in 0..4{self.border[col+1+offset][p]-=factor*upper[p];}
            }
            for p in 0..4{let factor=self.cross[p][col]/diagonal;self.cross[p][col]=factor;
                for k in col+1..end{self.cross[p][k]-=factor*row[k];}for q in 0..4{outer[p][q]-=factor*upper[q];}
            }
        }
        if self.lu.a.iter().flatten().chain(self.border.iter().flatten()).chain(self.cross.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(())
    }
    fn forward(&self,b:[f64;N],rhs:&mut [f64;4])->[f64;N]{
        let mut x=[0.;N];for i in 0..N{let mut v=b[self.lu.perm[i]];for k in 0..i{v-=self.lu.a[i][k]*x[k];}x[i]=v;}
        for p in 0..4{for k in 0..N{rhs[p]-=self.cross[p][k]*x[k];}}x
    }
    fn reconstruct(&self,mut x:[f64;N],p:[f64;4])->[f64;N]{
        for i in (0..N).rev(){let mut v=x[i];for k in i+1..N{v-=self.lu.a[i][k]*x[k];}for k in 0..4{v-=self.border[i][k]*p[k];}x[i]=v/self.lu.a[i][i];}x
    }
}
const CAPACITY:usize=4096;
struct Sparse{row:[usize;M+1],column:[u16;CAPACITY],value:[f64;CAPACITY],floor:[f64;M]}
impl Sparse{
    const fn new()->Self{Self{row:[0;M+1],column:[0;CAPACITY],value:[0.;CAPACITY],floor:[0.;M]}}
    fn residual(&self,b:&[f64;M],d:&[f64;M])->Result<([f64;M],f64),StepError>{
        let mut r=[0.;M];let mut worst=0_f64;
        for i in 0..M{let mut high=-b[i];let mut low=0.;let mut scale=b[i].abs()+self.floor[i];
            for z in self.row[i]..self.row[i+1]{let k=self.column[z] as usize;let a=self.value[z];let p=a*d[k];let s=high+p;
                low+=if high.abs()>=p.abs(){(high-s)+p}else{(p-s)+high};low+=a.mul_add(d[k],-p);high=s;scale+=a.abs()*d[k].abs();
            }
            if !high.is_finite()||!low.is_finite()||!scale.is_finite(){return Err(StepError::InvalidInput);}
            r[i]=-(high+low);let error=if scale==0.{if r[i]!=0.{return Err(StepError::NoDecrease);}0.}else{r[i].abs()/scale};
            if !error.is_finite(){return Err(StepError::InvalidInput);}worst=worst.max(error);
        }Ok((r,worst))
    }
}
#[derive(Clone,Copy,Default,Debug)]
pub struct Statistics{pub solves:usize,pub refinements:usize,pub max_initial_backward:f64,pub max_final_backward:f64,pub max_nonzeros:usize}
pub struct Workspace{contour:Block<108>,audio:Block<124>,outer:Lu<4>,sparse:Sparse,pub statistics:Statistics}
impl Workspace{
    pub const fn new()->Self{Self{contour:Block::new(),audio:Block::new(),outer:Lu::new(),sparse:Sparse::new(),statistics:Statistics{solves:0,refinements:0,max_initial_backward:0.,max_final_backward:0.,max_nonzeros:0}}}
    fn initialize(&mut self,stages:[Stage;2],weights:[[f64;2];2])->Result<(),StepError>{
        if weights.iter().flatten().any(|v|!v.is_finite())||stages.iter().any(|s|!s.tangent.complete()){return Err(StepError::InvalidInput);}
        self.contour.scale=[0.;108];self.audio.scale=[0.;124];
        self.contour.lu.a=[[0.;108];108];self.contour.border=[[0.;4];108];self.contour.cross=[[0.;108];4];
        self.audio.lu.a=[[0.;124];124];self.audio.border=[[0.;4];124];self.audio.cross=[[0.;124];4];
        self.outer.a=[[0.;4];4];let mut count=0;
        for i in 0..2{for a in 0..N{
            let row=i*N+a;self.sparse.row[row]=count;self.sparse.floor[row]=0.;
            for jj in 0..2{let weight=weights[i][jj];
                for(b,dc,mass)in stages[jj].tangent.entries(a){
                    if mass==0.&&(i!=jj||dc==0.){continue;}
                    let value=weight*mass+if i==jj{dc}else{0.};
                    if !value.is_finite(){return Err(StepError::InvalidInput);}if value==0.{continue;}
                    let col=jj*N+b;let ri=LOCAL[row];let ci=LOCAL[col];
                    match (OWNER[row],OWNER[col]){
                        (1,1)=>{self.contour.lu.a[ri][ci]=value;self.contour.scale[ri]=self.contour.scale[ri].max(value.abs());},
                        (2,2)=>{self.audio.lu.a[ri][ci]=value;self.audio.scale[ri]=self.audio.scale[ri].max(value.abs());},
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
    fn correction(&self,b:[f64;M])->Result<[f64;M],StepError>{
        let mut rhs=PORTS.map(|i|b[i]);let c=self.contour.forward(CONTOUR.map(|i|b[i]),&mut rhs);let a=self.audio.forward(AUDIO.map(|i|b[i]),&mut rhs);
        let p=self.outer.solve(rhs)?;let mut d=[0.;M];for i in 0..4{d[PORTS[i]]=p[i];}
        let c=self.contour.reconstruct(c,p);let a=self.audio.reconstruct(a,p);
        for i in 0..108{d[CONTOUR[i]]=c[i];}for i in 0..124{d[AUDIO[i]]=a[i];}
        if d.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(d)
    }
    pub fn solve(&mut self,stages:[Stage;2],weights:[[f64;2];2],b:[f64;M])->Result<[f64;M],StepError>{
        if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}self.initialize(stages,weights)?;
        let mut d=self.correction(b)?;let(mut r,mut metric)=self.sparse.residual(&b,&d)?;let initial=metric;
        for n in 0..=MAX_REFINEMENTS{
            if metric<=BACKWARD_GATE{self.statistics.solves+=1;self.statistics.refinements+=n;self.statistics.max_initial_backward=self.statistics.max_initial_backward.max(initial);self.statistics.max_final_backward=self.statistics.max_final_backward.max(metric);self.statistics.max_nonzeros=self.statistics.max_nonzeros.max(self.sparse.row[M]);return Ok(d);}
            if n==MAX_REFINEMENTS{return Err(StepError::IterationBudget);}let e=self.correction(r)?;for k in 0..M{d[k]+=e[k];}
            let(rr,next)=self.sparse.residual(&b,&d)?;if next>=metric&&next>BACKWARD_GATE{return Err(StepError::NoDecrease);}r=rr;metric=next;
        }unreachable!()
    }
}

#[cfg(laboratory)]impl Workspace{pub fn check_direction(&mut self,s:[Stage;2],w:[[f64;2];2],b:[f64;M],d:[f64;M])->Result<f64,StepError>{self.initialize(s,w)?;Ok(self.sparse.residual(&b,&d)?.1)}}
