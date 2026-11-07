//! Modified Newton BE preconditioner; all twelve laws in residual.
//! Experimental static-cutoff hybrid. Eighteen charges, twelve recovery/input junctions.
//! Own RF-D Ebers-Moll law; remaining devices locally linear, no voice admission.
#[path="recovery_port_input_data.rs"]mod data;
const GAMMA:f64=0.2928932188134524756;
#[derive(Clone,Copy,Debug)]
pub struct State{pub index:usize,pub q:[f64;18],pub input:f64,pub history:[f64;18],pub defects:[f64;12]}
#[derive(Clone,Copy,Debug)]pub enum Error{Input,RootBudget,Domain,Singular}
#[derive(Clone,Copy)]pub struct Ports{pub bus_v:f64,pub base_v:f64,pub j7_v:f64,pub panel_a:f64}
impl State{pub fn dc(index:usize)->Result<Self,Error>{if index>=3{return Err(Error::Input)}Ok(Self{index,q:[0.;18],input:0.,history:[0.;18],defects:[0.;12]})}}
pub fn law(index:usize,z:[f64;12])->Result<([f64;12],[f64;12]),Error>{
 let mut n=[0.;12];let mut slope=[0.;12];for k in 0..12{let x=z[k];if !x.is_finite()||x.abs()>40.{return Err(Error::Domain)}
 let(v,em1)=if x.abs()<0.125{
 let poly=1./2.+x*(1./6.+x*(1./24.+x*(1./120.+x*(1./720.+x*(1./5040.+x*(1./40320.+x*(1./362880.+x*(1./3628800.+x*(1./39916800.+x*(1./479001600.))))))))));
 let v=x*x*poly;(v,x+v)
 }else{let em1=x.exp_m1();(em1-x,em1)};
 n[k]=data::IEXP[index][k]*v;slope[k]=data::IEXP[index][k]*em1;}Ok((n,slope))
}
fn solve(mut a:[[f64;6];6],mut b:[f64;6])->Result<[f64;6],Error>{
 for k in 0..6{let mut pivot=k;for j in k+1..6{if a[j][k].abs()>a[pivot][k].abs(){pivot=j}}if a[pivot][k].abs()<1e-28{return Err(Error::Singular)}a.swap(k,pivot);b.swap(k,pivot);for j in k+1..6{let f=a[j][k]/a[k][k];a[j][k]=0.;for l in k+1..6{a[j][l]-=f*a[k][l];}b[j]-=f*b[k];}}
 let mut x=[0.;6];for k in(0..6).rev(){let mut v=b[k];for j in k+1..6{v-=a[k][j]*x[j];}x[k]=v/a[k][k];}Ok(x)
}
#[inline]
pub fn stage(index:usize,q:[f64;18],u:f64,budget:usize)->Result<([f64;18],[f64;12],[f64;12],usize,f64),Error>{
 let mut zp=[0.;12];for k in 0..12{zp[k]=data::ZU[index][k]*u;for j in 0..18{zp[k]+=data::ZH[index][k][j]*q[j];}}let mut z=zp;
 for iteration in 0..budget{let(n,slope)=law(index,z)?;let mut r=[0.;12];let mut maximum=0_f64;for k in 0..12{r[k]=z[k]-zp[k];for j in 0..12{r[k]+=data::P[index][k][j]*n[j];}maximum=maximum.max(r[k].abs());}
  if maximum<=2e-13{let mut next=[0.;18];for k in 0..18{next[k]=data::QU[index][k]*u;for j in 0..18{next[k]+=data::QH[index][k][j]*q[j];}for j in 0..12{next[k]-=data::QD[index][k][j]*n[j];}if !next[k].is_finite(){return Err(Error::Domain)}}return Ok((next,n,z,iteration+1,maximum));}
  let a=std::array::from_fn(|k|std::array::from_fn(|j|if k==j{1.+data::P[index][2*k][2*j]*slope[2*j]}else{data::P[index][2*k][2*j]*slope[2*j]}));let even=solve(a,std::array::from_fn(|k|r[2*k]))?;for k in 0..6{let mut odd=r[2*k+1];for j in 0..6{odd-=data::P[index][2*k+1][2*j]*slope[2*j]*even[j];}z[2*k]-=even[k];z[2*k+1]-=odd;}
 }Err(Error::RootBudget)
}
fn node(s:State,k:usize)->f64{let mut x=data::XU[s.index][k]*s.input;for j in 0..18{x+=data::XH[s.index][k][j]*s.history[j];}for j in 0..12{x-=data::XD[s.index][k][j]*s.defects[j];}data::DC[s.index][k]+x}
pub fn nodes(s:State)->[f64;68]{std::array::from_fn(|k|node(s,k))}
pub fn step(s:&mut State,u:f64)->Result<Ports,Error>{step_with_budget(s,u,12)}
pub fn step_with_budget(s:&mut State,u:f64,budget:usize)->Result<Ports,Error>{
 if s.index>=3||!u.is_finite()||u.abs()>0.13||!s.input.is_finite()||s.q.iter().any(|v|!v.is_finite()){return Err(Error::Input)}
 let(first,_,_,_,_)=stage(s.index,s.q,(1.-GAMMA)*s.input+GAMMA*u,budget)?;let history=std::array::from_fn(|k|s.q[k]+(1.-GAMMA)/GAMMA*(first[k]-s.q[k]));let(q,defects,_,_,_)=stage(s.index,history,u,budget)?;
 let candidate=State{index:s.index,q,input:u,history,defects};let bus=node(candidate,66);let base=node(candidate,6);let j7=node(candidate,61);if !bus.is_finite()||!base.is_finite()||!j7.is_finite(){return Err(Error::Domain)}
 *s=candidate;Ok(Ports{bus_v:bus,base_v:base,j7_v:j7,panel_a:(bus-0.5*u)/39250.})
}
