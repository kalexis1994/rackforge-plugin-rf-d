use rf_d_circuit::{vco1_stamp::{self,Controls,C4,Memory,Mode,N,NV},vco1_substep,vco1_newton::{Boundary,Budget},vco1_startup};
fn controls(v:&[f64])->Controls {Controls{r8_fraction:v[0],r11_ohm:v[1],c4:if v[2]==1e-11 {C4::Schematic10Pf} else {C4::Bom100Pf},mixer_v:v[3],external_neg4_load_a:v[4],cv_v:v[5..11].try_into().unwrap()}}
fn rows()->Vec<Vec<f64>> {include_str!("../../../evidence/voice_vco1_substep_vectors02.txt").lines().map(|l|l.split_whitespace().map(|s|s.parse().unwrap()).collect()).collect()}
#[test]
fn all_short_stamps_and_available_independent_roots() {
 let pattern:Vec<(usize,usize)>=include_str!("../../../evidence/voice_vco1_stamp_pattern08.txt").lines().map(|l|{let v:Vec<usize>=l.split_whitespace().map(|s|s.parse().unwrap()).collect();(v[0],v[1])}).collect();
 let bank=rows();assert_eq!(bank.len(),48);let mut roots=0;let mut mr=0_f64;let mut mj=0_f64;let mut mn=0_f64;let mut mb=0_f64;
 for v in bank {
  let c=controls(&v);let x=v[11..11+N].try_into().unwrap();let old=v[11+N..11+2*N].try_into().unwrap();let dt=v[11+2*N];let k=12+2*N;assert_eq!(v.len(),k+N+1+pattern.len()+N);
  let m=Mode::Euler{dt_s:dt,previous:Memory{state:old}};let s=vco1_substep::linearize(x,c,m).unwrap();let mut expected=[[0.;N];N];
  for (i,&(a,b)) in pattern.iter().enumerate() {expected[a][b]=v[k+N+1+i];}
  for a in 0..N {let d=(s.residual[a]-v[k+a]).abs();mr=mr.max(d);assert!(d<=2e-12+2e-11*v[k+a].abs());
   for b in 0..N {let d=(s.jacobian[a][b]-expected[a][b]).abs();mj=mj.max(d);assert!(d<=2e-12+2e-11*expected[a][b].abs(),"J {a} {b}: {d:e}");}}
  assert!((s.ground_current_a-v[k+N]).abs()<=2e-12+2e-11*v[k+N].abs());assert!((s.residual[..NV].iter().sum::<f64>()+s.ground_current_a).abs()<1e-11);assert_eq!(s.candidate.state,x);
  let root=&v[k+N+1+pattern.len()..];
  // All-zero placeholder explicitly denotes a rejected independent solve, never a fixture root.
  if root.iter().any(|x|*x!=0.) {
   let p=vco1_substep::solve(c,m,Boundary::Free,old,Budget::default()).unwrap();assert!(p.residual_ratio<=1.&&p.correction_ratio<=1.);
   for i in 0..N {let d=(p.nodes[i]-root[i]).abs();if i<NV {mn=mn.max(d);assert!(d<=2e-7);} else {mb=mb.max(d);assert!(d<=2e-10);}}
   roots+=1;
  }
 }
 println!("VCO1_SUBSTEP,stamps=48,all_jac_entries=861888,available_roots={roots},max_residual={mr:.17e},max_jacobian={mj:.17e},max_node_v={mn:.17e},max_branch_a={mb:.17e}");
}
#[test]
fn legacy_delegation_and_atomic_rejection() {
 for line in include_str!("../../../evidence/voice_vco1_stamp_vectors08.txt").lines() {
  let v:Vec<f64>=line.split_whitespace().map(|s|s.parse().unwrap()).collect();let x=v[11..11+N].try_into().unwrap();let dt=v[11+2*N];let m=if dt==0. {Mode::Dc} else {Mode::Euler{dt_s:dt,previous:Memory{state:v[11+N..11+2*N].try_into().unwrap()}}};let c=controls(&v);
  let a=vco1_stamp::linearize(x,c,m).unwrap();let b=vco1_substep::linearize(x,c,m).unwrap();assert_eq!(a.residual,b.residual);assert_eq!(a.jacobian,b.jacobian);assert_eq!(a.ground_current_a,b.ground_current_a);assert_eq!(a.candidate,b.candidate);
 }
 let c=Controls::default();let x=vco1_startup::startup(c).unwrap().nodes;let old=Memory{state:x};
 for dt in [0.,f64::NAN,f64::INFINITY,vco1_substep::MIN_DT_S/2.,1.001e-3] {assert!(vco1_substep::linearize(x,c,Mode::Euler{dt_s:dt,previous:old}).is_err());}
 let m=Mode::Euler{dt_s:62.5e-9,previous:old};let a=vco1_substep::solve(c,m,Boundary::Free,x,Budget::default()).unwrap();
 assert!(vco1_substep::solve(c,m,Boundary::Free,x,Budget{iterations:1,halvings:24}).is_err());let b=vco1_substep::solve(c,m,Boundary::Free,x,Budget::default()).unwrap();assert_eq!(a.nodes,b.nodes);assert_eq!(a.candidate,b.candidate);assert_eq!(old.state,x);
}
