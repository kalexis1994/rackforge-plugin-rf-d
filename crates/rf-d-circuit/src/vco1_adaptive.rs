//! Step doubling, fixed tolerances; provisional midpoint+endpoint published together.
//! No I/O/heap and no waveform thresholds. See VCO1_SUBPASOS_PROTOCOLO.md.
use crate::{vco1_substep,vco1_stamp::{Controls,Memory,Mode,N,NV},vco1_newton::{Boundary,Budget,Solution}};
pub const TICK_S:f64=vco1_substep::MIN_DT_S;
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Error {InvalidInput,Nonlinear(crate::vco1_newton::Error),PrecisionLimit,AttemptLimit}
#[derive(Debug)]
pub struct Candidate {pub midpoint:Solution,pub endpoint:Solution,pub half_ticks:u32,pub next_full_ticks:u32,pub error_ratio:f64,pub attempts:u32}
/// Limits and remaining time are integer ticks. Every retry keeps `previous` unchanged.
pub fn advance(c:Controls,previous:Memory,proposed_full_ticks:u32,maximum_half_ticks:u32,remaining_ticks:u32)->Result<Candidate,Error> {
 if !proposed_full_ticks.is_power_of_two()||proposed_full_ticks<2||!maximum_half_ticks.is_power_of_two()||maximum_half_ticks>32768||proposed_full_ticks>2*maximum_half_ticks||remaining_ticks<2||remaining_ticks%2!=0 {return Err(Error::InvalidInput);}
 let mut ticks=proposed_full_ticks;
 while ticks>remaining_ticks {ticks/=2;}
 for attempts in 1..=16 {
  let solve=|old:Memory,dt:f64|vco1_substep::solve(c,Mode::Euler{dt_s:dt,previous:old},Boundary::Free,old.state,Budget::default());
  let trial=(||{
   let full=solve(previous,ticks as f64*TICK_S)?;
   let mid=solve(previous,(ticks/2) as f64*TICK_S)?;
   let end=solve(mid.candidate,(ticks/2) as f64*TICK_S)?;
   let error=(0..N).fold(0_f64,|a,k|a.max((full.nodes[k]-end.nodes[k]).abs()/if k<NV {2e-6} else {2e-9}));
   Ok::<_,crate::vco1_newton::Error>((mid,end,error))
  })();
  match trial {
   Ok((midpoint,endpoint,error_ratio)) if error_ratio<=1.=>return Ok(Candidate{midpoint,endpoint,half_ticks:ticks/2,next_full_ticks:if error_ratio<=0.25 {(ticks*2).min(2*maximum_half_ticks)} else {ticks},error_ratio,attempts}),
   Ok(_)=>if ticks==2 {return Err(Error::PrecisionLimit);},
   Err(e)=>if ticks==2 {return Err(Error::Nonlinear(e));},
  }
  ticks/=2;
 }
 Err(Error::AttemptLimit)
}
