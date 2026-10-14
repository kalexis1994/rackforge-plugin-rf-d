//! Exact two-stage dynamic condensation, HYBRID_SCHUR_PROTOCOLO.
//! 108 contour + 124 audio interior unknowns, four shared port unknowns.
use crate::StepError;
pub const M:usize=236;
pub const PORTS:[usize;4]=[54,55,172,173];
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
            let mut pivot=col;let mut best=0.;for row in col..N{let q=self.a[row][col].abs()/scale[row];if q>best{best=q;pivot=row;}}
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
struct Block<const N:usize>{lu:Lu<N>,border:[[f64;4];N],cross:[[f64;N];4]}
impl<const N:usize> Block<N>{
    const fn new()->Self{Self{lu:Lu::new(),border:[[0.;4];N],cross:[[0.;N];4]}}
    fn initialize(&mut self,j:&[[f64;M];M],ids:[usize;N],outer:&mut [[f64;4];4])->Result<(),StepError>{
        for i in 0..N{for k in 0..N{self.lu.a[i][k]=j[ids[i]][ids[k]];}for p in 0..4{self.border[i][p]=j[ids[i]][PORTS[p]];self.cross[p][i]=j[PORTS[p]][ids[i]];}}
        self.lu.perm=std::array::from_fn(|i|i);let mut scale=[0_f64;N];
        for i in 0..N{scale[i]=self.lu.a[i].iter().fold(0_f64,|s,x|s.max(x.abs()));if scale[i]==0.{return Err(StepError::SingularJacobian);}}
        for col in 0..N{
            let mut pivot=col;let mut best=0.;for row in col..N{let q=self.lu.a[row][col].abs()/scale[row];if q>best{best=q;pivot=row;}}
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
    fn initialize(&mut self,j:&[[f64;M];M])->Result<(),StepError>{
        let mut n=0;for i in 0..M{self.row[i]=n;self.floor[i]=0.;for k in 0..M{
            let a=j[i][k];if !a.is_finite(){return Err(StepError::InvalidInput);}if a==0.{continue;}
            let owner=|v:usize|match v%118{0..=53=>1,54..=55=>0,_=>2};
            if owner(i)!=0&&owner(k)!=0&&owner(i)!=owner(k){return Err(StepError::InvalidInput);}
            if n==CAPACITY{return Err(StepError::InvalidInput);}self.column[n]=k as u16;self.value[n]=a;self.floor[i]+=a.abs()*2e-9;n+=1;
        }}self.row[M]=n;Ok(())
    }
    fn residual(&self,b:&[f64;M],d:&[f64;M])->Result<([f64;M],f64),StepError>{
        let mut r=[0.;M];let mut worst=0_f64;
        for i in 0..M{let mut high=-b[i];let mut low=0.;let mut scale=b[i].abs()+self.floor[i];
            for z in self.row[i]..self.row[i+1]{let k=self.column[z] as usize;let a=self.value[z];let p=a*d[k];let s=high+p;
                low+=if high.abs()>=p.abs(){(high-s)+p}else{(p-s)+high};low+=a.mul_add(d[k],-p);high=s;scale+=a.abs()*d[k].abs();
            }
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
    fn initialize(&mut self,j:&[[f64;M];M])->Result<(),StepError>{
        self.sparse.initialize(j)?;
        self.outer.a=std::array::from_fn(|i|std::array::from_fn(|k|j[PORTS[i]][PORTS[k]]));
        self.contour.initialize(j,CONTOUR,&mut self.outer.a)?;self.audio.initialize(j,AUDIO,&mut self.outer.a)?;self.outer.factor()
    }
    fn correction(&self,j:&[[f64;M];M],b:[f64;M])->Result<[f64;M],StepError>{
        let _=j;let mut rhs=PORTS.map(|i|b[i]);let c=self.contour.forward(CONTOUR.map(|i|b[i]),&mut rhs);let a=self.audio.forward(AUDIO.map(|i|b[i]),&mut rhs);
        let p=self.outer.solve(rhs)?;let mut d=[0.;M];for i in 0..4{d[PORTS[i]]=p[i];}
        let c=self.contour.reconstruct(c,p);let a=self.audio.reconstruct(a,p);
        for i in 0..108{d[CONTOUR[i]]=c[i];}for i in 0..124{d[AUDIO[i]]=a[i];}
        if d.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(d)
    }
    pub fn solve(&mut self,j:&[[f64;M];M],b:[f64;M])->Result<[f64;M],StepError>{
        if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}self.initialize(j)?;
        let mut d=self.correction(j,b)?;let(mut r,mut metric)=self.sparse.residual(&b,&d)?;let initial=metric;
        for n in 0..=MAX_REFINEMENTS{
            if metric<=BACKWARD_GATE{self.statistics.solves+=1;self.statistics.refinements+=n;self.statistics.max_initial_backward=self.statistics.max_initial_backward.max(initial);self.statistics.max_final_backward=self.statistics.max_final_backward.max(metric);self.statistics.max_nonzeros=self.statistics.max_nonzeros.max(self.sparse.row[M]);return Ok(d);}
            if n==MAX_REFINEMENTS{return Err(StepError::IterationBudget);}let e=self.correction(j,r)?;for k in 0..M{d[k]+=e[k];}
            let(rr,next)=self.sparse.residual(&b,&d)?;if next>=metric&&next>BACKWARD_GATE{return Err(StepError::NoDecrease);}r=rr;metric=next;
        }unreachable!()
    }
}
