use rf_d_circuit::vco1_startup::startup;
use rf_d_circuit::vco1_stamp::Controls;
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
#[global_allocator]
static ALLOCATOR:Count=Count;
#[test]
fn complete_increment_memory_and_recovery_use_no_heap() {
 let c=Controls::default();let mut old=rf_d_circuit::vco1_increment::State::from_nodes(startup(c).unwrap().nodes);
 let v:Vec<f64>=include_str!("../../../evidence/voice_vco1_adaptive_failure_history01.txt").split_whitespace().map(|s|s.parse().unwrap()).collect();let floor=rf_d_circuit::vco1_increment::State::from_nodes(v.try_into().unwrap());
 let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
 for _ in 0..16 {let p=rf_d_circuit::vco1_increment::solve(c,floor,rf_d_circuit::vco1_increment::MIN_DT_S,rf_d_circuit::vco1_newton::Budget::default()).unwrap();sum+=p.candidate.low[15];}
 for _ in 0..128 {let p=rf_d_circuit::vco1_increment::solve(c,old,62.5e-9,rf_d_circuit::vco1_newton::Budget::default()).unwrap();sum+=p.candidate.high[43];old=p.candidate;}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());println!("VCO1_INCREMENT_ALLOCATION,recoveries=16,steps=128,allocations={allocations}");
}
