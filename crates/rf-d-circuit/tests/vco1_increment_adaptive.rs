use rf_d_circuit::{vco1_increment_adaptive::{advance,Error},vco1_increment::State,vco1_stamp::{Controls,N},vco1_startup};
#[test]
fn accepted_pair_transports_complete_memory_and_clock() {
 let c=Controls::default();let mut old=State::from_nodes(vco1_startup::startup(c).unwrap().nodes);let mut proposed=32768;let mut remaining=983040000;
 for _ in 0..128 {
  let a=advance(c,old,proposed,16384,remaining).unwrap();let b=advance(c,old,proposed,16384,remaining).unwrap();
  assert_eq!(a.midpoint.candidate,b.midpoint.candidate);assert_eq!(a.endpoint.candidate,b.endpoint.candidate);assert_eq!(a.error_ratio,b.error_ratio);assert_eq!(a.next_full_ticks,b.next_full_ticks);
  assert!(a.error_ratio<=1.&&a.half_ticks>=1&&a.half_ticks<=16384&&a.attempts<=16);
  assert!(a.midpoint.residual_ratio<=1.&&a.endpoint.residual_ratio<=1.&&a.midpoint.correction_ratio<=1.&&a.endpoint.correction_ratio<=1.);
  assert_eq!(a.midpoint.candidate,old.advanced(a.midpoint.delta));assert_eq!(a.endpoint.candidate,a.midpoint.candidate.advanced(a.endpoint.delta));
  remaining-=2*a.half_ticks;proposed=a.next_full_ticks;old=a.endpoint.candidate;
 }
 println!("VCO1_INCREMENT_ADAPTIVE,pairs=128,retry_identical=true,complete_memory=true");
}
#[test]
fn preserved_precision_floor_recovers_and_invalid_clock_is_atomic() {
 let c=Controls::default();let values:Vec<f64>=include_str!("../../../evidence/voice_vco1_adaptive_failure_history01.txt").split_whitespace().map(|s|s.parse().unwrap()).collect();let high:[f64;N]=values.try_into().unwrap();let old=State::from_nodes(high);
 let a=advance(c,old,2,16384,944240832).unwrap();let b=advance(c,old,2,16384,944240832).unwrap();
 assert_eq!(a.midpoint.candidate,b.midpoint.candidate);assert_eq!(a.endpoint.candidate,b.endpoint.candidate);assert_eq!(a.half_ticks,1);assert!(a.error_ratio<=1.);assert_ne!(a.endpoint.candidate.low[15],0.);assert_eq!(old,State::from_nodes(high));
 for (proposal,max,remaining) in [(0,16384,100),(3,16384,100),(32768,0,100),(32768,16384,1),(32768,16384,3),(65536,1024,100)] {let a=advance(c,old,proposal,max,remaining).unwrap_err();let b=advance(c,old,proposal,max,remaining).unwrap_err();assert_eq!(a,Error::InvalidInput);assert_eq!(a,b);assert_eq!(old,State::from_nodes(high));}
 println!("VCO1_INCREMENT_ADAPTIVE_FLOOR,recovered=true,invalid_clock_atomic=true");
}
