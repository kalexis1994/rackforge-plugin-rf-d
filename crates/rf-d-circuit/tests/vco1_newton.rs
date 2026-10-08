use rf_d_circuit::vco1_newton::{solve,Boundary,Budget,Error};
use rf_d_circuit::vco1_stamp::{linearize,Controls,C4,Mode,Memory,N,NV};
fn controls(v:&[f64])->Controls {Controls{r8_fraction:v[0],r11_ohm:v[1],c4:if v[2]==1e-11 {C4::Schematic10Pf} else {C4::Bom100Pf},mixer_v:v[3],external_neg4_load_a:v[4],cv_v:v[5..11].try_into().unwrap()}}
fn dcrows()->Vec<Vec<f64>> {include_str!("../../../evidence/voice_vco1_newton_startup01.txt").lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn close(a:f64,b:f64,gate:f64) {assert!(a.is_finite()&&b.is_finite()&&(a-b).abs()<=gate,"{a:e} vs {b:e},gate={gate:e}");}
#[test]
fn conditioned_dc_and_six_own_short_continuations() {
 let seeds=dcrows();assert_eq!(seeds.len(),2);let mut dcsolutions=Vec::new();let mut max_v:f64=0.;let mut max_a:f64=0.;let mut max_it=0;let mut max_trials=0;
 for v in &seeds {
  assert_eq!(v.len(),12+2*N);let c=controls(v);let initial=v[11..11+N].try_into().unwrap();let p=solve(c,Mode::Dc,Boundary::StartupRampZero,initial,Budget::default()).unwrap();assert_eq!(p.candidate,Memory{state:p.nodes});assert!(p.residual_ratio<=1.&&p.correction_ratio<=1.);assert_eq!(p.nodes[43],0.);
  for k in 0..N {let delta=(p.nodes[k]-v[11+N+k]).abs();if k<NV {max_v=max_v.max(delta);} else {max_a=max_a.max(delta);}close(p.nodes[k],v[11+N+k],if k<NV {2e-7} else {2e-10});}
  close(p.startup_current_a.unwrap(),v[11+2*N],2e-10);let mut stamp=linearize(p.nodes,c,Mode::Dc).unwrap();stamp.residual[43]+=p.startup_current_a.unwrap();assert!(stamp.residual.iter().all(|r|r.abs()<=1e-11));max_it=max_it.max(p.iterations);max_trials=max_trials.max(p.trials);dcsolutions.push(p.nodes);
 }
 let mut previous=[0.;N];let mut profiles=0;let mut steps=0;
 for line in include_str!("../../../evidence/voice_vco1_newton_trajectory01.txt").lines() {
  let v:Vec<f64>=line.split_whitespace().map(|s|s.parse().unwrap()).collect();assert_eq!(v.len(),13+N);let c=controls(&v);let dt=v[11];let index=v[12] as usize;
  if index==1 {profiles+=1;previous=dcsolutions[if c.c4==C4::Schematic10Pf {0} else {1}];}
  let incoming=Memory{state:previous};let p=solve(c,Mode::Euler{dt_s:dt,previous:incoming},Boundary::Free,previous,Budget::default()).unwrap();assert_eq!(incoming.state,previous);assert_eq!(p.candidate,Memory{state:p.nodes});assert!(p.startup_current_a.is_none());assert!(p.residual_ratio<=1.&&p.correction_ratio<=1.);
  let s=linearize(p.nodes,c,Mode::Euler{dt_s:dt,previous:incoming}).unwrap();assert!(s.residual[..NV].iter().all(|r|r.abs()<=1e-13));assert!(s.residual[NV..].iter().all(|r|r.abs()<=1e-11));assert!((s.residual[..NV].iter().sum::<f64>()+s.ground_current_a).abs()<1e-11);
  for k in 0..N {let delta=(p.nodes[k]-v[13+k]).abs();if k<NV {max_v=max_v.max(delta);} else {max_a=max_a.max(delta);}close(p.nodes[k],v[13+k],if k<NV {2e-7} else {2e-10});}max_it=max_it.max(p.iterations);max_trials=max_trials.max(p.trials);previous=p.nodes;steps+=1;
 }
 assert_eq!(profiles,6);assert_eq!(steps,224);println!("VCO1_NEWTON,dc=2,profiles=6,steps=224,max_node_v={max_v:.17e},max_branch_a={max_a:.17e},max_iterations={max_it},max_trials={max_trials}");
}
#[test]
fn rejection_and_retry_are_atomic_and_pure() {
 let bank=dcrows();let v=&bank[0];let c=controls(v);let initial:[f64;N]=v[11..11+N].try_into().unwrap();let before=initial;
 let budget=Budget{iterations:1,halvings:24};assert!(matches!(solve(c,Mode::Dc,Boundary::StartupRampZero,initial,budget),Err(Error::IterationLimit)));assert!(matches!(solve(c,Mode::Dc,Boundary::StartupRampZero,initial,budget),Err(Error::IterationLimit)));assert_eq!(initial,before);
 let a=solve(c,Mode::Dc,Boundary::StartupRampZero,initial,Budget::default()).unwrap();let b=solve(c,Mode::Dc,Boundary::StartupRampZero,initial,Budget::default()).unwrap();assert_eq!(a.nodes,b.nodes);assert_eq!(a.candidate,b.candidate);assert_eq!(a.startup_current_a,b.startup_current_a);assert_eq!(a.iterations,b.iterations);assert_eq!(a.trials,b.trials);
 let previous=a.candidate;assert_eq!(solve(c,Mode::Euler{dt_s:125e-9,previous},Boundary::StartupRampZero,a.nodes,Budget::default()).unwrap_err(),Error::InvalidInput);
 for budget in [Budget{iterations:0,halvings:1},Budget{iterations:65,halvings:1},Budget{iterations:1,halvings:0},Budget{iterations:1,halvings:25}] {assert_eq!(solve(c,Mode::Dc,Boundary::StartupRampZero,initial,budget).unwrap_err(),Error::InvalidInput);}
 for bad in [f64::NAN,f64::INFINITY,0.,124e-9,1.001e-3] {assert!(solve(c,Mode::Euler{dt_s:bad,previous},Boundary::Free,a.nodes,Budget::default()).is_err());}
 let mut bad=a.nodes;bad[0]=f64::NAN;assert!(solve(c,Mode::Euler{dt_s:125e-9,previous},Boundary::Free,bad,Budget::default()).is_err());let mut cc=c;cc.cv_v[2]=f64::NAN;assert!(solve(cc,Mode::Euler{dt_s:125e-9,previous},Boundary::Free,a.nodes,Budget::default()).is_err());assert_eq!(previous,a.candidate);
}
