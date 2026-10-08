//! Conditional CA3046 VCO1 -> shared BUS -> ladder/VCAs/J7.
//! Explicit OSC1 panel remains in VCO. See VOZ_BUS_CONJUNTO_PROTOCOLO.
use crate::{joint_vco_fine as fine,vco1_stamp::{self,Controls,Mode},chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,output_conversion::solve_linear_sparse,StepError};
pub const N:usize=200;
pub const M:usize=2*N;
pub const BUS:usize=12;
pub const MIN_DT_S:f64=chain_charge::MIN_DT_S;
pub const B:[[f64;2];2]=crate::vco1_radau::B;
pub const fn vco_index(k:usize)->Option<usize> {if k==108 {None} else if k<108 {Some(k)} else {Some(k-1)}}
pub const fn chain_index(k:usize)->usize {if k==66 {BUS} else if k==67 {199} else {133+k}}
#[derive(Clone,Copy)]
pub struct Parameters {pub controls:Controls,chain:Chain,pub sources:[f64;5]}
impl Parameters {
 /// OSC1 always belongs to the VCO panel; other branches retain imposed sources.
 pub fn new(controls:Controls,mut chain:Chain,other_on:[bool;4],alpha:[f64;4],sources:[f64;5])->Result<Self,StepError> {
  if sources.iter().any(|v|!v.is_finite()||v.abs()>40.) {return Err(StepError::InvalidInput);}
  chain.mixer=OnMixer::new([false,other_on[0],other_on[1],other_on[2],other_on[3]],alpha).map_err(|_|StepError::InvalidInput)?;
  Ok(Self{controls,chain,sources})
 }
 pub fn chain(self)->Chain {self.chain}
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct State {pub high:[f64;N],pub low:[f64;N]}
impl State {
 pub fn from_nodes(high:[f64;N])->Self {Self{high,low:[0.;N]}}
 pub fn advanced(self,d:[f64;N])->Self {
  let mut s=self;for k in 0..N {let(h,e)=fine::two_sum(s.high[k],d[k]);let(l,f)=fine::two_sum(s.low[k],e);let(h,l)=fine::two_sum(h,l);(s.high[k],s.low[k])=fine::two_sum(h,l+f);}s
 }
 /// Explicitly lift a conditioned history; the chain BUS is owned by VCO12.
 pub fn lift(vco_high:[f64;134],vco_low:[f64;134],chain:chain_charge::State)->Self {
  let mut s=Self::from_nodes([0.;N]);for k in 0..134 {if let Some(i)=vco_index(k) {s.high[i]=vco_high[k];s.low[i]=vco_low[k];}}
  for k in 0..68 {if k!=66 {let i=chain_index(k);s.high[i]=chain.high[k];s.low[i]=chain.low[k];}}s
 }
 fn vco(self)->fine::State {fine::State{high:std::array::from_fn(|k|vco_index(k).map_or(0.,|i|self.high[i])),low:std::array::from_fn(|k|vco_index(k).map_or(0.,|i|self.low[i]))}}
 fn chain(self)->chain_charge::State {chain_charge::State{high:std::array::from_fn(|k|self.high[chain_index(k)]),low:std::array::from_fn(|k|self.low[chain_index(k)])}}
}
pub struct Parts {pub dc:[f64;N],pub charge_over_h:[f64;N],pub dc_jacobian:[[f64;N];N],pub mass_over_h:[[f64;N];N],pub candidate:State}
pub fn parts(p:Parameters,old:State,delta:State,h:f64)->Result<Parts,StepError> {
 let e=fine::linearize_compensated(old.vco(),delta.vco(),p.controls,h).map_err(|_|StepError::InvalidInput)?;
 let d=vco1_stamp::linearize(e.candidate.high,p.controls,Mode::Dc).map_err(|_|StepError::InvalidInput)?;
 let c=chain_charge::linearize_compensated(p.chain,p.sources,old.chain(),delta.chain(),h)?;
 let mut s=Parts{dc:[0.;N],charge_over_h:[0.;N],dc_jacobian:[[0.;N];N],mass_over_h:[[0.;N];N],candidate:State::from_nodes([0.;N])};
 for a in 0..134 {if let Some(i)=vco_index(a) {
  let f=d.residual[a]+(0..134).map(|b|d.jacobian[a][b]*e.candidate.low[b]).sum::<f64>();
  s.dc[i]+=f;s.charge_over_h[i]+=e.residual[a]-f;s.candidate.high[i]=e.candidate.high[a];s.candidate.low[i]=e.candidate.low[a];
  for b in 0..134 {if let Some(j)=vco_index(b) {s.dc_jacobian[i][j]+=d.jacobian[a][b];s.mass_over_h[i][j]+=e.jacobian[a][b]-d.jacobian[a][b];}}
 }}
 for a in 0..68 {let i=chain_index(a);s.dc[i]+=c.dc[a];s.charge_over_h[i]+=c.charge_over_h[a];
  if a!=66 {s.candidate.high[i]=c.candidate.high[a];s.candidate.low[i]=c.candidate.low[a];}
  for b in 0..68 {let j=chain_index(b);s.dc_jacobian[i][j]+=c.dc_jacobian[a][b];s.mass_over_h[i][j]+=c.mass_over_h[a][b];}
 }
 if s.dc.iter().chain(s.charge_over_h.iter()).chain(s.dc_jacobian.iter().flatten()).chain(s.mass_over_h.iter().flatten()).any(|v|!v.is_finite()) {return Err(StepError::ExponentialDomain);}Ok(s)
}
pub fn constraint_row(p:Parameters,k:usize)->bool { (98..133).contains(&k) || (k>=133&&chain_charge::constraint_row(p.chain,if k==199 {67} else {k-133})) }
fn current_unknown(k:usize)->bool {(98..133).contains(&k)}
pub struct Stamp {pub residual:[f64;M],pub jacobian:[[f64;M];M],pub candidates:[State;2]}
pub fn linearize(p:Parameters,old:State,delta:[State;2],h:f64)->Result<Stamp,StepError> {
 let q=[parts(p,old,delta[0],h)?,parts(p,old,delta[1],h)?];
 Ok(Stamp {residual:std::array::from_fn(|k|{let i=k/N;let a=k%N;q[i].dc[a]+B[i][0]*q[0].charge_over_h[a]+B[i][1]*q[1].charge_over_h[a]}),
  jacobian:std::array::from_fn(|k|std::array::from_fn(|l|{let i=k/N;let j=l/N;let a=k%N;let b=l%N;B[i][j]*q[j].mass_over_h[a][b]+if i==j {q[i].dc_jacobian[a][b]} else {0.}})),candidates:[q[0].candidate,q[1].candidate]})
}
fn merit(p:Parameters,r:&[f64;M])->f64 {r.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if constraint_row(p,k%N) {1e-11} else {1e-13}))}
fn correction(d:&[f64;M])->f64 {d.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if current_unknown(k%N) {2e-12} else {2e-9}))}
pub struct Pair {pub candidates:[State;2],pub increments:[State;2],pub residual_ratio:f64,pub correction_ratio:f64,pub iterations:usize,pub trials:usize}
/// Pure candidate solve. The caller publishes both block histories together.
pub fn step(p:Parameters,old:State,h:f64)->Result<Pair,StepError> {
 let mut delta=[State::from_nodes([0.;N]);2];let mut trials=0;
 for iteration in 1..=64 {
  let s=linearize(p,old,delta,h)?;let norm=merit(p,&s.residual);let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|k|-s.residual[k]))?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {return Ok(Pair{candidates:s.candidates,increments:delta,residual_ratio:norm,correction_ratio:ratio,iterations:iteration,trials});}
  let mut accepted=false;
  for power in 0..24 {let alpha=2_f64.powi(-power);let trial=std::array::from_fn(|i|delta[i].advanced(std::array::from_fn(|a|alpha*d[i*N+a])));trials+=1;
   if let Ok(t)=linearize(p,old,trial,h) {if let Ok(dd)=solve_linear_sparse(t.jacobian,std::array::from_fn(|k|-t.residual[k])) {let next=correction(&dd);
    if (merit(p,&t.residual)<=1.&&next<=1.)||merit(p,&t.residual)<norm*(1.-1e-4*alpha) {delta=trial;accepted=true;break;}
   }}
  }
  if !accepted {return Err(StepError::NoDecrease);}
 }Err(StepError::IterationBudget)
}
