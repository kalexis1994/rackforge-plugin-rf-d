//! Increment coordinates with normalized high/low memory. See protocol.
//! All physical laws are inherited; low components use first-order evaluations.
use crate::{vco1_stamp::{self,Controls,C4,Mode,N,NV},vco_bjt,vco_jfet,lm741};
use crate::vco1_newton::{Budget,Error};
use crate::block_decay_voice::solve_linear_sparse;
#[path="../crates/rf-d-circuit/src/vco1_stamp_data.rs"] mod data;
pub const MIN_DT_S:f64=125e-9/65536.;
pub fn two_sum(a:f64,b:f64)->(f64,f64) {let s=a+b;let v=s-a;let e=(a-(s-v))+(b-v);(s,e)}
fn add_pair(h:f64,l:f64,d:f64)->(f64,f64) {let(s,e)=two_sum(h,d);let(t,f)=two_sum(l,e);let(u,v)=two_sum(s,t);two_sum(u,v+f)}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct State {pub high:[f64;N],pub low:[f64;N]}
impl State {
 pub fn from_nodes(high:[f64;N])->Self {Self{high,low:[0.;N]}}
 pub fn advanced(self,delta:[f64;N])->Self {let mut q=self;for k in 0..N {(q.high[k],q.low[k])=add_pair(self.high[k],self.low[k],delta[k]);}q}
 pub fn difference(self,other:Self)->[f64;N] {std::array::from_fn(|k|{let(h,l)=add_pair(self.high[k],self.low[k],-other.high[k]);let(h,l)=add_pair(h,l,-other.low[k]);h+l})}
 fn valid(self)->bool {(0..N).all(|k|{let(h,l)=(self.high[k],self.low[k]);let limit=if k<NV {40.} else {1.};h.is_finite()&&l.is_finite()&&h.abs()<=limit&&(h.abs()!=limit||h*l<=0.)&&two_sum(h,l)==(h,l)})}
}
#[derive(Debug)]
pub struct Stamp {pub residual:[f64;N],pub jacobian:[[f64;N];N],pub ground_current_a:f64,pub candidate:State}
#[derive(Debug)]
pub struct Solution {pub candidate:State,pub delta:[f64;N],pub iterations:usize,pub trials:usize,pub residual_ratio:f64,pub correction_ratio:f64}
fn value(x:&[f64;N],i:usize)->f64 {if i==N {0.} else {x[i]}}
fn current(s:&mut Stamp,i:usize,v:f64) {if i==N {s.ground_current_a+=v;} else {s.residual[i]+=v;}}
fn derivative(s:&mut Stamp,i:usize,j:usize,v:f64) {if i!=N&&j!=N {s.jacobian[i][j]+=v;}}
fn cap(s:&mut Stamp,d:State,a:usize,b:usize,c:f64,dt:f64) {let g=c/dt;let(h,l)=add_pair(value(&d.high,a),value(&d.low,a),-value(&d.high,b));let(h,l)=add_pair(h,l,-value(&d.low,b));let i=g*(h+l);current(s,a,i);current(s,b,-i);for (r,col,v) in [(a,a,g),(a,b,-g),(b,a,-g),(b,b,g)] {derivative(s,r,col,v);}}
fn junction_ok(s:State,a:usize,b:usize,sign:f64)->bool {
 let(h,l)=add_pair(value(&s.high,a),value(&s.low,a),-value(&s.high,b));let(h,l)=add_pair(h,l,-value(&s.low,b));let(h,l)=(sign*h,sign*l);
 h>=-40.&&h<=0.9&&(h!=-40.||l>=0.)&&(h!=0.9||l<=0.)
}
fn domain(s:State)->bool {
 if !s.valid() {return false;}
 for(pnp,m) in data::TRANSISTORS {let sign=if pnp {-1.} else {1.};if !junction_ok(s,m[1],m[0],sign)||!junction_ok(s,m[1],m[2],sign) {return false;}}
 for m in data::JFETS {if !junction_ok(s,m[1],m[0],1.)||!junction_ok(s,m[1],m[2],1.) {return false;}}
 for m in data::OPAMPS {let ix=|n|m[lm741::NODES.iter().position(|i|*i==n).unwrap()];
  for (a,b) in [(2,4),(2,5),(7,4),(7,6),(9,8),(10,9),(26,24),(25,27),(21,15),(15,20)] {if !junction_ok(s,ix(a),ix(b),1.) {return false;}}
 }true
}
/// Returns terminal displacement currents and their Jacobian, using stable inherited increments.
fn bjt_dynamic(p:vco_bjt::Polarity,map:[usize;4],now:State,old:State,dt:f64)->Result<([f64;4],[[f64;4];4]),vco1_stamp::Error> {
 let t=vco_bjt::companion(p,map.map(|k|value(&now.high,k)),map.map(|k|value(&old.high,k)),125e-9).map_err(vco1_stamp::Error::Bjt)?;
 let o=vco_bjt::evaluate(p,map.map(|k|value(&old.high,k))).map_err(vco1_stamp::Error::Bjt)?;let sign=if p==vco_bjt::Polarity::Pnp {-1.} else {1.};let be=sign*t.delta_charge_c[0];let bc=sign*t.delta_charge_c[1];let mut dq=[-bc,be+bc,-be,0.];
 for a in 0..4 {for b in 0..4 {dq[a]+=t.candidate.charge_jacobian_f[a][b]*value(&now.low,map[b])-o.charge_jacobian_f[a][b]*value(&old.low,map[b]);}}
 Ok((dq.map(|v|v/dt),t.candidate.charge_jacobian_f.map(|row|row.map(|v|v/dt))))
}
fn jfet_dynamic(map:[usize;3],now:State,old:State,dt:f64)->Result<([f64;3],[[f64;3];3]),vco1_stamp::Error> {
 let t=vco_jfet::companion(map.map(|k|value(&now.high,k)),map.map(|k|value(&old.high,k)),125e-9).map_err(vco1_stamp::Error::Jfet)?;
 let o=vco_jfet::evaluate(map.map(|k|value(&old.high,k))).map_err(vco1_stamp::Error::Jfet)?;let gs=t.delta_charge_c[0];let gd=t.delta_charge_c[1];let mut dq=[-gd,gs+gd,-gs];
 for a in 0..3 {for b in 0..3 {dq[a]+=t.candidate.charge_jacobian_f[a][b]*value(&now.low,map[b])-o.charge_jacobian_f[a][b]*value(&old.low,map[b]);}}
 Ok((dq.map(|v|v/dt),t.candidate.charge_jacobian_f.map(|row|row.map(|v|v/dt))))
}
pub fn linearize(previous:State,delta:[f64;N],c:Controls,dt:f64)->Result<Stamp,vco1_stamp::Error> {
 linearize_compensated(previous,State::from_nodes(delta),c,dt)
}
pub fn linearize_compensated(previous:State,delta:State,c:Controls,dt:f64)->Result<Stamp,vco1_stamp::Error> {
 if !dt.is_finite()||!(MIN_DT_S..=1e-3).contains(&dt)||!domain(previous)||delta.high.iter().chain(delta.low.iter()).any(|v|!v.is_finite())||!(0..N).all(|k|two_sum(delta.high[k],delta.low[k])==(delta.high[k],delta.low[k])) {return Err(vco1_stamp::Error::InvalidInput);}
 let now=previous.advanced(delta.high).advanced(delta.low);if !domain(now) {return Err(vco1_stamp::Error::InvalidInput);}
 let dc=vco1_stamp::linearize(now.high,c,Mode::Dc)?;let mut s=Stamp{residual:dc.residual,jacobian:dc.jacobian,ground_current_a:dc.ground_current_a,candidate:now};
 // Ground gradient is minus the summed nodal columns of the inherited DC incidence.
 for a in 0..N {let correction=(0..N).map(|b|dc.jacobian[a][b]*now.low[b]).sum::<f64>();s.residual[a]+=correction;if a<NV {s.ground_current_a-=correction;}}
 for(k,(a,b,v)) in data::CAPACITORS.into_iter().enumerate() {let v=if k==3 {match c.c4 {C4::Schematic10Pf=>1e-11,C4::Bom100Pf=>1e-10}} else {v};cap(&mut s,delta,a,b,v,dt);}
 for(pnp,m) in data::TRANSISTORS {let p=if pnp {vco_bjt::Polarity::Pnp} else {vco_bjt::Polarity::Npn};let(i,j)=bjt_dynamic(p,m,now,previous,dt)?;for a in 0..4 {current(&mut s,m[a],i[a]);for b in 0..4 {derivative(&mut s,m[a],m[b],j[a][b]);}}}
 for m in data::JFETS {let(i,j)=jfet_dynamic(m,now,previous,dt)?;for a in 0..3 {current(&mut s,m[a],i[a]);for b in 0..3 {derivative(&mut s,m[a],m[b],j[a][b]);}}}
 for m in data::OPAMPS {let ix=|n|m[lm741::NODES.iter().position(|i|*i==n).unwrap()];for(a,b,v) in [(5,6,60.3614e-12),(98,9,333.33e-12),(98,15,5.3052e-15)] {cap(&mut s,delta,ix(a),ix(b),v,dt);}
  for(k,l) in [0.5305,100e-12].into_iter().enumerate() {let row=m[35+k];s.residual[row]-=l/dt*(delta.high[row]+delta.low[row]);s.jacobian[row][row]-=l/dt;}
 }
 if !s.ground_current_a.is_finite()||s.residual.iter().chain(s.jacobian.iter().flatten()).any(|v|!v.is_finite()) {return Err(vco1_stamp::Error::NonFinite);}Ok(s)
}
fn merit(r:&[f64;N])->f64 {r.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i<NV {1e-13} else {1e-11}))}
fn correction(d:&[f64;N])->f64 {d.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if i<NV {2e-9} else {2e-12}))}
pub fn solve(c:Controls,previous:State,dt:f64,budget:Budget)->Result<Solution,Error> {
 if !(1..=64).contains(&budget.iterations)||!(1..=24).contains(&budget.halvings) {return Err(Error::InvalidInput);}
 let mut delta=[0.;N];let mut trials=0;
 for iteration in 1..=budget.iterations {
  let s=linearize(previous,delta,c,dt).map_err(Error::Device)?;let norm=merit(&s.residual);
  let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|i|-s.residual[i])).map_err(|_|Error::Singular)?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {return Ok(Solution{candidate:s.candidate,delta,iterations:iteration,trials,residual_ratio:norm,correction_ratio:ratio});}
  let mut accepted=false;
  for power in 0..budget.halvings {let alpha=2_f64.powi(-(power as i32));let trial=std::array::from_fn(|i|delta[i]+alpha*d[i]);trials+=1;
   if let Ok(t)=linearize(previous,trial,c,dt) {if let Ok(dd)=solve_linear_sparse(t.jacobian,std::array::from_fn(|i|-t.residual[i])) {let next=correction(&dd);
    if (merit(&t.residual)<=1.&&next<=1.)||next<ratio*(1.-1e-4*alpha) {delta=trial;accepted=true;break;}
   }}
  }
  if !accepted {return Err(Error::LineSearch);}
 }Err(Error::IterationLimit)
}

/// Fixed Qa/Q10 collector and left JFET gate currents, including charge and low components.
pub fn observed_currents(now:State,old:State,dt:f64)->Result<[f64;3],vco1_stamp::Error> {
 if !dt.is_finite()||!(MIN_DT_S..=1e-3).contains(&dt)||!domain(now)||!domain(old) {return Err(vco1_stamp::Error::InvalidInput);}
 let mut result=[0.;3];
 for(k,(p,map)) in [(vco_bjt::Polarity::Npn,[43,33,18,N]),(vco_bjt::Polarity::Pnp,[43,21,N,N])].into_iter().enumerate() {
  let dc=vco_bjt::evaluate(p,map.map(|n|value(&now.high,n))).map_err(vco1_stamp::Error::Bjt)?;let(i,_)=bjt_dynamic(p,map,now,old,dt)?;
  result[k]=dc.current_a[0]+(0..4).map(|j|dc.jacobian_s[0][j]*value(&now.low,map[j])).sum::<f64>()+i[0];
 }
 let map=[5,43,4];let dc=vco_jfet::evaluate(map.map(|n|value(&now.high,n))).map_err(vco1_stamp::Error::Jfet)?;let(i,_)=jfet_dynamic(map,now,old,dt)?;
 result[2]=dc.current_a[1]+(0..3).map(|j|dc.jacobian_s[1][j]*now.low[map[j]]).sum::<f64>()+i[1];Ok(result)
}
