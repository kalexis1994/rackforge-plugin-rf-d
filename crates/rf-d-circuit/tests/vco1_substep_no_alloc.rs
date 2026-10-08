use rf_d_circuit::vco1_startup::startup;
use rf_d_circuit::vco1_newton::{Boundary,Budget};
use rf_d_circuit::vco1_stamp::{Controls,Memory,Mode};
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
fn short_stamps_and_continuation_use_no_heap() {
 let c=Controls::default();let mut x=startup(c).unwrap().nodes;let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
 for _ in 0..100 {let s=rf_d_circuit::vco1_substep::linearize(x,c,Mode::Euler{dt_s:rf_d_circuit::vco1_substep::MIN_DT_S,previous:Memory{state:x}}).unwrap();sum+=s.residual[43];}
 for _ in 0..128 {let p=rf_d_circuit::vco1_substep::solve(c,Mode::Euler{dt_s:62.5e-9,previous:Memory{state:x}},Boundary::Free,x,Budget::default()).unwrap();sum+=p.nodes[43];x=p.nodes;}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());println!("VCO1_SUBSTEP_ALLOCATION,stamps=100,steps=128,allocations={allocations}");
}
