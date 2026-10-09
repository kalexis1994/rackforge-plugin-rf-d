//! Joint DC initialization with explicit RAMP_C1=0 constraint (SVC-9 p.5).
//! Seed supplied by caller; not free DC or an analytic whole-voice startup.
use crate::{joint_voice::{self as joint,State,Parameters,N},output_conversion::solve_linear_sparse,StepError};
pub use crate::vco1_newton::Budget;
pub struct Solution {pub state:State,pub constraint_current_a:f64,pub iterations:usize,pub trials:usize,pub residual_ratio:f64,pub correction_ratio:f64}
fn system(p:Parameters,x:State)->Result<([f64;N],[[f64;N];N],f64),StepError> {
 let q=joint::parts(p,x,State::from_nodes([0.;N]),125e-9)?;
 let mut r=q.dc;let mut j=q.dc_jacobian;let forcing=-r[43];
 r[43]=x.high[43]+x.low[43];j[43]=[0.;N];j[43][43]=1.;Ok((r,j,forcing))
}
fn merit(p:Parameters,r:&[f64;N])->f64 {r.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if k==43||joint::constraint_row(p,k) {1e-11} else {1e-13}))}
fn correction(d:&[f64;N])->f64 {d.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if (98..133).contains(&k) {2e-12} else {2e-9}))}
pub fn condition(p:Parameters,initial:State,budget:Budget)->Result<Solution,StepError> {
 if !(1..=64).contains(&budget.iterations)||!(1..=24).contains(&budget.halvings) {return Err(StepError::InvalidInput);}
 let mut x=initial;let mut trials=0;
 for iteration in 1..=budget.iterations {
  let(r,j,forcing)=system(p,x)?;let norm=merit(p,&r);let d=solve_linear_sparse(j,std::array::from_fn(|k|-r[k]))?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {return Ok(Solution{state:x,constraint_current_a:forcing,iterations:iteration,trials,residual_ratio:norm,correction_ratio:ratio});}
  let mut accepted=false;
  for power in 0..budget.halvings {
   let alpha=2_f64.powi(-(power as i32));let trial=x.advanced(std::array::from_fn(|k|alpha*d[k]));trials+=1;
   if let Ok((rr,jj,_))=system(p,trial) {if let Ok(dd)=solve_linear_sparse(jj,std::array::from_fn(|k|-rr[k])) {
    if (merit(p,&rr)<=1.&&correction(&dd)<=1.)||merit(p,&rr)<norm*(1.-1e-4*alpha) {x=trial;accepted=true;break;}
   }}
  }
  if !accepted {return Err(StepError::NoDecrease);}
 }Err(StepError::IterationBudget)
}
