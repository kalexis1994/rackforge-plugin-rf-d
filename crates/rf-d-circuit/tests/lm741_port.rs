use rf_d_circuit::lm741::{self,Mode,N,NV};
use rf_d_circuit::lm741_port::{self as port,Budget};
fn bank(text:&str)->Vec<Vec<f64>> {text.lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn close(a:f64,e:f64,abs:f64,rel:f64) {assert!((a-e).abs()<=abs+rel*e.abs(),"actual={a:.17e},expected={e:.17e},gate={:.17e}",abs+rel*e.abs());}
fn root(s:&port::Port,expected:&[f64],currents:&[f64])->[f64;3] {
 assert!(s.residual_ratio<=1. && s.correction_ratio<=1.);assert_eq!(s.candidate,lm741::memory(&s.nodes));let mut max=[0_f64;3];
 for i in 0..N {let k=if i<NV {0}else{1};let e=(s.nodes[i]-expected[i]).abs();max[k]=max[k].max(e);close(s.nodes[i],expected[i],if i<NV {2e-7}else{2e-10},0.);}
 for i in 0..5 {let e=(s.current_a[i]-currents[i]).abs();max[2]=max[2].max(e);close(s.current_a[i],currents[i],2e-10,0.);}max
}
fn maxima(a:&mut [f64;3],b:[f64;3]) {for i in 0..3 {a[i]=a[i].max(b[i]);}}
#[test]
fn own_dc_and_672_step_decimal100_trajectories() {
 let mut max=[0_f64;3];let mut rounds=0;let mut halves=0;
 for r in bank(include_str!("../../../evidence/voice_lm741_roots09.txt")) {let p=r[..5].try_into().unwrap();let s=port::dc(p).unwrap();maxima(&mut max,root(&s,&r[..N],&r[N..]));rounds=rounds.max(s.iterations);halves=halves.max(s.halvings);}
 let rows=bank(include_str!("../../../evidence/voice_lm741_port_trajectory12.txt"));assert_eq!(rows.len(),672);let mut previous=port::dc([0.,0.001,12.,-12.,0.]).unwrap();let mut profile=(-1_f64,0_f64);let mut profiles=0;let mut count=0;
 for r in rows {assert_eq!(r.len(),50);if profile!=(r[0],r[1]) {previous=port::dc([0.,0.001,12.,-12.,0.]).unwrap();profile=(r[0],r[1]);profiles+=1;count=0;}
  count+=1;close(r[2],count as f64*r[1],0.,0.);let p=r[3..8].try_into().unwrap();let mode=Mode::Euler{dt_s:r[1],previous:previous.candidate};let s=port::solve(p,mode,previous.nodes,Budget::default()).unwrap();
  maxima(&mut max,root(&s,&r[8..45],&r[45..50]));rounds=rounds.max(s.iterations);halves=halves.max(s.halvings);previous=s;
 }
 assert_eq!(profiles,9);println!("LM741_PORT_TRAJECTORY,dc=6,profiles=9,steps=672,max_node_v={:.17e},max_branch_a={:.17e},max_port_a={:.17e},max_iterations={rounds},max_trials={halves}",max[0],max[1],max[2]);
}
#[test]
fn independent_spice_euler_intervals_with_fixed_history() {
 let rows=bank(include_str!("../../../evidence/voice_lm741_port_spice12.txt"));assert_eq!(rows.len(),371);let mut max=[0_f64;3];let mut rounds=0;
 for r in rows {assert_eq!(r.len(),80);let previous:[f64;N]=r[1..38].try_into().unwrap();let expected=&r[38..75];let p=expected[..5].try_into().unwrap();let mode=Mode::Euler{dt_s:r[0],previous:lm741::memory(&previous)};
  let s=port::solve(p,mode,previous,Budget::default()).unwrap();maxima(&mut max,root(&s,expected,&r[75..80]));rounds=rounds.max(s.iterations);
 }
 println!("LM741_PORT_SPICE,intervals=371,max_node_v={:.17e},max_branch_a={:.17e},max_port_a={:.17e},max_iterations={rounds}",max[0],max[1],max[2]);
}
fn derivatives(p:[f64;5],mode:Mode,initial:[f64;N]) {
 let s=port::solve(p,mode,initial,Budget::default()).unwrap();
 for k in 0..5 {let h=if k<2 {1e-9}else{1e-5};let mut plus=p;let mut minus=p;plus[k]+=h;minus[k]-=h;
  let a=port::solve(plus,mode,s.nodes,Budget::default()).unwrap();let b=port::solve(minus,mode,s.nodes,Budget::default()).unwrap();
  for i in 0..N {close(s.node_gradient[i][k],(a.nodes[i]-b.nodes[i])/(2.*h),2e-4,2e-4);}
  for i in 0..5 {close(s.admittance[i][k],(a.current_a[i]-b.current_a[i])/(2.*h),2e-7,2e-4);}
 }
}
#[test]
fn loaded_derivatives_purity_rejections_and_atomic_retry() {
 for r in bank(include_str!("../../../evidence/voice_lm741_roots09.txt")) {let p=r[..5].try_into().unwrap();let a=port::dc(p).unwrap();derivatives(p,Mode::Dc,a.nodes);}
 let rows=bank(include_str!("../../../evidence/voice_lm741_port_spice12.txt"));for r in rows.iter().step_by(41).take(9) {let prev:[f64;N]=r[1..38].try_into().unwrap();let original=prev;let p=r[38..43].try_into().unwrap();let history=lm741::memory(&prev);let mode=Mode::Euler{dt_s:r[0],previous:history};derivatives(p,mode,prev);
  let a=port::solve(p,mode,prev,Budget::default()).unwrap();let b=port::solve(p,mode,prev,Budget::default()).unwrap();assert_eq!(a.nodes,b.nodes);assert_eq!(a.candidate,b.candidate);assert_eq!(a.admittance,b.admittance);assert_eq!(prev,original);assert_eq!(lm741::memory(&prev),history);
 }
 let p=[0.,0.001,12.,-12.,0.];let initial=port::seed(p);let original=initial;assert!(port::solve(p,Mode::Dc,initial,Budget{iterations:1,halvings:1}).is_err());assert_eq!(initial,original);let retried=port::solve(p,Mode::Dc,initial,Budget::default()).unwrap();assert_eq!(retried.nodes,port::dc(p).unwrap().nodes);
 for dt_s in [0.,124e-9,1.01e-3,f64::NAN] {assert!(port::solve(p,Mode::Euler{dt_s,previous:retried.candidate},retried.nodes,Budget::default()).is_err());}
 for i in 0..5 {for bad in [f64::NAN,f64::INFINITY,41.] {let mut invalid=p;invalid[i]=bad;assert!(port::dc(invalid).is_err());}}
 let mut reversed=p;reversed[2]=-12.;reversed[3]=12.;assert!(port::dc(reversed).is_err());assert!(port::seed(reversed).iter().all(|v|v.is_nan()));let mut h=retried.candidate;h.capacitor_v[0]=81.;assert!(port::solve(p,Mode::Euler{dt_s:125e-9,previous:h},retried.nodes,Budget::default()).is_err());
}
