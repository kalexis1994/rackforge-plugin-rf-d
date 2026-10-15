//! Actual full Newton correction via an affine Schur reconstruction.
//! A frame borrows its stages and factors exclusively; no cross-state factor cache.
use super::{ladder,solver,Stage,N,M,R,RM,Z,RETAINED};
use crate::StepError;
fn sign(n:usize)->f64{if(67..=69).contains(&n){-1.}else{1.}}
fn right(k:usize)->Option<usize>{if k>=4{Some(67+k-4)}else{None}}
pub struct Local{
    factor:ladder::Factor,cross:[[f64;7];R],response:[[f64;R];7],columns:[usize;R],count:usize,
}
impl Local{
    pub fn new(j:&[[f64;N];N],mass:&[[f64;N];N])->Result<Self,StepError>{
        if j.iter().flatten().chain(mass.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
        let mut zz=[[0.;7];7];let mut zy=[[0.;R];7];let mut cross=[[0.;7];R];
        for k in 0..7{
            for a in 0..N{
                let column=mass[a][Z[k]]+right(k).map_or(0.,|q|mass[a][q]);
                let row=mass[Z[k]][a]+right(k).map_or(0.,|q|mass[q][a]);
                if column!=0.||row!=0.{return Err(StepError::InvalidInput);}
            }
            for l in 0..7{
                let a=j[Z[k]][Z[l]]+right(l).map_or(0.,|q|j[Z[k]][q]);
                let b=right(k).map_or(0.,|row|j[row][Z[l]]+right(l).map_or(0.,|q|j[row][q]));zz[k][l]=a+b;
            }
            for y in 0..R{let a=RETAINED[y];let s=sign(a);
                zy[k][y]=s*(j[Z[k]][a]+right(k).map_or(0.,|row|j[row][a]));
                cross[y][k]=s*(j[a][Z[k]]+right(k).map_or(0.,|col|j[a][col]));
            }
        }
        if cross.iter().flatten().chain(zy.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
        let factor=ladder::Factor::new(zz)?;let mut response=[[0.;R];7];let mut columns=[0;R];let mut count=0;
        for y in 0..R{let b=std::array::from_fn(|k|-zy[k][y]);if b.iter().any(|v|*v!=0.){
            let x=factor.solve(b)?;for k in 0..7{response[k][y]=x[k];}columns[count]=y;count+=1;
        }}
        Ok(Self{factor,cross,response,columns,count})
    }
    pub fn coefficients(&self,j:&[[f64;N];N],m:&[[f64;N];N],dc:&mut [[f64;R];R],mass:&mut [[f64;R];R])->Result<(),StepError>{
        for a in 0..R{let row=RETAINED[a];for b in 0..R{let col=RETAINED[b];let s=sign(row)*sign(col);dc[a][b]=s*j[row][col];mass[a][b]=s*m[row][col];}
            for col in self.columns[..self.count].iter().copied(){let correction=(0..7).map(|k|self.cross[a][k]*self.response[k][col]).sum::<f64>();dc[a][col]+=correction;}
        }
        if dc.iter().flatten().chain(mass.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}Ok(())
    }
    fn rhs(&self,b:&[f64;N])->Result<([f64;R],[f64;7]),StepError>{
        let rz=std::array::from_fn(|k|b[Z[k]]+right(k).map_or(0.,|q|b[q]));let particular=self.factor.solve(rz)?;
        let by=std::array::from_fn(|a|sign(RETAINED[a])*b[RETAINED[a]]-(0..7).map(|k|self.cross[a][k]*particular[k]).sum::<f64>());
        if by.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}Ok((by,particular))
    }
    fn reconstruct(&self,y:[f64;R],particular:[f64;7])->Result<[f64;N],StepError>{
        let mut x=[0.;N];for a in 0..R{x[RETAINED[a]]=sign(RETAINED[a])*y[a];}
        for k in 0..7{let dz=particular[k]+self.columns[..self.count].iter().map(|col|self.response[k][*col]*y[*col]).sum::<f64>();
            x[Z[k]]=dz;if let Some(q)=right(k){x[q]+=dz;}}
        if x.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(x)
    }
}
const CAPACITY:usize=4096;
pub struct Sparse{rows:[usize;M+1],columns:[u16;CAPACITY],values:[f64;CAPACITY],floor:[f64;M]}
impl Sparse{
    pub const fn new()->Self{Self{rows:[0;M+1],columns:[0;CAPACITY],values:[0.;CAPACITY],floor:[0.;M]}}
    pub fn initialize(&mut self,s:&[Stage;2],weights:[[f64;2];2])->Result<(),StepError>{
        if weights.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
        let mut count=0;
        for i in 0..2{for a in 0..N{let row=i*N+a;self.rows[row]=count;self.floor[row]=0.;
            for stage in 0..2{for b in 0..N{
                let mass=s[stage].physical.mass[a][b];let dc=s[stage].physical.j[a][b];
                if !mass.is_finite()||!dc.is_finite(){return Err(StepError::InvalidInput);}
                if mass==0.&&(i!=stage||dc==0.){continue;}
                let value=weights[i][stage]*mass+if i==stage{dc}else{0.};if !value.is_finite(){return Err(StepError::InvalidInput);}if value==0.{continue;}
                if count==CAPACITY{return Err(StepError::InvalidInput);}self.columns[count]=(stage*N+b)as u16;self.values[count]=value;count+=1;self.floor[row]+=value.abs()*2e-9;
            }}
        }}self.rows[M]=count;Ok(())
    }
    pub fn residual(&self,b:&[f64;M],d:&[f64;M])->Result<([f64;M],f64),StepError>{
    let _clock=crate::execution_clock::enter(13);
        if b.iter().chain(d.iter()).any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
        let mut result=[0.;M];let mut worst=0_f64;
        for i in 0..M{let mut high=-b[i];let mut low=0.;let mut scale=b[i].abs()+self.floor[i];
            for n in self.rows[i]..self.rows[i+1]{let a=self.values[n];let k=self.columns[n]as usize;let p=a*d[k];let sum=high+p;
                low+=if high.abs()>=p.abs(){(high-sum)+p}else{(p-sum)+high};low+=a.mul_add(d[k],-p);high=sum;scale+=a.abs()*d[k].abs();
            }
            if !high.is_finite()||!low.is_finite()||!scale.is_finite(){return Err(StepError::InvalidInput);}
            result[i]=-(high+low);let metric=if scale==0.{if result[i]!=0.{return Err(StepError::NoDecrease);}0.}else{result[i].abs()/scale};
            if !metric.is_finite(){return Err(StepError::InvalidInput);}worst=worst.max(metric);
        }Ok((result,worst))
    }
    #[cfg(laboratory)]pub fn coefficients(&self)->[[f64;M];M]{let mut a=[[0.;M];M];for i in 0..M{for z in self.rows[i]..self.rows[i+1]{a[i][self.columns[z]as usize]=self.values[z];}}a}
}
#[derive(Clone,Copy)]
pub struct Statistics{pub preparations:usize,pub physical_solves:usize,pub reduced_rhs:usize,pub physical_refinements:usize,pub maximum_nonzeros:usize,pub maximum_initial_backward:f64,pub maximum_final_backward:f64}
impl Statistics{pub const fn new()->Self{Self{preparations:0,physical_solves:0,reduced_rhs:0,physical_refinements:0,maximum_nonzeros:0,maximum_initial_backward:0.,maximum_final_backward:0.}}}
pub struct Frame<'w,'s>{reduced:solver::Prepared<'w>,local:[Local;2],physical:&'w Sparse,_stages:&'s[Stage;2],statistics:&'w mut Statistics}
impl<'w,'s> Frame<'w,'s>{
    #[cfg(laboratory)]pub fn physical_coefficients(&self)->[[f64;M];M]{self.physical.coefficients()}
    #[cfg(laboratory)]pub fn reduced_coefficients(&self)->[[f64;RM];RM]{self.reduced.coefficients()}
    #[cfg(laboratory)]pub fn backward(&self,b:[f64;M],x:[f64;M])->Result<f64,StepError>{Ok(self.physical.residual(&b,&x)?.1)}
    pub fn new(reduced:solver::Prepared<'w>,local:[Local;2],physical:&'w Sparse,s:&'s[Stage;2],statistics:&'w mut Statistics)->Self{
        statistics.preparations+=1;Self{reduced,local,physical,_stages:s,statistics}
    }
    fn apply(&mut self,b:[f64;M])->Result<([f64;RM],[f64;M]),StepError>{
        if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
        let mut rhs=[0.;RM];let mut particular=[[0.;7];2];
        for i in 0..2{let(r,p)=self.local[i].rhs(&std::array::from_fn(|k|b[i*N+k]))?;rhs[i*R..(i+1)*R].copy_from_slice(&r);particular[i]=p;}
        let phase_clock=crate::execution_clock::enter(12);let dy=self.reduced.solve(rhs)?;drop(phase_clock);self.statistics.reduced_rhs+=1;let mut dx=[0.;M];
        for i in 0..2{let x=self.local[i].reconstruct(std::array::from_fn(|k|dy[i*R+k]),particular[i])?;dx[i*N..(i+1)*N].copy_from_slice(&x);}
        Ok((dy,dx))
    }
    pub fn solve(&mut self,b:[f64;M])->Result<([f64;RM],[f64;M]),StepError>{
    let _clock=crate::execution_clock::enter(11);
        let(mut dy,mut dx)=self.apply(b)?;let(mut residual,mut backward)=self.physical.residual(&b,&dx)?;let initial=backward;
        for n in 0..=3{
            if backward<=1e-11{self.statistics.physical_solves+=1;self.statistics.physical_refinements+=n;self.statistics.maximum_initial_backward=self.statistics.maximum_initial_backward.max(initial);self.statistics.maximum_final_backward=self.statistics.maximum_final_backward.max(backward);self.statistics.maximum_nonzeros=self.statistics.maximum_nonzeros.max(self.physical.rows[M]);return Ok((dy,dx));}
            if n==3{return Err(StepError::IterationBudget);}
            let(ey,ex)=self.apply(residual)?;for k in 0..RM{dy[k]+=ey[k];}for k in 0..M{dx[k]+=ex[k];}
            let(r,next)=self.physical.residual(&b,&dx)?;if next>=backward&&next>1e-11{return Err(StepError::NoDecrease);}residual=r;backward=next;
        }unreachable!()
    }
}
