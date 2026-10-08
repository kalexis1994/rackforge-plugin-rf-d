use rf_d_circuit::{joint_engine::{self as temporal,Engine,Settings,Checkpoint,Error},joint_voice as joint,chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,vco1_startup,vco1_stamp::Controls};
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
const TARGET:u64=1048576;
fn scene(mask:bool)->(joint::Parameters,joint::State) {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let p=Chain {circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([true;5],[0.5;4]).unwrap()};
 let controls=Controls::default();let v=vco1_startup::startup(controls).unwrap().nodes;
 let row:Vec<f64>=include_str!("../../../evidence/voice_chain_charge_vectors06.txt").lines().next().unwrap().split_whitespace().map(|x|x.parse().unwrap()).collect();
 let c=chain_charge::State::from_nodes(row[8..76].try_into().unwrap());
 (joint::Parameters::new(controls,p,[mask;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap(),joint::State::lift(v,[0.;134],c))
}
fn same(a:Checkpoint,b:Checkpoint) {
 assert_eq!(a.state,b.state);assert_eq!(a.elapsed_ticks,b.elapsed_ticks);assert_eq!(a.next_full_ticks,b.next_full_ticks);assert_eq!(a.settings,b.settings);
 assert_eq!(a.parameters.controls,b.parameters.controls);assert_eq!(a.parameters.sources,b.parameters.sources);assert_eq!(a.parameters.chain().mixer.admittance_s(),b.parameters.chain().mixer.admittance_s());
}
fn export(mask:bool,h:f64,old:joint::State,pair:&joint::Pair) {
 println!("JOINT_ROOT,{},{h:e},{:e},{:e}",usize::from(mask),pair.residual_ratio,pair.correction_ratio);
 for s in [old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]] {println!("JOINT_STATE,{}",s.high.into_iter().chain(s.low).map(|v|format!("{v:.17e}")).collect::<Vec<_>>().join(","));}
}
#[test]
fn trajectories_step_doubling_and_restore_replay() {
 let mut profiles=0;let mut total_pairs=0;let mut worst=0_f64;let mut worst_bus=0_f64;let mut worst_global=0_f64;
 for mask in [false,true] {let(p,old)=scene(mask);let mut finals=[old;2];
  for (profile,maximum_half_ticks) in [65536,32768].into_iter().enumerate() {
   let mut engine=Engine::from_conditioned(p,old,Settings{maximum_half_ticks,attempt_limit:20}).unwrap();let mut calls=0;let mut retried=0;
   while engine.checkpoint().elapsed_ticks<TARGET {
    assert!(calls<4096,"trajectory budget");let before=engine.checkpoint();let accepted=engine.advance_to(TARGET).unwrap();calls+=1;retried+=accepted.attempts-1;
    let mid=accepted.endpoints[0].pair.candidates[1];let end=accepted.endpoints[1].pair.candidates[1];
    assert_eq!(accepted.error_ratio,temporal::error_ratio(accepted.coarse.candidates[1],end));assert!(accepted.error_ratio<=1.);worst=worst.max(accepted.error_ratio);
    assert_eq!(accepted.endpoints[0].elapsed_ticks,before.elapsed_ticks+u64::from(accepted.half_ticks));assert_eq!(accepted.endpoints[1].elapsed_ticks,before.elapsed_ticks+2*u64::from(accepted.half_ticks));assert!(engine.checkpoint().elapsed_ticks<=TARGET);assert_eq!(engine.checkpoint().state,end);
    for e in &accepted.endpoints {assert!(e.pair.residual_ratio<=1.&&e.pair.correction_ratio<=1.);worst_bus=worst_bus.max(e.observations.bus_kcl_a.abs());assert!(e.observations.bus_kcl_a.abs()<=1e-12);}
    if profile==0&&(calls==1||engine.checkpoint().elapsed_ticks==TARGET) {
     let h=f64::from(accepted.half_ticks)*temporal::TICK_S;export(mask,2.*h,before.state,&accepted.coarse);export(mask,h,before.state,&accepted.endpoints[0].pair);export(mask,h,mid,&accepted.endpoints[1].pair);
    }
    if calls==3 {
     let q=engine.checkpoint();let mut restored=Engine::restore(q).unwrap();let a=engine.advance_to(TARGET).unwrap();let b=restored.advance_to(TARGET).unwrap();same(engine.checkpoint(),restored.checkpoint());assert_eq!(a.error_ratio,b.error_ratio);assert_eq!(a.attempts,b.attempts);
     for i in 0..2 {assert_eq!(a.endpoints[i].pair.increments,b.endpoints[i].pair.increments);assert_eq!(a.endpoints[i].pair.candidates,b.endpoints[i].pair.candidates);assert_eq!(a.endpoints[i].observations,b.endpoints[i].observations);}calls+=1;
    }
   }
   finals[profile]=engine.checkpoint().state;assert_eq!(engine.checkpoint().elapsed_ticks,TARGET);total_pairs+=calls;profiles+=1;
   println!("ENGINE_PROFILE,mask={},half_max={maximum_half_ticks},pairs={calls},retries={retried},ticks={TARGET}",usize::from(mask));
  }
  let global=temporal::error_ratio(finals[0],finals[1]);worst_global=worst_global.max(global);assert!(global<=1.,"same-clock refinement {global:e}");
 }
 println!("ENGINE_TRAJECTORY,profiles={profiles},accepted_pairs={total_pairs},max_lte={worst:e},max_bus_a={worst_bus:e},max_global_ratio={worst_global:e},restore_replays=4,target_ticks={TARGET}");
}
#[test]
fn rejection_and_checkpoint_domains_are_atomic() {
 let(p,old)=scene(false);let mut engine=Engine::from_conditioned(p,old,Settings::default()).unwrap();let q=engine.checkpoint();
 for target in [0,7] {assert_eq!(engine.advance_to(target).err(),Some(Error::InvalidInput));same(q,engine.checkpoint());}
 for variant in 0..6 {let mut broken=q;match variant {0=>broken.state.low[46]=1.,1=>broken.state.high[43]=f64::NAN,2=>broken.elapsed_ticks=1,3=>broken.next_full_ticks=7,4=>broken.settings.attempt_limit=0,_=>broken.parameters.sources[1]=f64::INFINITY};assert!(Engine::restore(broken).is_err());}
 // A one-attempt budget must preserve the complete previous checkpoint on error.
 let mut stressed=p;stressed.controls.external_neg4_load_a=1.;let mut limited=Engine::from_conditioned(stressed,old,Settings{maximum_half_ticks:131072,attempt_limit:1}).unwrap();let before=limited.checkpoint();
 let rejected=limited.advance_to(TARGET);assert!(rejected.is_err());same(before,limited.checkpoint());println!("ENGINE_REJECT,error={:?},invalid_targets=2,invalid_checkpoints=6,budget_rollback=1",rejected.err().unwrap());
}
#[test]
fn accepted_and_invalid_target_paths_allocate_no_heap() {
 let(p,old)=scene(false);let mut engine=Engine::from_conditioned(p,old,Settings{maximum_half_ticks:4,attempt_limit:20}).unwrap();
 ALLOCATIONS.store(0,Ordering::SeqCst);let accepted=engine.advance_to(8);let a=ALLOCATIONS.load(Ordering::SeqCst);assert!(accepted.is_ok());assert_eq!(a,0);
 let before=engine.checkpoint();ALLOCATIONS.store(0,Ordering::SeqCst);let rejected=engine.advance_to(8);let b=ALLOCATIONS.load(Ordering::SeqCst);assert_eq!(rejected.err(),Some(Error::InvalidInput));assert_eq!(b,0);same(before,engine.checkpoint());
 println!("ENGINE_HEAP,accepted_allocations={a},invalid_target_allocations={b}");
}
