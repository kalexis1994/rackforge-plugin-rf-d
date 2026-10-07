//! Five imposed terminal voltages, full nominal LM741 solve and loaded tangents.
//! See VCO_741_PUERTO_PROTOCOLO.md. History and every candidate are caller-owned.
use crate::lm741::{self,Memory,Mode,Stamp,N,NV};
use crate::output_conversion::{solve_linear,solve_linear_many};
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Budget {pub iterations:usize,pub halvings:usize}
impl Default for Budget {fn default()->Self {Self{iterations:64,halvings:24}}}
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Error {InvalidInput,Device(lm741::Error),Singular,IterationLimit,LineSearch}
#[derive(Debug)]
pub struct Port {pub nodes:[f64;N],pub candidate:Memory,pub current_a:[f64;5],pub admittance:[[f64;5];5],pub node_gradient:[[f64;5];N],pub iterations:usize,pub halvings:usize,pub residual_ratio:f64,pub correction_ratio:f64}
/// Analytic start only; no imported operating-point vector.
pub fn seed(p:[f64;5])->[f64;N] {
 if p.iter().any(|v|!v.is_finite()||v.abs()>40.) || p[3]+1.63-0.65>p[2]-1.63+0.65 {return [f64::NAN;N];}
 let mut x=[0.;N];x[..5].copy_from_slice(&p);let mid=(p[2]+p[3])*0.5;let cm=mid+3.1623e-5*((p[0]+p[1])*0.5-mid);
 x[5]=(p[0]+p[1])*0.5;x[9]=p[0]+0.001+cm-mid;
 let differential=x[9]-p[1];let tail=100e-6*625./626.;let split=(differential/(2.*lm741::VT)).tanh();
 x[6]=0.5*(p[1]+x[9])-lm741::VT*(tail/(2e-16*(differential/(2.*lm741::VT)).cosh())).ln();
 x[7]=p[2]-517.*tail*(1.-split)*0.5;x[8]=p[2]-517.*tail*(1.+split)*0.5;
 x[10]=p[2]-1.63;x[12]=p[3]+1.63;
 // Smooth pair current estimate and diode-limit estimates are seeds only.
 x[11]=(mid+0.0021*95.493e6*517.*tail*split).clamp(x[12]-0.65,x[10]+0.65);
 x[15]=x[11].clamp(p[4]-0.75,p[4]+0.75);x[18]=x[15];
 x[13]=mid;x[14]=mid;x[16]=cm;x[17]=mid;x[20]=p[4]+0.65;x[21]=p[4];x[23]=p[4]-0.65;x[24]=p[4]-0.18;x[25]=p[4]+0.18;
 x[19]=x[18].max(x[20]-lm741::VT*((x[20]-x[18]).max(0.)/25./1e-15).ln_1p());
 x[22]=x[18].min(x[23]+lm741::VT*((x[18]-x[23]).max(0.)/25./1e-15).ln_1p());x

}
fn system(x:[f64;N],p:[f64;5],mode:Mode)->Result<([f64;N],[[f64;N];N],Stamp),Error> {
 let s=lm741::linearize(x,mode).map_err(Error::Device)?;let mut r=s.residual;let mut j=s.jacobian;
 for i in 0..5 {r[i]=x[i]-p[i];j[i]=[0.;N];j[i][i]=1.;}Ok((r,j,s))
}
fn merit(r:&[f64;N])->f64 {r.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if (5..NV).contains(&i){1e-13}else{1e-11}))}
fn correction(d:&[f64;N])->f64 {d.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i<NV {2e-9}else{2e-12}))}
pub fn solve(p:[f64;5],mode:Mode,initial:[f64;N],budget:Budget)->Result<Port,Error> {
 if p.iter().any(|v|!v.is_finite()||v.abs()>40.)||initial.iter().any(|v|!v.is_finite())||!(1..=64).contains(&budget.iterations)||!(1..=24).contains(&budget.halvings) {return Err(Error::InvalidInput);}
 // Keep input port voltages equal throughout trials; ideal current rows remain.
 let mut x=initial;
 // Predict the linear common-mode subnetwork from its accepted L2 history.
 let mid=0.5*(p[2]+p[3]);x[5]=0.5*(p[0]+p[1]);x[14]=mid;x[13]=mid;
 x[35]=-3.1623e-8*(x[5]-mid);x[17]=mid;
 if let Mode::Euler{dt_s,previous}=mode {
  if !dt_s.is_finite()||!(125e-9..=1e-3).contains(&dt_s){return Err(Error::InvalidInput);}
  x[17]-=0.5305/dt_s*(x[35]-previous.inductor_i_a[0]);
 }
 x[16]=x[17]-1000.*x[35];x[9]=p[0]+0.001+x[16]-mid;
 x[6]+=0.5*((p[1]-initial[1])+(x[9]-initial[9]));
 x[..5].copy_from_slice(&p);let mut total=0;
 for iteration in 1..=budget.iterations {
  let (r,j,s)=system(x,p,mode)?;let norm=merit(&r);let d=solve_linear(j,std::array::from_fn(|i|-r[i])).map_err(|_|Error::Singular)?;let correction_ratio=correction(&d);
  if norm<=1. && correction_ratio<=1. {
   let mut rhs=[[0.;5];N];for i in 0..5 {rhs[i][i]=1.;}
   let gradient=solve_linear_many(j,rhs).map_err(|_|Error::Singular)?;
   let mut y=[[0.;5];5];for i in 0..5 {for k in 0..5 {for c in 0..N {y[i][k]+=s.jacobian[i][c]*gradient[c][k];}}}
   if y.iter().flatten().chain(gradient.iter().flatten()).any(|v|!v.is_finite()){return Err(Error::Singular);}
   return Ok(Port{nodes:x,candidate:s.candidate,current_a:std::array::from_fn(|i|s.residual[i]),admittance:y,node_gradient:gradient,iterations:iteration,halvings:total,residual_ratio:norm,correction_ratio});
  }
  let mut accepted=false;
  for power in 0..budget.halvings {
   let alpha=2_f64.powi(-(power as i32));let mut trial=std::array::from_fn(|i|x[i]+alpha*d[i]);trial[..5].copy_from_slice(&p);total+=1;
   if let Ok((rr,jj,_))=system(trial,p,mode) {
    if let Ok(dd)=solve_linear(jj,std::array::from_fn(|i|-rr[i])) {
     let next=correction(&dd);
     if (merit(&rr)<=1. && next<=1.) || next<correction_ratio*(1.-1e-4*alpha) {x=trial;accepted=true;break;}
    }
   }
  }
  if !accepted{return Err(Error::LineSearch);}
 }
 Err(Error::IterationLimit)
}
pub fn dc(p:[f64;5])->Result<Port,Error> {solve(p,Mode::Dc,seed(p),Budget::default())}
