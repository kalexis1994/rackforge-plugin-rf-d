//! Short-step VCO1: unchanged DC laws + physical charge/memory increments.
//! Numeric floor only; see VCO1_SUBPASOS_PROTOCOLO.md.
use crate::{lm741,vco_bjt,vco_jfet,vco1_stamp};
use vco1_stamp::{Controls,Memory,Mode,Stamp,N,NV};
use crate::vco1_newton::{Boundary,Budget,Error,Solution};
use crate::output_conversion::solve_linear_sparse;
#[path="vco1_stamp_data.rs"] mod data;
pub const MIN_DT_S:f64=125e-9/4096.;
const RAMP:usize=43;
fn value(x:&[f64;N],i:usize)->f64 {if i==N {0.} else {x[i]}}
fn current(s:&mut Stamp,i:usize,v:f64) {if i==N {s.ground_current_a+=v;} else {s.residual[i]+=v;}}
fn derivative(s:&mut Stamp,i:usize,j:usize,v:f64) {if i!=N&&j!=N {s.jacobian[i][j]+=v;}}
fn capacitor(s:&mut Stamp,x:&[f64;N],old:&[f64;N],a:usize,b:usize,c:f64,dt:f64) {
 let g=c/dt;let i=g*((value(x,a)-value(x,b))-(value(old,a)-value(old,b)));
 current(s,a,i);current(s,b,-i);derivative(s,a,a,g);derivative(s,a,b,-g);derivative(s,b,a,-g);derivative(s,b,b,g);
}
pub fn linearize(x:[f64;N],c:Controls,m:Mode)->Result<Stamp,vco1_stamp::Error> {
 let (dt,old)=match m {Mode::Dc=>return vco1_stamp::linearize(x,c,m),Mode::Euler{dt_s,previous}=>{
  if !dt_s.is_finite()||!(MIN_DT_S..=1e-3).contains(&dt_s) {return Err(vco1_stamp::Error::InvalidInput);}
  if dt_s>=125e-9 {return vco1_stamp::linearize(x,c,m);} (dt_s,previous.state)
 }};
 if old[..NV].iter().any(|v|!v.is_finite()||v.abs()>40.)||old[NV..].iter().any(|v|!v.is_finite()||v.abs()>1.) {return Err(vco1_stamp::Error::InvalidInput);}
 let mut s=vco1_stamp::linearize(x,c,Mode::Dc)?;
 for (k,(a,b,v)) in data::CAPACITORS.into_iter().enumerate() {let cap=if k==3 {match c.c4 {vco1_stamp::C4::Schematic10Pf=>1e-11,vco1_stamp::C4::Bom100Pf=>1e-10}} else {v};capacitor(&mut s,&x,&old,a,b,cap,dt);}
 for (pnp,map) in data::TRANSISTORS {
  let p=if pnp {vco_bjt::Polarity::Pnp} else {vco_bjt::Polarity::Npn};
  let t=vco_bjt::companion(p,map.map(|i|value(&x,i)),map.map(|i|value(&old,i)),125e-9).map_err(vco1_stamp::Error::Bjt)?;
  let sign=if pnp {-1.} else {1.};let be=sign*t.delta_charge_c[0]/dt;let bc=sign*t.delta_charge_c[1]/dt;
  for (i,v) in map.into_iter().zip([-bc,be+bc,-be,0.]) {current(&mut s,i,v);}
  for a in 0..4 {for b in 0..4 {derivative(&mut s,map[a],map[b],t.candidate.charge_jacobian_f[a][b]/dt);}}
 }
 for map in data::JFETS {
  let t=vco_jfet::companion(map.map(|i|value(&x,i)),map.map(|i|value(&old,i)),125e-9).map_err(vco1_stamp::Error::Jfet)?;
  let gs=t.delta_charge_c[0]/dt;let gd=t.delta_charge_c[1]/dt;
  for (i,v) in map.into_iter().zip([-gd,gs+gd,-gs]) {current(&mut s,i,v);}
  for a in 0..3 {for b in 0..3 {derivative(&mut s,map[a],map[b],t.candidate.charge_jacobian_f[a][b]/dt);}}
 }
 for map in data::OPAMPS {
  let at=|n|map[lm741::NODES.iter().position(|i|*i==n).unwrap()];
  for (a,b,c) in [(5,6,60.3614e-12),(98,9,333.33e-12),(98,15,5.3052e-15)] {capacitor(&mut s,&x,&old,at(a),at(b),c,dt);}
  for (k,l) in [0.5305,100e-12].into_iter().enumerate() {let row=map[35+k];s.residual[row]-=l/dt*(x[row]-old[row]);s.jacobian[row][row]-=l/dt;}
 }
 if !s.ground_current_a.is_finite()||s.residual.iter().chain(s.jacobian.iter().flatten()).any(|v|!v.is_finite()) {return Err(vco1_stamp::Error::NonFinite);}Ok(s)
}
fn system(x:[f64;N],c:Controls,m:Mode,b:Boundary)->Result<(Stamp,Option<f64>),Error> {
 let mut s=linearize(x,c,m).map_err(Error::Device)?;
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
