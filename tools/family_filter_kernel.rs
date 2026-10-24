//! Full 68-node chain plus phase. Fixed laboratory controls, FAMILIA_FILTRO.
use rf_d_circuit::{chain_charge::{self,Parameters,State as Chain,N as CN},StepError};
#[path="vco_cv_load_linear.rs"]mod linear;
use linear::solve_linear_sparse;
#[path="family_mixer_family128.rs"]mod family;
pub const N:usize=69;pub const BUS:usize=66;pub const PHASE:usize=68;
#[derive(Clone,Copy,Debug,PartialEq)]pub struct State{pub high:[f64;N],pub low:[f64;N]}
fn sum(a:f64,b:f64)->(f64,f64){let s=a+b;let v=s-a;(s,(a-(s-v))+(b-v))}
impl State{
 pub fn new(high:[f64;N])->Self{Self{high,low:[0.;N]}}
 pub fn advanced(self,d:[f64;N])->Self{let mut s=self;for k in 0..N{let(a,b)=sum(s.high[k],d[k]);let(c,e)=sum(s.low[k],b);let(a,b)=sum(a,c);(s.high[k],s.low[k])=sum(a,b+e);}s}
 pub fn chain(self)->Chain{Chain{high:std::array::from_fn(|k|self.high[k]),low:std::array::from_fn(|k|self.low[k])}}
 pub fn value(self,k:usize)->f64{self.high[k]+self.low[k]}
 pub fn valid(self)->bool{(0..N).all(|k|self.high[k].is_finite()&&self.low[k].is_finite()&&sum(self.high[k],self.low[k])==(self.high[k],self.low[k])&&self.value(k).abs()<40.)}
}
pub struct Stamp{pub r:[f64;N],pub j:[[f64;N];N],pub candidate:State}
#[derive(Clone,Copy)]pub struct Accepted{pub state:State,pub residual_ratio:f64,pub correction_ratio:f64,pub iterations:usize}
fn weights(cv:f64)->[f64;4]{std::array::from_fn(|i|{let mut w=1.;for j in 0..4{if i!=j{w*=(cv-family::CV[j])/(family::CV[i]-family::CV[j]);}}w})}
fn source(cv:f64,s:State,mean:bool)->Result<(f64,f64,f64,f64,f64),StepError>{
 let bus=s.value(BUS);let phase=s.value(PHASE).rem_euclid(1.);let q=family::evaluate(cv,bus,phase).map_err(|_|StepError::InvalidInput)?;
 let w=weights(cv);let u=(bus+0.125)/0.25;
 if mean{let mut saw=0.;let mut ds=0.;for i in 0..4{let a=crate::data::COEFFICIENTS[i][0][0][0][0];let b=crate::data::COEFFICIENTS[i][1][0][0][0];saw+=w[i]*((1.-u)*a+u*b);ds+=w[i]*(b-a)/0.25;}return Ok(((bus-0.5*saw)/39250.,(1.-0.5*ds)/39250.,0.,q.values[0],q.dbus[0]));}
 let mut slope=0.;for n in 1..=128{let(sn,cs)=(std::f64::consts::TAU*n as f64*phase).sin_cos();for i in 0..4{for j in 0..2{let a=crate::data::COEFFICIENTS[i][j][0][n];slope+=w[i]*if j==0{1.-u}else{u}*2.*std::f64::consts::TAU*n as f64*(-a[0]*sn-a[1]*cs);}}}
 Ok((q.values[11],q.dbus[11],-0.5*slope/39250.,q.values[0],q.dbus[0]))
}
pub fn current(cv:f64,s:State)->Result<f64,StepError>{Ok(source(cv,s,false)?.0)}
pub fn linearize(p:Parameters,cv:f64,old:State,delta:State,h:f64,dc:bool)->Result<Stamp,StepError>{
 if !old.valid()||!delta.valid(){return Err(StepError::InvalidInput);}
 let a=chain_charge::linearize_compensated(p,[0.;5],old.chain(),delta.chain(),h)?;let now=old.advanced(delta.high).advanced(delta.low);if !now.valid(){return Err(StepError::InvalidInput);}
 let q=source(cv,now,dc)?;let mut r=[0.;N];let mut j=[[0.;N];N];
 if dc{for k in 0..CN{r[k]=a.dc[k];j[k][..CN].copy_from_slice(&a.dc_jacobian[k]);}r[BUS]+=q.0;j[BUS][BUS]+=q.1;r[PHASE]=delta.value(PHASE);j[PHASE][PHASE]=1.;}
 else{let b=chain_charge::linearize_compensated(p,[0.;5],old.chain(),Chain::from_nodes([0.;CN]),h)?;let previous=source(cv,old,false)?;
  for k in 0..CN{r[k]=a.dc[k]+b.dc[k]+2.*a.charge_over_h[k];for l in 0..CN{j[k][l]=a.dc_jacobian[k][l]+2.*a.mass_over_h[k][l];}}
  r[BUS]+=q.0+previous.0;j[BUS][BUS]+=q.1;j[BUS][PHASE]+=q.2;
  r[PHASE]=delta.value(PHASE)-h*0.5*(q.3+previous.3);j[PHASE][PHASE]=1.;j[PHASE][BUS]=-h*0.5*q.4;
 }
 Ok(Stamp{r,j,candidate:now})
}
fn residual(r:&[f64;N])->f64{r.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if k==PHASE{1e-11}else{1e-13}))}
fn correction(r:&[f64;N])->f64{r.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if k==PHASE{1e-11}else{2e-9}))}
pub fn solve(p:Parameters,cv:f64,old:State,h:f64,dc:bool,budget:usize)->Result<Accepted,StepError>{
 if !(1..=64).contains(&budget){return Err(StepError::InvalidInput);}
 let mut delta=State::new([0.;N]);
 for iteration in 1..=budget{let s=linearize(p,cv,old,delta,h,dc)?;let norm=residual(&s.r);let d=solve_linear_sparse(s.j,s.r.map(|x|-x))?;let corr=correction(&d);
  if norm<=1.&&corr<=1.{return Ok(Accepted{state:s.candidate,residual_ratio:norm,correction_ratio:corr,iterations:iteration});}
  let mut found=false;
  for power in 0..24{let alpha=2_f64.powi(-power);let trial=delta.advanced(d.map(|x|x*alpha));if let Ok(t)=linearize(p,cv,old,trial,h,dc){if let Ok(dd)=solve_linear_sparse(t.j,t.r.map(|v|-v)){let next=correction(&dd);if(residual(&t.r)<=1.&&next<=1.)||residual(&t.r)<norm*(1.-1e-4*alpha){delta=trial;found=true;break;}}}}
  if !found{return Err(StepError::NoDecrease);}
 }Err(StepError::IterationBudget)
}
pub fn process(p:Parameters,cv:f64,s:&mut State,h:f64,budget:usize)->Result<Accepted,StepError>{let q=solve(p,cv,*s,h,false,budget)?;*s=q.state;Ok(q)}
