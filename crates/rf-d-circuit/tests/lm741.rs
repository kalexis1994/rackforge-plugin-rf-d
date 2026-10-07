use rf_d_circuit::lm741::{self as op,Memory,Mode,Error,N,NV};
fn bank(text:&str)->Vec<Vec<f64>> {text.lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn close(a:f64,e:f64,abs:f64,rel:f64) {assert!((a-e).abs()<=abs+rel*e.abs(),"actual={a:0.17e},expected={e:0.17e},gate={:0.17e}",abs+rel*e.abs());}
fn args(r:&[f64])->([f64;N],Mode) {let x=r[..N].try_into().unwrap();let h=Memory{capacitor_v:r[38..41].try_into().unwrap(),inductor_i_a:r[41..43].try_into().unwrap()};(x,if r[N]==0. {Mode::Dc} else {Mode::Euler{dt_s:r[N],previous:h}})}
#[test]
fn decimal100_full_stamp_and_six_independent_roots() {
 let rows=bank(include_str!("../../../evidence/voice_lm741_vectors09.txt"));assert_eq!(rows.len(),60);let mut max=[0_f64;4];
 for r in rows {assert_eq!(r.len(),1455);let (x,mode)=args(&r);let s=op::linearize(x,mode).unwrap();
  for i in 0..N {let a=if i<NV {1e-14} else {1e-11};close(s.residual[i],r[43+i],a,3e-12);max[if i<NV {0} else {1}]=max[if i<NV {0} else {1}].max((s.residual[i]-r[43+i]).abs());
   for j in 0..N {let a=if i<NV {1e-12} else {1e-10};close(s.jacobian[i][j],r[80+i*N+j],a,3e-12);max[if i<NV {2} else {3}]=max[if i<NV {2} else {3}].max((s.jacobian[i][j]-r[80+i*N+j]).abs());}
  }
  for (a,e) in s.candidate.capacitor_v.iter().chain(s.candidate.inductor_i_a.iter()).zip(&r[1449..1454]) {close(*a,*e,2e-14,3e-12);}
  close(s.ground_current_a,r[1454],1e-24,3e-12);
  let sum=s.residual[..NV].iter().sum::<f64>()+s.ground_current_a;let scale=s.residual[..NV].iter().map(|v|v.abs()).sum::<f64>();assert!(sum.abs()<=2e-14+3e-14*scale);
 }
 let roots=bank(include_str!("../../../evidence/voice_lm741_roots09.txt"));assert_eq!(roots.len(),6);let mut ports=0_f64;
 for r in roots {assert_eq!(r.len(),42);let s=op::linearize(r[..N].try_into().unwrap(),Mode::Dc).unwrap();
  for i in 5..NV {assert!(s.residual[i].abs()<=1e-11,"DC KCL row {i}: {}",s.residual[i]);}
  for i in NV..N {assert!(s.residual[i].abs()<=1e-11,"DC constraint row {i}: {}",s.residual[i]);}
  for i in 0..5 {close(s.residual[i],r[N+i],2e-14,1e-7);ports=ports.max((s.residual[i]-r[N+i]).abs());}
 }
 println!("LM741_ORACLE,rows=60,spice=6,max_kcl_a={:0.17e},max_constraint_v={:0.17e},max_jac_kcl={:0.17e},max_jac_constraint={:0.17e},max_port_a={ports:0.17e}",max[0],max[1],max[2],max[3]);
}
#[test]
fn all_37_derivative_columns_fixed_history_and_candidate_purity() {
 for r in bank(include_str!("../../../evidence/voice_lm741_vectors09.txt")) {
  let (x,mode)=args(&r);let s=op::linearize(x,mode).unwrap();
  for j in 0..N {let h=if j<NV {1e-6} else {1e-9};let mut p=x;let mut m=x;p[j]+=h;m[j]-=h;
   let a=op::linearize(p,mode).unwrap();let b=op::linearize(m,mode).unwrap();
   for i in 0..N {close(s.jacobian[i][j],(a.residual[i]-b.residual[i])/(2.*h),if i<NV {2e-9} else {1e-6},2e-6);}
  }
  let again=op::linearize(x,mode).unwrap();assert_eq!(s.residual,again.residual);assert_eq!(s.jacobian,again.jacobian);assert_eq!(s.candidate,again.candidate);
 }
}
#[test]
fn equal_history_five_memories_and_domain_rejections() {
 for r in bank(include_str!("../../../evidence/voice_lm741_roots09.txt")) {
  let x:[f64;N]=r[..N].try_into().unwrap();let dc=op::linearize(x,Mode::Dc).unwrap();let previous=op::memory(&x);let e=op::linearize(x,Mode::Euler{dt_s:125e-9,previous}).unwrap();assert_eq!(dc.residual,e.residual);assert_eq!(previous,e.candidate);
  // Reactances retain their own branch rows and cannot be eliminated.
  close(e.jacobian[35][35],-0.5305/125e-9,0.,1e-15);close(e.jacobian[36][36],-100e-12/125e-9,0.,1e-15);
  for k in 0..5 {let mut h=previous;if k<3 {h.capacitor_v[k]+=0.01;} else {h.inductor_i_a[k-3]+=1e-8;}
   let changed=op::linearize(x,Mode::Euler{dt_s:125e-9,previous:h}).unwrap();assert_ne!(changed.residual,e.residual);assert_eq!(changed.jacobian,e.jacobian);assert_eq!(changed.candidate,e.candidate);
  }
  for dt_s in [0.,f64::NAN,124e-9,1.001e-3] {assert!(matches!(op::linearize(x,Mode::Euler{dt_s,previous}),Err(Error::InvalidInput)));}
  let mut bad=x;bad[0]=f64::INFINITY;assert!(matches!(op::linearize(bad,Mode::Dc),Err(Error::InvalidInput)));bad=x;bad[26]=1.01;assert!(matches!(op::linearize(bad,Mode::Dc),Err(Error::InvalidInput)));
  bad=x;bad[1]=x[6]+0.901;assert!(matches!(op::linearize(bad,Mode::Dc),Err(Error::JunctionDomain)));
  let mut h=previous;h.capacitor_v[0]=81.;assert!(matches!(op::linearize(x,Mode::Euler{dt_s:125e-9,previous:h}),Err(Error::InvalidInput)));
 }
}
