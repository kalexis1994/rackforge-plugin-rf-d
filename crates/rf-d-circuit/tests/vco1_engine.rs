use rf_d_circuit::{vco1_engine::{Engine,State,Settings,Checkpoint,Error,Rejection,TICK_S},vco1_radau,vco1_stamp::{Controls,N,NV}};
use serde_json::Value;
use std::alloc::{GlobalAlloc,Layout,System};
use std::sync::atomic::{AtomicUsize,Ordering};
struct Count;
static ALLOCATIONS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Count {
    unsafe fn alloc(&self,l:Layout)->*mut u8 {ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.alloc(l)}}
    unsafe fn alloc_zeroed(&self,l:Layout)->*mut u8 {ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.alloc_zeroed(l)}}
    unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8 {ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.realloc(p,l,n)}}
    unsafe fn dealloc(&self,p:*mut u8,l:Layout) {unsafe {System.dealloc(p,l)}}
}
#[global_allocator] static ALLOCATOR:Count=Count;
fn vectors()->Value {serde_json::from_str(include_str!("../../../evidence/voice_vco1_portable_vectors01.json")).unwrap()}
fn array(v:&Value)->[f64;N] {std::array::from_fn(|k|v[k].as_f64().unwrap())}
fn old(v:&Value)->State {State {high:array(&v["previous_high"]),low:array(&v["previous_low"])}}
fn compare(pair:&vco1_radau::Pair, roots:&Value) {
    for (s,name) in [(&pair.stage,"stage"),(&pair.endpoint,"endpoint")] {
        assert!(s.residual_ratio<=1. && s.correction_ratio<=1.);
        for k in 0..N {
            let expected: f64=roots[name]["independent_decimal"][k].as_str().unwrap().parse().unwrap();
            let tol=if k<NV {2e-7} else {2e-10};
            assert!((s.candidate.high[k]+s.candidate.low[k]-expected).abs()<=tol,"{name}/{k}");
        }
    }
}
#[test]
fn admitted_intervals_and_recovered_newton_match_independent_roots() {
    let v=vectors();let c=Controls::default();let mut stages=0;
    for a in v["actual_intervals"].as_array().unwrap() {
        let h=a["dt_s"].as_f64().unwrap();let previous=old(a);
        let pair=vco1_radau::step(c,previous,h).unwrap();compare(&pair,&a["roots"]);stages+=2;
        let currents=vco1_radau::terminal_currents(&pair,previous,h).unwrap();
        for k in 0..3 {let expected:f64=a["independent_currents_a"][k].as_str().unwrap().parse().unwrap();assert!((currents[k]-expected).abs()<=2e-10);}
    }
    let d=&v["diagnostic"];let previous=old(d);
    for trio in d["independent"].as_array().unwrap() {
        let ticks=trio["full_ticks"].as_u64().unwrap();let h=ticks as f64*TICK_S;
        let full=vco1_radau::step(c,previous,h).unwrap();compare(&full,&trio["steps"]["full"]["roots"]);
        let mid=vco1_radau::step(c,previous,h/2.).unwrap();compare(&mid,&trio["steps"]["mid"]["roots"]);
        let end=vco1_radau::step(c,mid.endpoint.candidate,h/2.).unwrap();compare(&end,&trio["steps"]["end"]["roots"]);
        let difference=full.endpoint.candidate.difference(end.endpoint.candidate);
        let ratio=(0..N).fold(0_f64,|a,k|a.max(difference[k].abs()/if k<NV {2e-6} else {2e-9}));
        assert!(ratio<=1.);stages+=6;
    }
    println!("VCO1_PORTABLE_ROOTS,comparisons={stages},actual_currents=12,new_independent_solves=0");
}
#[test]
fn own_startup_checkpoint_continuity_and_zero_heap() {
    let before=ALLOCATIONS.load(Ordering::Relaxed);
    let mut engine=Engine::startup(Controls::default(),Settings::default()).unwrap();
    let initial=engine.checkpoint();
    let first=engine.advance_to(131072).unwrap();let saved=engine.checkpoint();
    let mut restored=Engine::restore(saved).unwrap();
    let next=engine.advance_to(131072).unwrap();let replay=restored.advance_to(131072).unwrap();
    let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;
    assert_eq!(allocations,0);assert_eq!(engine.checkpoint(),restored.checkpoint());
    assert_eq!(next.endpoints[0].pair.endpoint.candidate,replay.endpoints[0].pair.endpoint.candidate);
    assert_eq!(next.endpoints[1].current_a,replay.endpoints[1].current_a);
    assert_eq!(first.endpoints[0].elapsed_ticks,u64::from(first.half_ticks));
    assert_eq!(first.endpoints[1].elapsed_ticks,2*u64::from(first.half_ticks));
    assert_eq!(initial.elapsed_ticks,0);assert_eq!(initial.state.high[43],0.);
    assert!(first.error_ratio<=1. && first.attempts>1);
    println!("VCO1_PORTABLE_HEAP,startup_restore_accepted_allocations={allocations},first_attempts={}",first.attempts);
}
#[test]
fn budget_rejection_rolls_back_all_state_and_uses_no_heap() {
    let v=vectors();let d=&v["diagnostic"];
    let checkpoint=Checkpoint {state:old(d),controls:Controls::default(),settings:Settings {maximum_half_ticks:65536,attempt_limit:1},elapsed_ticks:d["elapsed_ticks"].as_u64().unwrap(),next_full_ticks:64};
    let mut engine=Engine::restore(checkpoint).unwrap();
    let before=ALLOCATIONS.load(Ordering::Relaxed);
    let temporal=engine.advance_to(checkpoint.elapsed_ticks+64);
    let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;
    assert!(matches!(temporal,Err(Error::AttemptLimit(Rejection::LocalError(e))) if e>1.));
    assert_eq!(engine.checkpoint(),checkpoint);assert_eq!(allocations,0);
    // Diagnosed extreme range CV rejects in Newton; this tests rollback, not electrical admission.
    let mut nonlinear=checkpoint;nonlinear.controls.cv_v[5]=40.;nonlinear.next_full_ticks=8;
    let mut engine=Engine::restore(nonlinear).unwrap();
    let before=ALLOCATIONS.load(Ordering::Relaxed);
    let result=engine.advance_to(nonlinear.elapsed_ticks+8);
    let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;
    assert!(matches!(result,Err(Error::PrecisionLimit(Rejection::Nonlinear(_)))));
    assert_eq!(engine.checkpoint(),nonlinear);assert_eq!(allocations,0);
    println!("VCO1_PORTABLE_ROLLBACK,temporal_and_nonlinear=true,allocations=0");
}
#[test]
fn integer_clock_limits_and_invalid_restores() {
    let v=vectors();let d=&v["diagnostic"];
    let base=Checkpoint {state:old(d),controls:Controls::default(),settings:Settings::default(),elapsed_ticks:u64::MAX-15,next_full_ticks:8};
    let mut engine=Engine::restore(base).unwrap();
    for bad_target in [0,base.elapsed_ticks,base.elapsed_ticks+1,u64::MAX] {
        assert!(matches!(engine.advance_to(bad_target),Err(Error::InvalidInput)));assert_eq!(engine.checkpoint(),base);
    }
    let accepted=engine.advance_to(u64::MAX-7).unwrap();
    assert_eq!(accepted.endpoints[0].elapsed_ticks,u64::MAX-11);assert_eq!(engine.checkpoint().elapsed_ticks,u64::MAX-7);
    assert!(matches!(engine.advance_to(u64::MAX-7),Err(Error::InvalidInput)));
    for bad in 0..6 {
        let mut q=base;
        match bad {0=>q.next_full_ticks=4,1=>q.next_full_ticks=12,2=>q.elapsed_ticks+=1,3=>q.state.low[43]=1.,4=>q.controls.mixer_v=f64::NAN,_=>q.settings.attempt_limit=0};
        assert!(matches!(Engine::restore(q),Err(Error::InvalidInput)));
    }
    assert!(base.elapsed_ticks>u64::from(u32::MAX));
    println!("VCO1_PORTABLE_CLOCK,u64_boundary=true,invalid_restore_cases=6");
}
