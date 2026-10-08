//! Coupled two-stage Radau IIA on charge/flux; private lab, physical cards intact.
use crate::{vco1_radau_fine::{self as fine,State,Solution},vco1_stamp::{self,Controls,Mode,N,NV},vco1_newton::{Budget,Error},output_conversion::solve_linear_sparse};
const M:usize=2*N;
pub const B:[[f64;2];2]=[[1.5,0.5],[-4.5,2.5]];
pub struct Pair {pub stage:Solution,pub endpoint:Solution}
struct Parts {f:[f64;N],q:[f64;N],g:[[f64;N];N],mass:[[f64;N];N],ground_f:f64,ground_q:f64,state:State}
pub struct Stamp {pub residual:[f64;M],pub jacobian:[[f64;M];M],pub ground:[f64;2],pub candidates:[State;2]}
fn parts(c:Controls,old:State,delta:[f64;N],h:f64)->Result<Parts,vco1_stamp::Error> {
 let e=fine::linearize(old,delta,c,h)?;let d=vco1_stamp::linearize(e.candidate.high,c,Mode::Dc)?;
 let lo:[f64;N]=std::array::from_fn(|a|(0..N).map(|b|d.jacobian[a][b]*e.candidate.low[b]).sum());
 let f=std::array::from_fn(|a|d.residual[a]+lo[a]);let q=std::array::from_fn(|a|e.residual[a]-f[a]);
 let mass=std::array::from_fn(|a|std::array::from_fn(|b|e.jacobian[a][b]-d.jacobian[a][b]));
 let ground_f=d.ground_current_a-lo[..NV].iter().sum::<f64>();
 if q.iter().enumerate().any(|(k,v)|!v.is_finite()||(k>=NV&&![118,119,129,130].contains(&k)&&*v!=0.)) {return Err(vco1_stamp::Error::NonFinite);}
 Ok(Parts{f,q,g:d.jacobian,mass,ground_f,ground_q:e.ground_current_a-ground_f,state:e.candidate})
}
pub fn linearize(c:Controls,old:State,delta:[[f64;N];2],h:f64)->Result<Stamp,vco1_stamp::Error> {
 let p=[parts(c,old,delta[0],h)?,parts(c,old,delta[1],h)?];
 let residual=std::array::from_fn(|k|{let i=k/N;let a=k%N;p[i].f[a]+B[i][0]*p[0].q[a]+B[i][1]*p[1].q[a]});
 let jacobian=std::array::from_fn(|k|std::array::from_fn(|l|{let i=k/N;let j=l/N;let a=k%N;let b=l%N;B[i][j]*p[j].mass[a][b]+if i==j {p[i].g[a][b]} else {0.}}));
 let ground=std::array::from_fn(|i|p[i].ground_f+B[i][0]*p[0].ground_q+B[i][1]*p[1].ground_q);
 if residual.iter().chain(jacobian.iter().flatten()).chain(ground.iter()).any(|v|!v.is_finite()) {return Err(vco1_stamp::Error::NonFinite);}
 Ok(Stamp{residual,jacobian,ground,candidates:[p[0].state,p[1].state]})
}
fn merit(r:&[f64;M])->f64 {r.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i%N<NV {1e-13} else {1e-11}))}
fn correction(r:&[f64;M])->f64 {r.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i%N<NV {2e-9} else {2e-12}))}
pub fn step(c:Controls,old:State,h:f64)->Result<Pair,Error> {
 let budget=Budget::default();let mut delta=[[0.;N];2];let mut trials=0;
 for iteration in 1..=budget.iterations {
  let s=linearize(c,old,delta,h).map_err(Error::Device)?;let norm=merit(&s.residual);
  let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|k|-s.residual[k])).map_err(|_|Error::Singular)?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {
   let make=|i|Solution{candidate:s.candidates[i],delta:delta[i],iterations:iteration,trials,residual_ratio:norm,correction_ratio:ratio};
   return Ok(Pair{stage:make(0),endpoint:make(1)});
  }
  let mut accepted=false;
  for power in 0..budget.halvings {
   let alpha=2_f64.powi(-(power as i32));let trial=std::array::from_fn(|i|std::array::from_fn(|a|delta[i][a]+alpha*d[i*N+a]));trials+=1;
   if let Ok(t)=linearize(c,old,trial,h) {if let Ok(dd)=solve_linear_sparse(t.jacobian,std::array::from_fn(|k|-t.residual[k])) {let next=correction(&dd);
    if (merit(&t.residual)<=1.&&next<=1.)||merit(&t.residual)<norm*(1.-1e-4*alpha) {delta=trial;accepted=true;break;}
   }}
  }
  if !accepted {return Err(Error::LineSearch);}
 }Err(Error::IterationLimit)
}

/// Outward Qa/Q10 collector and Q7 gate currents with the endpoint Radau derivative.
pub fn terminal_currents(p:&Pair,old:State,h:f64)->Result<[f64;3],vco1_stamp::Error> {
 let a=p.stage.candidate;let b=p.endpoint.candidate;
 let fa=fine::observed_currents(a,a,h)?;let ea=fine::observed_currents(a,old,h)?;
 let fb=fine::observed_currents(b,b,h)?;let eb=fine::observed_currents(b,old,h)?;
 Ok(std::array::from_fn(|k|fb[k]+B[1][0]*(ea[k]-fa[k])+B[1][1]*(eb[k]-fb[k])))
}
