//! Fixed-boundary charge Radau for the conditional mixer/filter/VCA chain.
//! Own increment guesses; no state publication or IO. Reference-only cost.
use crate::{chain_charge::{self,Parameters,State,N},output_conversion::solve_linear_sparse,StepError};
pub const B:[[f64;2];2]=crate::vco1_radau::B;
const M:usize=2*N;
pub struct Stamp {pub residual:[f64;M],pub jacobian:[[f64;M];M],pub candidates:[State;2]}
pub struct Solution {pub candidate:State,pub delta:[f64;N],pub delta_low:[f64;N],pub residual_ratio:f64,pub correction_ratio:f64,pub iterations:usize,pub trials:usize}
pub struct Pair {pub stage:Solution,pub endpoint:Solution}
pub fn linearize(p:Parameters,sources:[f64;5],old:State,delta:[[f64;N];2],h:f64)->Result<Stamp,StepError> {
 linearize_compensated(p,sources,old,delta.map(State::from_nodes),h)
}
pub fn linearize_compensated(p:Parameters,sources:[f64;5],old:State,delta:[State;2],h:f64)->Result<Stamp,StepError> {
 let q=[chain_charge::linearize_compensated(p,sources,old,delta[0],h)?,chain_charge::linearize_compensated(p,sources,old,delta[1],h)?];
 let residual=std::array::from_fn(|k|{let i=k/N;let a=k%N;q[i].dc[a]+B[i][0]*q[0].charge_over_h[a]+B[i][1]*q[1].charge_over_h[a]});
 let jacobian=std::array::from_fn(|k|std::array::from_fn(|l|{let i=k/N;let j=l/N;let a=k%N;let b=l%N;B[i][j]*q[j].mass_over_h[a][b]+if i==j {q[i].dc_jacobian[a][b]} else {0.}}));
 if residual.iter().chain(jacobian.iter().flatten()).any(|v|!v.is_finite()) {return Err(StepError::ExponentialDomain);}
 Ok(Stamp{residual,jacobian,candidates:[q[0].candidate,q[1].candidate]})
}
fn merit(p:Parameters,r:&[f64;M])->f64 {r.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if chain_charge::constraint_row(p,k%N) {1e-11} else {1e-13}))}
fn correction(r:&[f64;M])->f64 {r.iter().fold(0_f64,|a,v|a.max(v.abs()/2e-9))}
pub fn step(p:Parameters,sources:[f64;5],old:State,h:f64)->Result<Pair,StepError> {
 let mut delta=[State::from_nodes([0.;N]);2];let mut trials=0;
 for iteration in 1..=64 {
  let s=linearize_compensated(p,sources,old,delta,h)?;let norm=merit(p,&s.residual);
  let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|k|-s.residual[k]))?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {let make=|i:usize|Solution {candidate:s.candidates[i],delta:delta[i].high,delta_low:delta[i].low,residual_ratio:norm,correction_ratio:ratio,iterations:iteration,trials};return Ok(Pair{stage:make(0),endpoint:make(1)});}
  let mut accepted=false;
  for power in 0..24 {let alpha=2_f64.powi(-power);let trial=std::array::from_fn(|i|delta[i].advanced(std::array::from_fn(|a|alpha*d[i*N+a])));trials+=1;
   if let Ok(t)=linearize_compensated(p,sources,old,trial,h) {if let Ok(dd)=solve_linear_sparse(t.jacobian,std::array::from_fn(|k|-t.residual[k])) {let next=correction(&dd);
    if (merit(p,&t.residual)<=1.&&next<=1.)||merit(p,&t.residual)<norm*(1.-1e-4*alpha) {delta=trial;accepted=true;break;}
   }}
  }
  if !accepted {return Err(StepError::NoDecrease);}
 }Err(StepError::IterationBudget)
}
