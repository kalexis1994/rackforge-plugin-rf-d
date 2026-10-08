use rf_d_circuit::vco1_stamp::{linearize,Controls,C4,Memory,Mode,Error,N,NV,NAMES};
fn rows()->Vec<Vec<f64>> {include_str!("../../../evidence/voice_vco1_stamp_vectors08.txt").lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn controls(v:&[f64])->Controls {Controls{r8_fraction:v[0],r11_ohm:v[1],c4:if v[2]==1e-11 {C4::Schematic10Pf} else {assert_eq!(v[2],1e-10);C4::Bom100Pf},mixer_v:v[3],external_neg4_load_a:v[4],cv_v:v[5..11].try_into().unwrap()}}
fn mode(v:&[f64])->Mode {if v[11+2*N]==0. {Mode::Dc} else {Mode::Euler{dt_s:v[11+2*N],previous:Memory{state:v[11+N..11+2*N].try_into().unwrap()}}}}
fn close(a:f64,b:f64,abs:f64,rel:f64,label:&str) {assert!(a.is_finite()&&b.is_finite()&&(a-b).abs()<=abs+rel*b.abs(),"{label}: {a:e} vs {b:e}");}
#[test]
fn full_graph_matches_independent_incidence_and_startup() {
 let pattern:Vec<(usize,usize)>=include_str!("../../../evidence/voice_vco1_stamp_pattern08.txt").lines().map(|l|{let v:Vec<usize>=l.split_whitespace().map(|s|s.parse().unwrap()).collect();(v[0],v[1])}).collect();
 let mut max_r:f64=0.;let mut max_j:f64=0.;let mut max_balance:f64=0.;let bank=rows();assert_eq!(bank.len(),40);
 for v in &bank {
  let x=v[11..11+N].try_into().unwrap();let s=linearize(x,controls(v),mode(v)).unwrap();let k=12+2*N;assert_eq!(v.len(),k+N+1+pattern.len());
  assert_eq!(s.candidate,Memory{state:x});let mut expected=[[0.;N];N];
  for (i,&(r,c)) in pattern.iter().enumerate() {expected[r][c]=v[k+N+1+i];}
  for r in 0..N {close(s.residual[r],v[k+r],if r<NV {2e-11} else {2e-10},3e-11,&format!("R{}",NAMES[r]));max_r=max_r.max((s.residual[r]-v[k+r]).abs());
   for c in 0..N {close(s.jacobian[r][c],expected[r][c],2e-10,3e-11,"J");max_j=max_j.max((s.jacobian[r][c]-expected[r][c]).abs());}}
  close(s.ground_current_a,v[k+N],2e-11,3e-11,"ground");let balance=s.residual[..NV].iter().sum::<f64>()+s.ground_current_a;max_balance=max_balance.max(balance.abs());assert!(balance.abs()<1e-11);
 }
 for line in include_str!("../../../evidence/voice_vco1_stamp_startup08.txt").lines() {
  let v:Vec<f64>=line.split_whitespace().map(|s|s.parse().unwrap()).collect();assert_eq!(v.len(),12+N);let x=v[11..11+N].try_into().unwrap();let mut s=linearize(x,controls(&v),Mode::Dc).unwrap();let ramp=NAMES.iter().position(|n|*n=="RAMP_C1").unwrap();assert_eq!(x[ramp],0.);s.residual[ramp]+=v[11+N];s.ground_current_a-=v[11+N];
  for r in s.residual {assert!(r.abs()<1e-11,"startup residual {r:e}");}assert!((s.residual[..NV].iter().sum::<f64>()+s.ground_current_a).abs()<1e-11);
 }
 println!("VCO1_STAMP,rows=40,unknowns=134,all_jac_entries=718240,max_residual={max_r:.17e},max_jacobian={max_j:.17e},max_balance_a={max_balance:.17e}");
}
#[test]
fn all_columns_fd_fixed_history_and_controls() {
 let bank=rows();let mut columns=0;
 for v in &bank {
  let x:[f64;N]=v[11..11+N].try_into().unwrap();let c=controls(v);let m=mode(v);let s=linearize(x,c,m).unwrap();let repeat=linearize(x,c,m).unwrap();assert_eq!(s.residual,repeat.residual);assert_eq!(s.jacobian,repeat.jacobian);assert_eq!(s.candidate,repeat.candidate);
  for col in 0..N {let h=if col<NV {1e-7} else {1e-10};let mut hi=x;let mut lo=x;hi[col]+=h;lo[col]-=h;let a=linearize(hi,c,m).unwrap();let b=linearize(lo,c,m).unwrap();
   for row in 0..N {close((a.residual[row]-b.residual[row])/(2.*h),s.jacobian[row][col],2e-6,2e-5,&format!("FD {row}/{col}"));}columns+=1;}
  // Each independent board CV changes exactly its own source constraint.
  for cv in 0..6 {let mut changed=c;changed.cv_v[cv]+=0.01;let t=linearize(x,changed,m).unwrap();
   for row in 0..N {close(t.residual[row]-s.residual[row],if row==NV+3+cv {-0.01} else {0.},1e-13,1e-12,"CV incidence");}}
 }
 println!("VCO1_FD,columns={columns},history=fixed");
}
#[test]
fn input_failures_do_not_publish_memory() {
 let v=&rows()[0];let x:[f64;N]=v[11..11+N].try_into().unwrap();let c=controls(v);let previous=Memory{state:x};
 for dt in [f64::NAN,f64::INFINITY,0.,124e-9,1.001e-3] {assert_eq!(linearize(x,c,Mode::Euler{dt_s:dt,previous}).unwrap_err(),Error::InvalidInput);}
 for k in 0..N {for bad in [f64::NAN,f64::INFINITY,if k<NV {40.01} else {1.01}] {let mut y=x;y[k]=bad;assert_eq!(linearize(y,c,Mode::Dc).unwrap_err(),Error::InvalidInput);assert_eq!(linearize(x,c,Mode::Euler{dt_s:125e-9,previous:Memory{state:y}}).unwrap_err(),Error::InvalidInput);}}
 for cv in 0..6 {let mut bad=c;bad.cv_v[cv]=f64::NAN;assert_eq!(linearize(x,bad,Mode::Dc).unwrap_err(),Error::InvalidInput);}
 for k in 0..4 {let mut bad=c;match k {0=>bad.r8_fraction=1.1,1=>bad.r11_ohm=-1.,2=>bad.mixer_v=41.,_=>bad.external_neg4_load_a=1.1};assert_eq!(linearize(x,bad,Mode::Dc).unwrap_err(),Error::InvalidInput);}
 let mut bad=x;let qb=NAMES.iter().position(|n|*n=="QA_BASE").unwrap();let emitter=NAMES.iter().position(|n|*n=="PAIR_EMITTER").unwrap();bad[qb]=bad[emitter]+1.;assert!(matches!(linearize(bad,c,Mode::Dc),Err(Error::Bjt(_))));
 assert_eq!(previous.state,x);assert!(linearize(x,c,Mode::Euler{dt_s:125e-9,previous}).is_ok());
}
