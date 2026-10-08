//! Coupled 134-row VCO1 Newton. See VCO1_NEWTON_PROTOCOLO.md.
//! No waveform/threshold imposed in Free mode; startup constraint is explicit.
use crate::vco1_stamp::{self,Controls,Memory,Mode,Stamp,N,NV};
use crate::output_conversion::solve_linear_sparse;
const RAMP:usize=43;
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Boundary { Free, StartupRampZero }
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Budget {pub iterations:usize,pub halvings:usize}
impl Default for Budget {fn default()->Self {Self{iterations:64,halvings:24}}}
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Error {InvalidInput,Device(vco1_stamp::Error),Singular,IterationLimit,LineSearch}
#[derive(Debug)]
pub struct Solution {pub nodes:[f64;N],pub candidate:Memory,pub startup_current_a:Option<f64>,pub iterations:usize,pub trials:usize,pub residual_ratio:f64,pub correction_ratio:f64}
fn system(x:[f64;N],c:Controls,m:Mode,b:Boundary)->Result<(Stamp,Option<f64>),Error> {
 let mut s=vco1_stamp::linearize(x,c,m).map_err(Error::Device)?;
 let forcing=if b==Boundary::StartupRampZero {
  let i=-s.residual[RAMP];s.residual[RAMP]=x[RAMP];s.jacobian[RAMP]=[0.;N];s.jacobian[RAMP][RAMP]=1.;Some(i)
 } else {None};Ok((s,forcing))
}
fn merit(r:&[f64;N],b:Boundary)->f64 {r.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i<NV && !(b==Boundary::StartupRampZero&&i==RAMP) {1e-13} else {1e-11}))}
fn correction(d:&[f64;N])->f64 {d.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i<NV {2e-9} else {2e-12}))}
pub fn solve(c:Controls,m:Mode,b:Boundary,initial:[f64;N],budget:Budget)->Result<Solution,Error> {
 if !(1..=64).contains(&budget.iterations)||!(1..=24).contains(&budget.halvings)||(b==Boundary::StartupRampZero&&m!=Mode::Dc) {return Err(Error::InvalidInput);}
 let mut x=initial;let mut trials=0;
 for iteration in 1..=budget.iterations {
  let (s,forcing)=system(x,c,m,b)?;let norm=merit(&s.residual,b);
  let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|i|-s.residual[i])).map_err(|_|Error::Singular)?;let ratio=correction(&d);
  if norm<=1. && ratio<=1. {return Ok(Solution{nodes:x,candidate:s.candidate,startup_current_a:forcing,iterations:iteration,trials,residual_ratio:norm,correction_ratio:ratio});}
  let mut accepted=false;
  for power in 0..budget.halvings {
   let alpha=2_f64.powi(-(power as i32));let trial=std::array::from_fn(|i|x[i]+alpha*d[i]);trials+=1;
   if let Ok((t,_))=system(trial,c,m,b) {
    if let Ok(dd)=solve_linear_sparse(t.jacobian,std::array::from_fn(|i|-t.residual[i])) {
     let next=correction(&dd);
     if (merit(&t.residual,b)<=1. && next<=1.) || next<ratio*(1.-1e-4*alpha) {x=trial;accepted=true;break;}
    }
   }
  }
  if !accepted {return Err(Error::LineSearch);}
 }
 Err(Error::IterationLimit)
}
