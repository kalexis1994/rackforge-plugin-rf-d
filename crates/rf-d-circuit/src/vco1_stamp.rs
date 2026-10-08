//! Full conditional CA3046 VCO1 MNA; SVC-9 p.5 and p.19, nominal cards at 25 C.
//! Fixed panel SW6 3/10, alpha=.5, ON with imposed mixer bus. No autonomous solve.
//! Full rows of both 741s and exact trim contacts; see VCO1_STAMP_PROTOCOLO.md.
use crate::{lm741,vco_bjt,vco_jfet};
#[path="vco1_stamp_data.rs"] mod data;
pub use data::{N,NV,GROUND,NAMES};
use data::{RESISTORS,CAPACITORS,TRANSISTORS,JFETS,VOLTAGES,TRIMS,OPAMPS};
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum C4 { Schematic10Pf, Bom100Pf }
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Controls {
 /// Board-line volts [BEND,TUNE,KEYBOARD,MOD,EXT,OSC1_RANGE], not MIDI/knob values.
 pub cv_v:[f64;6], pub r8_fraction:f64, pub r11_ohm:f64,
 pub c4:C4, pub mixer_v:f64, pub external_neg4_load_a:f64,
}
impl Default for Controls {
 fn default()->Self {Self{cv_v:[-2.1;6],r8_fraction:0.5,r11_ohm:500.,c4:C4::Schematic10Pf,mixer_v:0.,external_neg4_load_a:0.}}
}
impl Controls {
 fn valid(self)->bool { self.cv_v.iter().chain([self.mixer_v].iter()).all(|v|v.is_finite()&&v.abs()<=40.)
  &&self.r8_fraction.is_finite()&&(0. ..=1.).contains(&self.r8_fraction)
  &&self.r11_ohm.is_finite()&&(0. ..=1000.).contains(&self.r11_ohm)
  &&self.external_neg4_load_a.is_finite()&&self.external_neg4_load_a.abs()<=1. }
}
/// Accepted state owns every physical junction and both 741 memories by node identity.
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Memory { pub state:[f64;N] }
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Mode { Dc, Euler {dt_s:f64,previous:Memory} }
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Error { InvalidInput, Bjt(vco_bjt::Error), Jfet(vco_jfet::Error), Opamp(lm741::Error), NonFinite }
#[derive(Debug)]
pub struct Stamp {pub residual:[f64;N],pub jacobian:[[f64;N];N],pub candidate:Memory,pub ground_current_a:f64}
fn valid_state(x:&[f64;N])->bool {x[..NV].iter().all(|v|v.is_finite()&&v.abs()<=40.)&&x[NV..].iter().all(|v|v.is_finite()&&v.abs()<=1.)}
fn value(x:&[f64;N],n:usize)->f64 {if n==GROUND {0.} else {x[n]}}
impl Stamp {
 fn current(&mut self,row:usize,i:f64) {if row==GROUND {self.ground_current_a+=i;} else {self.residual[row]+=i;}}
 fn derivative(&mut self,row:usize,col:usize,g:f64) {if row!=GROUND&&col!=GROUND {self.jacobian[row][col]+=g;}}
 fn branch(&mut self,a:usize,b:usize,i:f64,g:&[(usize,f64)]) {
  self.current(a,i);self.current(b,-i);
  for &(c,v) in g {self.derivative(a,c,v);self.derivative(b,c,-v);}
 }
 fn voltage(&mut self,x:&[f64;N],row:usize,a:usize,b:usize,v:f64,r:f64) {
  self.branch(a,b,x[row],&[(row,1.)]);self.residual[row]=value(x,a)-value(x,b)-v-r*x[row];
  self.derivative(row,a,1.);self.derivative(row,b,-1.);self.derivative(row,row,-r);
 }
 fn device<const K:usize>(&mut self,map:[usize;K],i:[f64;K],j:[[f64;K];K]) {
  for r in 0..K {self.current(map[r],i[r]);for c in 0..K {self.derivative(map[r],map[c],j[r][c]);}}
 }
}
pub fn linearize(x:[f64;N],controls:Controls,mode:Mode)->Result<Stamp,Error> {
 if !valid_state(&x)||!controls.valid() {return Err(Error::InvalidInput);}
 let (dt,old)=match mode {Mode::Dc=>(None,x),Mode::Euler{dt_s,previous}=>{
  if !dt_s.is_finite()||!(125e-9..=1e-3).contains(&dt_s)||!valid_state(&previous.state) {return Err(Error::InvalidInput);}
  (Some(dt_s),previous.state)
 }};
 let mut s=Stamp{residual:[0.;N],jacobian:[[0.;N];N],candidate:Memory{state:x},ground_current_a:0.};
 for (a,b,r) in RESISTORS {let g=1./r;s.branch(a,b,(value(&x,a)-value(&x,b))*g,&[(a,g),(b,-g)]);}
 for (k,(a,b,c)) in CAPACITORS.into_iter().enumerate() {
  if let Some(dt)=dt {let c=if k==3 {match controls.c4 {C4::Schematic10Pf=>1e-11,C4::Bom100Pf=>1e-10}} else {c};let g=c/dt;
   s.branch(a,b,g*((value(&x,a)-value(&x,b))-(value(&old,a)-value(&old,b))),&[(a,g),(b,-g)]);}
 }
 // Shared NEG4_REF external load returns to physical ground, never a new fixed rail.
 s.branch(15,GROUND,controls.external_neg4_load_a,&[]);
 for (k,(a,b,v)) in VOLTAGES.into_iter().enumerate() {
  let v=if (3..9).contains(&k) {controls.cv_v[k-3]} else if k==10 {controls.mixer_v} else {v};
  s.voltage(&x,NV+k,a,b,v,0.);
 }
 for (k,(a,b)) in TRIMS.into_iter().enumerate() {
  let r=match k {0=>100.*(1.-controls.r8_fraction),1=>100.*controls.r8_fraction,_=>controls.r11_ohm};
  s.voltage(&x,131+k,a,b,0.,r);
 }
 for (pnp,map) in TRANSISTORS {
  let p=if pnp {vco_bjt::Polarity::Pnp} else {vco_bjt::Polarity::Npn};let node=map.map(|n|value(&x,n));
  if let Some(dt)=dt {let t=vco_bjt::companion(p,node,map.map(|n|value(&old,n)),dt).map_err(Error::Bjt)?;s.device(map,t.current_a,t.jacobian_s);}
  else {let t=vco_bjt::evaluate(p,node).map_err(Error::Bjt)?;s.device(map,t.current_a,t.jacobian_s);}
 }
 for map in JFETS {
  let node=map.map(|n|value(&x,n));
  if let Some(dt)=dt {let t=vco_jfet::companion(node,map.map(|n|value(&old,n)),dt).map_err(Error::Jfet)?;s.device(map,t.current_a,t.jacobian_s);}
  else {let t=vco_jfet::evaluate(node).map_err(Error::Jfet)?;s.device(map,t.current_a,t.jacobian_s);}
 }
 for map in OPAMPS {
  let node=map.map(|n|value(&x,n));let mode=match dt {None=>lm741::Mode::Dc,Some(dt_s)=>lm741::Mode::Euler{dt_s,previous:lm741::memory(&map.map(|n|value(&old,n)))}};
  let t=lm741::linearize(node,mode).map_err(Error::Opamp)?;
  s.device(map,t.residual,t.jacobian);s.ground_current_a+=t.ground_current_a;
 }
 if !s.ground_current_a.is_finite()||s.residual.iter().chain(s.jacobian.iter().flatten()).any(|v|!v.is_finite()) {return Err(Error::NonFinite);}
 Ok(s)
}
