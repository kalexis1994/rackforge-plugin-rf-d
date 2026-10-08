use rf_d_circuit::{vco1_increment::{self,State},vco1_stamp::{Controls,C4,N,NV},vco1_newton::Budget,vco1_startup};
fn controls(v:&[f64])->Controls {Controls{r8_fraction:v[0],r11_ohm:v[1],c4:if v[2]==1e-11 {C4::Schematic10Pf} else {C4::Bom100Pf},mixer_v:v[3],external_neg4_load_a:v[4],cv_v:v[5..11].try_into().unwrap()}}
#[test]
fn full_decimal_stamps_and_fifty_increment_roots() {
 let pattern:Vec<(usize,usize)>=include_str!("../../../evidence/voice_vco1_stamp_pattern08.txt").lines().map(|l|{let v:Vec<usize>=l.split_whitespace().map(|s|s.parse().unwrap()).collect();(v[0],v[1])}).collect();
 let mut count=0;let mut mr=0_f64;let mut mj=0_f64;let mut mn=0_f64;let mut mb=0_f64;let mut floor_low=0_f64;
 for line in include_str!("../../../evidence/voice_vco1_increment_vectors01.txt").lines() {
  let v:Vec<f64>=line.split_whitespace().map(|s|s.parse().unwrap()).collect();let c=controls(&v);let previous=State{high:v[11..11+N].try_into().unwrap(),low:v[11+N..11+2*N].try_into().unwrap()};let delta=v[11+2*N..11+3*N].try_into().unwrap();let dt=v[11+3*N];let k=12+3*N;assert_eq!(v.len(),k+N+1+pattern.len()+2*N);
  let s=vco1_increment::linearize(previous,delta,c,dt).unwrap();let mut j=[[0.;N];N];for (i,&(a,b)) in pattern.iter().enumerate() {j[a][b]=v[k+N+1+i];}
  for a in 0..N {let d=(s.residual[a]-v[k+a]).abs();mr=mr.max(d);assert!(d<=2e-12+2e-11*v[k+a].abs(),"R {a}: {d:e}");for b in 0..N {let d=(s.jacobian[a][b]-j[a][b]).abs();mj=mj.max(d);assert!(d<=2e-12+2e-11*j[a][b].abs(),"J {a}/{b}: {d:e}");}}
  assert!((s.ground_current_a-v[k+N]).abs()<=2e-12+2e-11*v[k+N].abs());assert!((s.residual[..NV].iter().sum::<f64>()+s.ground_current_a).abs()<1e-11);
  let p=vco1_increment::solve(c,previous,dt,Budget::default()).unwrap();assert!(p.residual_ratio<=1.&&p.correction_ratio<=1.);let check=vco1_increment::linearize(previous,p.delta,c,dt).unwrap();assert_eq!(check.candidate,p.candidate);
  assert!(check.residual[..NV].iter().all(|r|r.abs()<=1e-13));assert!(check.residual[NV..].iter().all(|r|r.abs()<=1e-11));
  let off=k+N+1+pattern.len();let expected=State{high:v[off..off+N].try_into().unwrap(),low:v[off+N..off+2*N].try_into().unwrap()};
  for (i,d) in p.candidate.difference(expected).into_iter().enumerate() {if i<NV {mn=mn.max(d.abs());assert!(d.abs()<=2e-7);} else {mb=mb.max(d.abs());assert!(d.abs()<=2e-10);}}
  if count>=48 {assert!(p.candidate.low[15]!=0.);floor_low=floor_low.max(p.candidate.low[15].abs());}
  count+=1;
 }
 assert_eq!(count,50);println!("VCO1_INCREMENT,roots=50,stamps=50,all_jac_entries=897800,max_residual={mr:.17e},max_jacobian={mj:.17e},max_node_v={mn:.17e},max_branch_a={mb:.17e},floor_low_v={floor_low:.17e}");
}
#[test]
fn expanded_memory_preserves_updates_and_atomic_failures() {
 let sums:Vec<Vec<f64>>=include_str!("../../../evidence/voice_vco1_increment_sum01.txt").lines().map(|l|l.split_whitespace().map(|s|s.parse().unwrap()).collect()).collect();assert_eq!(sums.len(),110);
 for v in sums {assert_eq!(vco1_increment::two_sum(v[0],v[1]),(v[2],v[3]));}
 let mut old=State::from_nodes([0.;N]);old.high[15]=-4.;let start=old;let mut delta=[0.;N];delta[15]=1e-16;for _ in 0..100000 {old=old.advanced(delta);}
 assert!((old.difference(start)[15]-1e-11).abs()<1e-25);assert!(old.low[15]!=0.);
 let c=Controls::default();let previous=State::from_nodes(vco1_startup::startup(c).unwrap().nodes);
 for dt in [0.,f64::NAN,f64::INFINITY,vco1_increment::MIN_DT_S/2.,1.001e-3] {assert!(vco1_increment::solve(c,previous,dt,Budget::default()).is_err());}
 let mut bad=previous;bad.low[15]=1e-8;assert!(vco1_increment::linearize(bad,[0.;N],c,125e-9).is_err());bad.low[15]=f64::NAN;assert!(vco1_increment::linearize(bad,[0.;N],c,125e-9).is_err());
 let a=vco1_increment::solve(c,previous,62.5e-9,Budget::default()).unwrap();assert!(vco1_increment::solve(c,previous,62.5e-9,Budget{iterations:1,halvings:24}).is_err());let b=vco1_increment::solve(c,previous,62.5e-9,Budget::default()).unwrap();assert_eq!(a.candidate,b.candidate);assert_eq!(a.delta,b.delta);
 println!("VCO1_INCREMENT_MEMORY,two_sum=110,sub_ulp_updates=100000,retry_identical=true");
}
