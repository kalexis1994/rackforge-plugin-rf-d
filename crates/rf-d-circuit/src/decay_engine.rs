//! Conditional joint reference engine; no audio-thread/deadline admission.
//! Temporal gates inherited from VCO engine. See VOZ_MOTOR_TEMPORAL_PROTOCOLO.
use crate::decay_voice::{self as joint,State,N,Workspace};
use crate::StepError;
fn two_sum(a:f64,b:f64)->(f64,f64){let s=a+b;let v=s-a;(s,(a-(s-v))+(b-v))}
pub const TICK_S:f64=crate::vco1_engine::TICK_S;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Settings {pub maximum_half_ticks:u32,pub attempt_limit:u32}
impl Default for Settings {fn default()->Self {Self{maximum_half_ticks:65536,attempt_limit:20}}}
impl Settings {fn valid(self)->bool {(4..=1048576).contains(&self.maximum_half_ticks)&&self.maximum_half_ticks.is_power_of_two()&&(1..=20).contains(&self.attempt_limit)}}
#[derive(Clone,Copy)]
pub struct Checkpoint {pub state:State,pub parameters:joint::Parameters,pub settings:Settings,pub elapsed_ticks:u64,pub next_full_ticks:u32}
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Rejection {Nonlinear(StepError),LocalError(f64)}
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Error {InvalidInput,PrecisionLimit(Rejection),AttemptLimit(Rejection),Observation}
pub struct Engine {checkpoint:Checkpoint}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Observations {pub saw_v:f64,pub ramp_v:f64,pub bus_v:f64,pub cursor_v:f64,pub j7_v:f64,pub panel_current_a:f64,pub series_current_a:f64,pub c27_current_a:f64,pub bus_kcl_a:f64}
pub struct Endpoint {pub elapsed_ticks:u64,pub pair:joint::Pair,pub observations:Observations}
pub struct Accepted {pub coarse:joint::Pair,pub endpoints:[Endpoint;2],pub half_ticks:u32,pub error_ratio:f64,pub attempts:u32}
fn add(h:f64,l:f64,d:f64)->(f64,f64) {let(s,e)=two_sum(h,d);let(t,f)=two_sum(l,e);let(u,v)=two_sum(s,t);two_sum(u,v+f)}
pub fn difference(a:State,b:State)->[f64;N] {std::array::from_fn(|k|{let(h,l)=add(a.high[k],a.low[k],-b.high[k]);let(h,l)=add(h,l,-b.low[k]);h+l})}
pub fn error_ratio(a:State,b:State)->f64 {difference(a,b).iter().enumerate().fold(0_f64,|n,(k,v)|n.max(v.abs()/if (98..133).contains(&k) {2e-9} else {2e-6}))}
fn branch(s:State,a:usize,b:usize)->f64 {let(h,l)=add(s.high[a],s.low[a],-s.high[b]);let(h,l)=add(h,l,-s.low[b]);h+l}
fn endpoint(p:joint::Parameters,pair:joint::Pair,h:f64,elapsed_ticks:u64)->Result<Endpoint,Error> {
 let s=pair.candidates[1];let value=|k|s.high[k]+s.low[k];
 let c27=10e-6/h*(joint::B[1][0]*branch(pair.increments[0],12,joint::chain_index(6))+joint::B[1][1]*branch(pair.increments[1],12,joint::chain_index(6)));
 let mixer=p.chain().mixer;let port=mixer.evaluate([p.sources[0],p.sources[1],p.sources[2],p.sources[3],p.sources[4],s.high[12]]).map_err(|_|Error::Observation)?;
 let series=branch(s,12,39)/33000.;let bus_kcl=series+port.current_a[5]+mixer.admittance_s()[5][5]*s.low[12]+c27;
 let observations=Observations{saw_v:value(46),ramp_v:value(43),bus_v:value(12),cursor_v:value(39),j7_v:value(joint::chain_index(61)),panel_current_a:branch(s,46,39)/12500.,series_current_a:series,c27_current_a:c27,bus_kcl_a:bus_kcl};
 if [observations.saw_v,observations.ramp_v,observations.bus_v,observations.cursor_v,observations.j7_v,observations.panel_current_a,series,c27,bus_kcl].iter().any(|v|!v.is_finite()) {return Err(Error::Observation);}
 Ok(Endpoint{elapsed_ticks,pair,observations})
}
impl Engine {
 /// Takes an explicit conditioned history; does not establish joint DC startup.
 pub fn from_conditioned(parameters:joint::Parameters,state:State,settings:Settings)->Result<Self,Error> {
  Self::restore(Checkpoint{state,parameters,settings,elapsed_ticks:0,next_full_ticks:settings.maximum_half_ticks.saturating_mul(2)})
 }
 /// Validates representation, domains and clock; provenance belongs to evidence.
 pub fn restore(q:Checkpoint)->Result<Self,Error> {
  if !q.settings.valid()||q.elapsed_ticks%8!=0||q.next_full_ticks<8||!q.next_full_ticks.is_power_of_two()||q.next_full_ticks>2*q.settings.maximum_half_ticks {return Err(Error::InvalidInput);}
  if !q.parameters.keyboard.is_finite()||!(0. ..=10.).contains(&q.parameters.keyboard){return Err(Error::InvalidInput);}
  let mut trial=[0.;N];
  if q.parameters.keyboard-(q.state.high[222]+q.state.low[222])>0.5{trial[222]=q.parameters.keyboard-0.5-q.state.high[222]-q.state.low[222];}
  joint::parts(q.parameters,q.state,State::from_nodes(trial),4.*TICK_S).map_err(|_|Error::InvalidInput)?;
  Ok(Self{checkpoint:q})
 }
 /// Explicit ideal sources; no state or accepted charge is assigned.
 pub fn trigger(&mut self,key:f64,short:bool)->Result<(),Error>{
  if !key.is_finite()||!(0. ..=10.).contains(&key){return Err(Error::InvalidInput);}
  self.checkpoint.parameters.keyboard=key;self.checkpoint.parameters.short=short;Ok(())
 }
 /// Ideal parameter event; state, charges, clock and proposal are preserved.
 pub fn set_decay_ohm(&mut self,ohm:f64)->Result<(),Error>{if !joint::Parameters::valid_decay(ohm){return Err(Error::InvalidInput);}self.checkpoint.parameters.decay_ohm=ohm;Ok(())}
 pub fn checkpoint(&self)->Checkpoint {self.checkpoint}
 /// Advance one accepted pair only, never beyond target. All errors are atomic.
 pub fn advance_to(&mut self,workspace:&mut Workspace,target_ticks:u64)->Result<Accepted,Error> {
  let q=self.checkpoint;
  if target_ticks<=q.elapsed_ticks||target_ticks%8!=0 {return Err(Error::InvalidInput);}
  let remaining=target_ticks-q.elapsed_ticks;let mut ticks=q.next_full_ticks;
  while u64::from(ticks)>remaining {ticks/=2;}
  for attempts in 1..=q.settings.attempt_limit {
   let h=f64::from(ticks/2)*TICK_S;
   let trial=(|| {let coarse=workspace.step(q.parameters,q.state,2.*h)?;let mid=workspace.step(q.parameters,q.state,h)?;let end=workspace.step(q.parameters,mid.candidates[1],h)?;
    let error=error_ratio(coarse.candidates[1],end.candidates[1]);Ok::<_,StepError>((coarse,mid,end,error))})();
   let reason=match trial {
    Ok((coarse,mid,end,e)) if e.is_finite()&&e<=1.=> {
     let state=end.candidates[1];let end_clock=q.elapsed_ticks+u64::from(ticks);
     let endpoints=[endpoint(q.parameters,mid,h,q.elapsed_ticks+u64::from(ticks/2))?,endpoint(q.parameters,end,h,end_clock)?];
     self.checkpoint=Checkpoint{state,elapsed_ticks:end_clock,next_full_ticks:if e<=0.25 {(ticks*2).min(2*q.settings.maximum_half_ticks)} else {ticks},..q};
     return Ok(Accepted{coarse,endpoints,half_ticks:ticks/2,error_ratio:e,attempts});
    },
    Ok((_,_,_,e))=>Rejection::LocalError(e),Err(e)=>Rejection::Nonlinear(e),
   };
   if ticks==8 {return Err(Error::PrecisionLimit(reason));}
   if attempts==q.settings.attempt_limit {return Err(Error::AttemptLimit(reason));}
   ticks/=2;
  }unreachable!("positive validated budget")
 }
}
