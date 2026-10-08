use rf_d_circuit::{vco1_startup::{startup,seed},vco1_stamp::{Controls,C4,Mode,linearize,N,NV},vco1_newton};
#[test]
fn own_startup_nominal_and_reserved_controls() {
 let old:Vec<Vec<f64>>=include_str!("../../../evidence/voice_vco1_stamp_startup08.txt").lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect();
 let mut max_it=0;let mut max_node:f64=0.;let mut max_branch:f64=0.;let mut count=0;
 for (profile,c4) in [C4::Schematic10Pf,C4::Bom100Pf].into_iter().enumerate() {
  for scene in 0..5 {
   let mut c=Controls::default();c.c4=c4;
   if scene>0 {c.r8_fraction=0.26134047;c.r11_ohm=521.31266;c.cv_v[2]=[-3.1,-2.1,-1.1,-0.1][scene-1];}
   let guess=seed(c).unwrap();let s=startup(c).unwrap();assert_eq!(s.nodes[43],0.);assert!(s.residual_ratio<=1.&&s.correction_ratio<=1.);max_it=max_it.max(s.iterations);
   let mut stamp=linearize(s.nodes,c,Mode::Dc).unwrap();stamp.residual[43]+=s.startup_current_a.unwrap();stamp.ground_current_a-=s.startup_current_a.unwrap();assert!(stamp.residual[..NV].iter().all(|v|v.abs()<=1e-13));assert!(stamp.residual[NV..].iter().all(|v|v.abs()<=1e-11));assert!((stamp.residual[..NV].iter().sum::<f64>()+stamp.ground_current_a).abs()<1e-11);
   if scene==0 {for k in 0..N {let delta=(s.nodes[k]-old[profile][11+k]).abs();if k<NV {max_node=max_node.max(delta);assert!(delta<=2e-7);} else {max_branch=max_branch.max(delta);assert!(delta<=2e-10);}}assert!((s.startup_current_a.unwrap()-old[profile][11+N]).abs()<=2e-10);}
   print!("STARTUP_ROOT,{profile},{scene},{:.17e}",s.startup_current_a.unwrap());for v in s.nodes {print!(",{v:.17e}");}println!();
   print!("STARTUP_SEED,{profile},{scene}");for v in guess {print!(",{v:.17e}");}println!();count+=1;
  }
 }
 println!("VCO1_OWN_STARTUP,scenes={count},max_node_v={max_node:.17e},max_branch_a={max_branch:.17e},max_iterations={max_it}");
}
#[test]
fn startup_rejects_invalid_controls_and_repeats_without_state() {
 let c=Controls::default();let a=startup(c).unwrap();let b=startup(c).unwrap();assert_eq!(a.nodes,b.nodes);assert_eq!(a.candidate,b.candidate);assert_eq!(a.startup_current_a,b.startup_current_a);assert_eq!(a.iterations,b.iterations);
 for cv in 0..6 {for value in [f64::NAN,f64::INFINITY,40.01] {let mut bad=c;bad.cv_v[cv]=value;assert!(seed(bad).is_err());}}
 for k in 0..4 {let mut bad=c;match k {0=>bad.r8_fraction=-0.1,1=>bad.r11_ohm=1001.,2=>bad.mixer_v=f64::INFINITY,_=>bad.external_neg4_load_a=1.01};assert!(startup(bad).is_err());}
 let v=vco1_newton::solve(c,Mode::Dc,vco1_newton::Boundary::StartupRampZero,seed(c).unwrap(),vco1_newton::Budget{iterations:1,halvings:24});assert!(v.is_err());let retry=startup(c).unwrap();assert_eq!(retry.nodes,a.nodes);
}
