use rf_d_circuit::{chain_charge::{self,Parameters,State,N},chain_radau,mixer_on::OnMixer,circuit66,mixer_chain66_direct};
use std::alloc::{GlobalAlloc,Layout,System};
use std::sync::atomic::{AtomicUsize,Ordering};
#[allow(dead_code)] #[path="support/mixer_chain_lab.rs"] mod lab;
struct Count;static ALLOCATIONS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Count {
 unsafe fn alloc(&self,l:Layout)->*mut u8 {ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.alloc(l)}}
 unsafe fn alloc_zeroed(&self,l:Layout)->*mut u8 {ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.alloc_zeroed(l)}}
 unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8 {ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.realloc(p,l,n)}}
 unsafe fn dealloc(&self,p:*mut u8,l:Layout) {unsafe {System.dealloc(p,l)}}
}
#[global_allocator] static ALLOCATOR:Count=Count;
fn rows()->Vec<Vec<f64>> {include_str!("../../../evidence/voice_chain_charge_vectors06.txt").lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn parameters(r61:f64,mask:usize)->Parameters {
 let(mut p,c,h)=lab::lab_parameters();p.r61_ohm=r61;
 Parameters {circuit:p,conversion:c,headphone:h,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new(std::array::from_fn(|i|mask&(1<<i)!=0),[0.5;4]).unwrap()}
}
fn near(a:f64,b:f64,t:f64) {assert!(a.is_finite()&&b.is_finite()&&(a-b).abs()<=t,"{a:e} vs {b:e}; tol={t:e}");}
#[test]
fn all_radau_stages_and_loaded_currents_match_independent_roots() {
 let rows=rows();assert_eq!(rows.len(),12);let mut max_v=0_f64;let mut max_i=0_f64;let mut max_lte=0_f64;
 for r in &rows {
  assert_eq!(r.len(),500);let p=parameters(r[0],r[1] as usize);let sources=r[3..8].try_into().unwrap();let old=State::from_nodes(r[8..76].try_into().unwrap());
  let full=chain_radau::step(p,sources,old,r[2]).unwrap();let mid=chain_radau::step(p,sources,old,r[2]/2.).unwrap();let end=chain_radau::step(p,sources,mid.endpoint.candidate,r[2]/2.).unwrap();
  for (part,pair) in [&full,&mid,&end].into_iter().enumerate() {
   let base=76+part*141;
   for (offset,s) in [(0,&pair.stage),(N,&pair.endpoint)] {
    assert!(s.residual_ratio<=1.&&s.correction_ratio<=1.);
    for k in 0..N {let actual=s.candidate.high[k]+s.candidate.low[k];max_v=max_v.max((actual-r[base+offset+k]).abs());near(actual,r[base+offset+k],1e-6);}
   }
   let current=chain_charge::source_currents(p,sources,pair.endpoint.candidate).unwrap();
   for k in 0..5 {max_i=max_i.max((current[k]-r[base+2*N+k]).abs());near(current[k],r[base+2*N+k],1e-9);}
  }
  let error=full.endpoint.candidate.difference(end.endpoint.candidate).iter().fold(0_f64,|a,v|a.max(v.abs()/2e-6));max_lte=max_lte.max(error);assert!(error<=1.);
 }
 println!("CHAIN_CHARGE_ROOTS,scenes=12,stages=72,currents=180,max_v={max_v:e},max_i={max_i:e},max_lte={max_lte:e}");
}
#[test]
fn full_jacobian_and_contact_charge_rows_are_consistent() {
 let rows=rows();let mut worst=0_f64;
 for r in &rows {
  let p=parameters(r[0],r[1] as usize);let sources=r[3..8].try_into().unwrap();let old=State::from_nodes(r[8..76].try_into().unwrap());
  let pair=chain_radau::step(p,sources,old,r[2]).unwrap();let delta=[pair.stage.delta,pair.endpoint.delta];let stamp=chain_radau::linearize(p,sources,old,delta,r[2]).unwrap();
  for col in 0..2*N {
   let mut plus=delta;let mut minus=delta;plus[col/N][col%N]+=1e-7;minus[col/N][col%N]-=1e-7;
   let a=chain_radau::linearize(p,sources,old,plus,r[2]).unwrap();let b=chain_radau::linearize(p,sources,old,minus,r[2]).unwrap();
   for row in 0..2*N {let fd=(a.residual[row]-b.residual[row])/2e-7;let tol=1e-8+2e-5*fd.abs();let error=(stamp.jacobian[row][col]-fd).abs();worst=worst.max(error/tol);near(stamp.jacobian[row][col],fd,tol);}
  }
 }
 let r=&rows[0];let old=State::from_nodes(r[8..76].try_into().unwrap());let sources=r[3..8].try_into().unwrap();
 for lower in [0.,5000.] {for mode in 0..4 {
  let mut p=parameters(r[0],1);p.boundary.recovery.vca.second.output.output.r21_lower_ohm=lower;
  if mode==0 {p.boundary.r14_ohm=None;} else if mode==1 {p.boundary.r14_ohm=Some(0.);p.circuit.r30_ohm=1330.;}
  if mode==3 {p.boundary.r14_ohm=Some(1e-20);p.circuit.r30_ohm=1330.;}
  let stamp=chain_charge::linearize(p,sources,old,[0.;N],r[2]).unwrap();
  assert!(stamp.mass_over_h[49].iter().all(|v|*v==0.));assert_eq!(stamp.dc_jacobian[49][49],1.);
  if mode<2 {assert!(stamp.mass_over_h[67].iter().all(|v|*v==0.));assert!(chain_charge::constraint_row(p,67));}
  if mode==3 {assert!(!chain_charge::constraint_row(p,67));assert!(stamp.mass_over_h[67][67]>0.);assert!(stamp.dc_jacobian[67][67]>1e19);}
 }}
 println!("CHAIN_CHARGE_JACOBIAN,columns=1632,entries=221952,max_gate_ratio={worst:e},contact_cases=8");
}
#[test]
fn explicit_euler_stamp_matches_previous_reduced_chain_at_125ns() {
 let rows:Vec<Vec<f64>>=include_str!("../../../evidence/voice_mixer_direct_vectors01.txt").lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect();let mut comparisons=0;let mut worst=0_f64;
 for case in rows.chunks(16).filter(|case|case[0][6]==125e-9) {
  let r=&case[3];let p=parameters(r[0],r[1] as usize);let sources=r[7..12].try_into().unwrap();
  let prior=circuit66::State {node_v:r[12..78].try_into().unwrap(),previous_node_v:r[12..78].try_into().unwrap(),capacitor_v:r[78..95].try_into().unwrap(),c10_capacitor_v:r[95]};
  let high=std::array::from_fn(|k|if k<66 {prior.node_v[k]} else if k==66 {prior.node_v[6]-prior.capacitor_v[5]} else {prior.node_v[7]+prior.c10_capacitor_v});let old=State::from_nodes(high);
  let candidate=State::from_nodes(std::array::from_fn(|k|if k<66 {r[96+k]} else if k==66 {r[162]} else {r[96+7]+r[180]}));
  let delta=candidate.difference(old);let parts=chain_charge::linearize(p,sources,old,delta,125e-9).unwrap();
  let mut b=p.boundary;b.recovery.vca.second.output.output.dt_s=125e-9;
  let x=r[96..162].try_into().unwrap();let (expected,_,_)=mixer_chain66_direct::linearize(&prior,p.mixer,sources,p.circuit,p.conversion,p.headphone,b,&x).unwrap();
  for k in 0..66 {let actual=parts.dc[k]+parts.charge_over_h[k];worst=worst.max((actual-expected[k]).abs());near(actual,expected[k],2e-10);comparisons+=1;}
  near(parts.dc[66]+parts.charge_over_h[66],0.,2e-10);near(parts.dc[67]+parts.charge_over_h[67],0.,2e-10);
 }
 println!("CHAIN_CHARGE_EULER,physical_rows={comparisons},max_error_a={worst:e}");
}
#[test]
fn accepted_and_rejected_charge_operations_use_no_heap() {
 let rows=rows();let r=&rows[2];let old=State::from_nodes(r[8..76].try_into().unwrap());let p=parameters(r[0],r[1] as usize);let sources=r[3..8].try_into().unwrap();
 let before=ALLOCATIONS.load(Ordering::Relaxed);
 let full=chain_radau::step(p,sources,old,r[2]);let bad=chain_radau::step(p,sources,old,chain_charge::MIN_DT_S/2.);
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;
 assert!(full.is_ok()&&bad.is_err());assert_eq!(allocations,0);
 println!("CHAIN_CHARGE_HEAP,accepted_and_rejected_allocations={allocations}");
}
