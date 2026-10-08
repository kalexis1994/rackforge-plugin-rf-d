use rf_d_circuit::{vco1_adaptive::{advance,Error},vco1_stamp::{Controls,Memory,N},vco1_startup};
#[test]
fn bounded_step_doubling_is_pure_and_transports_both_halves() {
 let c=Controls::default();let x=vco1_startup::startup(c).unwrap().nodes;let mut old=Memory{state:x};let mut proposed=32768;let mut remaining=983040000;let mut steps=0;
 for _ in 0..128 {
  let a=advance(c,old,proposed,16384,remaining).unwrap();let b=advance(c,old,proposed,16384,remaining).unwrap();
  assert_eq!(a.midpoint.nodes,b.midpoint.nodes);assert_eq!(a.endpoint.nodes,b.endpoint.nodes);assert_eq!(a.error_ratio,b.error_ratio);assert_eq!(a.next_full_ticks,b.next_full_ticks);
  assert!(a.error_ratio<=1.&&a.half_ticks>=1&&a.half_ticks<=16384&&a.attempts<=16);assert!(a.midpoint.residual_ratio<=1.&&a.endpoint.residual_ratio<=1.&&a.midpoint.correction_ratio<=1.&&a.endpoint.correction_ratio<=1.);
  remaining-=2*a.half_ticks;proposed=a.next_full_ticks;old=a.endpoint.candidate;steps+=2;
 }
 assert!(old.state[43]<x[43]);println!("VCO1_ADAPTIVE,accepted_half_steps={steps},fixed_error_v=2e-6,fixed_error_a=2e-9");
}
#[test]
fn temporal_floor_failure_is_atomic_and_repeatable() {
 let c=Controls::default();let v:Vec<f64>=include_str!("../../../evidence/voice_vco1_adaptive_failure_history01.txt").split_whitespace().map(|s|s.parse().unwrap()).collect();let x:[f64;N]=v.try_into().unwrap();let old=Memory{state:x};
 let a=advance(c,old,2,16384,944240832).unwrap_err();let b=advance(c,old,2,16384,944240832).unwrap_err();assert_eq!(a,b);assert_eq!(a,Error::Nonlinear(rf_d_circuit::vco1_newton::Error::LineSearch));assert_eq!(old.state,x);
 for (proposal,max,remaining) in [(0,16384,100),(3,16384,100),(32768,0,100),(32768,16384,1),(32768,16384,3),(65536,1024,100)] {assert!(matches!(advance(c,old,proposal,max,remaining),Err(Error::InvalidInput)));}
 println!("VCO1_ADAPTIVE_FLOOR,error={a:?},retry_identical=true,state_unchanged=true");
}
