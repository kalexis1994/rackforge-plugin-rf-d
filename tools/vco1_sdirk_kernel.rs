//! Charge-form SDIRK2 lab kernel; no change to published physical cards.
use crate::{fine::{self,State,Solution,Stamp},vco1_stamp::{self,Controls,Mode,N,NV},vco1_newton::{Budget,Error},output_conversion::solve_linear_sparse};
pub const GAMMA:f64=1.-std::f64::consts::FRAC_1_SQRT_2;
pub fn weight()->f64 {(1.-GAMMA)/GAMMA}
#[derive(Debug)]
pub struct Pair {pub stage:Solution,pub endpoint:Solution,pub dynamic:[f64;N],pub ground_dynamic:f64}
fn dynamic(c:Controls,old:State,stage:&Solution,dt:f64)->Result<([f64;N],f64),Error> {
 let e=fine::linearize(old,stage.delta,c,dt).map_err(Error::Device)?;let d=vco1_stamp::linearize(stage.candidate.high,c,Mode::Dc).map_err(Error::Device)?;
 let correction: [f64;N]=std::array::from_fn(|a|(0..N).map(|b|d.jacobian[a][b]*stage.candidate.low[b]).sum());
 let dq=std::array::from_fn(|a|e.residual[a]-(d.residual[a]+correction[a]));let ground=e.ground_current_a-(d.ground_current_a-correction[..NV].iter().sum::<f64>());
 if dq.iter().enumerate().any(|(k,v)|!v.is_finite()||(k>=NV&&![118,119,129,130].contains(&k)&&*v!=0.))||!ground.is_finite() {return Err(Error::InvalidInput);}Ok((dq,ground))
}
fn forced(old:State,delta:[f64;N],c:Controls,dt:f64,history:&[f64;N],ground:f64)->Result<Stamp,vco1_stamp::Error> {
 let mut s=fine::linearize(old,delta,c,dt)?;for k in 0..N {s.residual[k]-=weight()*history[k];}s.ground_current_a-=weight()*ground;Ok(s)
}
pub fn step(c:Controls,old:State,h:f64)->Result<Pair,Error> {
 let dt=GAMMA*h;let stage=fine::solve(c,old,dt,Budget::default())?;let (history,ground)=dynamic(c,old,&stage,dt)?;
 let endpoint=forced_solve(c,old,dt,Budget::default(),stage.delta,history,ground)?;Ok(Pair{stage,endpoint,dynamic:history,ground_dynamic:ground})
}
fn merit(r:&[f64;N])->f64 {r.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i<NV {1e-13} else {1e-11}))}
fn correction(d:&[f64;N])->f64 {d.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i<NV {2e-9} else {2e-12}))}
fn forced_solve(c:Controls,previous:State,dt:f64,budget:Budget,initial:[f64;N],forcing:[f64;N],ground:f64)->Result<Solution,Error> {
 if !(1..=64).contains(&budget.iterations)||!(1..=24).contains(&budget.halvings) {return Err(Error::InvalidInput);}
 let mut delta=initial;let mut trials=0;
 for iteration in 1..=budget.iterations {
  let s=forced(previous,delta,c,dt,&forcing,ground).map_err(Error::Device)?;let norm=merit(&s.residual);
  let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|i|-s.residual[i])).map_err(|_|Error::Singular)?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {return Ok(Solution{candidate:s.candidate,delta,iterations:iteration,trials,residual_ratio:norm,correction_ratio:ratio});}
  let mut accepted=false;
  for power in 0..budget.halvings {let alpha=2_f64.powi(-(power as i32));let trial=std::array::from_fn(|i|delta[i]+alpha*d[i]);trials+=1;
   if let Ok(t)=forced(previous,trial,c,dt,&forcing,ground) {if let Ok(dd)=solve_linear_sparse(t.jacobian,std::array::from_fn(|i|-t.residual[i])) {let next=correction(&dd);
    if (merit(&t.residual)<=1.&&next<=1.)||next<ratio*(1.-1e-4*alpha) {delta=trial;accepted=true;break;}
   }}
  }
  if !accepted {return Err(Error::LineSearch);}
 }Err(Error::IterationLimit)
}

