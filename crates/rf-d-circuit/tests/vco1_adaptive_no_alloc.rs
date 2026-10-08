use rf_d_circuit::vco1_startup::startup;
use rf_d_circuit::vco1_stamp::{Controls,Memory};
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
fn adaptive_candidates_use_no_heap() {
 let c=Controls::default();let mut old=Memory{state:startup(c).unwrap().nodes};let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;let mut proposed=32768;let mut remaining=983040000;
 for _ in 0..128 {let p=rf_d_circuit::vco1_adaptive::advance(c,old,proposed,16384,remaining).unwrap();sum+=p.endpoint.nodes[43];remaining-=2*p.half_ticks;proposed=p.next_full_ticks;old=p.endpoint.candidate;}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());println!("VCO1_ADAPTIVE_ALLOCATION,candidates=128,allocations={allocations}");
}
