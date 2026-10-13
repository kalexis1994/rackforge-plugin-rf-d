use rf_d_circuit::{conditioned_voice as voice,conditioned_engine as temporal,chain_charge::Parameters as Chain,mixer_on::OnMixer,vco1_stamp::Controls};
use std::alloc::{GlobalAlloc,Layout,System};
use std::sync::atomic::{AtomicUsize,Ordering};
#[allow(dead_code)] #[path="support/mixer_chain_lab.rs"] mod lab;
#[path="support/conditioned_seed.rs"] mod fixture;
struct Count;static ALLOCATIONS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Count{
 unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe{System.alloc(l)}}
 unsafe fn alloc_zeroed(&self,l:Layout)->*mut u8{ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe{System.alloc_zeroed(l)}}
 unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe{System.realloc(p,l,n)}}
 unsafe fn dealloc(&self,p:*mut u8,l:Layout){unsafe{System.dealloc(p,l)}}
}
#[global_allocator]static ALLOCATOR:Count=Count;
fn checkpoint(bits:[u64;458],m:(u64,u32,u32,u32,f64,bool,bool))->temporal::Checkpoint{
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;let mut chain=Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};chain.boundary.panel.cutoff_fraction_from_neg10=1.;let mut p=voice::Parameters::new(Controls::default(),chain,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap();p.keyboard=m.4;p.final_decay=m.5;p.short=m.6;
 temporal::Checkpoint{state:voice::State{high:std::array::from_fn(|k|f64::from_bits(bits[k])),low:std::array::from_fn(|k|f64::from_bits(bits[k+229]))},parameters:p,settings:temporal::Settings{maximum_half_ticks:m.1,attempt_limit:m.2},elapsed_ticks:m.0,next_full_ticks:m.3}
}
fn same_state(a:voice::State,b:voice::State){assert_eq!(a.high.map(f64::to_bits),b.high.map(f64::to_bits));assert_eq!(a.low.map(f64::to_bits),b.low.map(f64::to_bits));}
fn same_checkpoint(a:temporal::Checkpoint,b:temporal::Checkpoint){same_state(a.state,b.state);assert_eq!(a.elapsed_ticks,b.elapsed_ticks);assert_eq!(a.next_full_ticks,b.next_full_ticks);assert_eq!(a.settings,b.settings);assert_eq!(a.parameters.keyboard.to_bits(),b.parameters.keyboard.to_bits());assert_eq!(a.parameters.short,b.parameters.short);assert_eq!(a.parameters.final_decay,b.parameters.final_decay);assert_eq!(a.parameters.controls,b.parameters.controls);assert_eq!(a.parameters.sources.map(f64::to_bits),b.parameters.sources.map(f64::to_bits));}
fn same_pair(a:&voice::Pair,b:&voice::Pair){assert_eq!(a.residual_ratio.to_bits(),b.residual_ratio.to_bits());assert_eq!(a.correction_ratio.to_bits(),b.correction_ratio.to_bits());assert_eq!(a.iterations,b.iterations);assert_eq!(a.trials,b.trials);for(x,y)in a.increments.iter().chain(&a.candidates).zip(b.increments.iter().chain(&b.candidates)){same_state(*x,*y);}}
fn measured<T>(f:impl FnOnce()->T)->T{ALLOCATIONS.store(0,Ordering::SeqCst);let q=f();let allocations=ALLOCATIONS.load(Ordering::SeqCst);assert_eq!(allocations,0,"processing allocated");q}

#[test]
fn memory_contract(){
 let stamp=std::mem::size_of::<voice::Stamp>();let workspace=voice::Workspace::storage_bytes();let engine=std::mem::size_of::<temporal::Engine>();let checkpoint=std::mem::size_of::<temporal::Checkpoint>();
 assert_eq!(workspace,2*stamp);assert!(stamp<=2*1024*1024&&workspace<=4*1024*1024&&engine<=16*1024&&checkpoint<=16*1024);println!("PORTABLE_MEMORY,stamp={stamp},workspace={workspace},engine={engine},checkpoint={checkpoint}");
}
#[test]
fn reusable_workspace_survives_other_history_and_rejection_without_heap(){
 let a=checkpoint(fixture::A_STATE,fixture::A_METADATA);let b=checkpoint(fixture::D_STATE,fixture::D_METADATA);let mut workspace=voice::Workspace::new();let h=2e-6;
 let expected=measured(||workspace.step(a.parameters,a.state,h)).unwrap();measured(||workspace.step(b.parameters,b.state,h)).unwrap();let repeated=measured(||workspace.step(a.parameters,a.state,h)).unwrap();same_pair(&expected,&repeated);
 let mut invalid=a.parameters;invalid.keyboard=11.;assert!(measured(||workspace.step(invalid,a.state,h)).is_err());let recovered=measured(||workspace.step(a.parameters,a.state,h)).unwrap();same_pair(&expected,&recovered);println!("PORTABLE_HEAP,workspace_successes=4,workspace_rejections=1,allocations=0");
}
#[test]
fn temporal_acceptance_budget_rollback_and_recovery_without_heap(){
 let a=checkpoint(fixture::A_STATE,fixture::A_METADATA);let mut workspace=voice::Workspace::new();let mut engine=temporal::Engine::restore(a).unwrap();let accepted=measured(||engine.advance_to(&mut workspace,a.elapsed_ticks+2097152)).unwrap();assert!(accepted.error_ratio<=1.);let before=engine.checkpoint();assert_eq!(measured(||engine.advance_to(&mut workspace,before.elapsed_ticks)).err(),Some(temporal::Error::InvalidInput));same_checkpoint(before,engine.checkpoint());
 let mut stress=checkpoint(fixture::TRIGGER_STATE,fixture::TRIGGER_METADATA);stress.settings.attempt_limit=1;let mut limited=temporal::Engine::restore(stress).unwrap();let target=stress.elapsed_ticks+157286400;assert!(measured(||limited.advance_to(&mut workspace,target)).is_err());same_checkpoint(stress,limited.checkpoint());
 let mut recovered=limited.checkpoint();recovered.settings.attempt_limit=20;let mut engine=temporal::Engine::restore(recovered).unwrap();let result=measured(||engine.advance_to(&mut workspace,target)).unwrap();assert!(result.error_ratio<=1.);println!("PORTABLE_HEAP,temporal_successes=2,temporal_rejections=2,allocations=0");
}
#[test]
fn two_temporal_engines_share_scratch_serially_and_match_fresh_history(){
 let a=checkpoint(fixture::A_STATE,fixture::A_METADATA);let b=checkpoint(fixture::D_STATE,fixture::D_METADATA);let mut workspace=voice::Workspace::new();let mut left=temporal::Engine::restore(a).unwrap();let mut right=temporal::Engine::restore(b).unwrap();let mut restored=temporal::Engine::restore(a).unwrap();
 let first=measured(||left.advance_to(&mut workspace,a.elapsed_ticks+2097152)).unwrap();measured(||right.advance_to(&mut workspace,b.elapsed_ticks+2097152)).unwrap();let replay=measured(||restored.advance_to(&mut workspace,a.elapsed_ticks+2097152)).unwrap();same_checkpoint(left.checkpoint(),restored.checkpoint());same_pair(&first.coarse,&replay.coarse);for i in 0..2{same_pair(&first.endpoints[i].pair,&replay.endpoints[i].pair);assert_eq!(first.endpoints[i].observations,replay.endpoints[i].observations);assert_eq!(first.endpoints[i].elapsed_ticks,replay.endpoints[i].elapsed_ticks);}println!("PORTABLE_SHARED_SCRATCH,successes=3,restore_matches=1,allocations=0");
}
