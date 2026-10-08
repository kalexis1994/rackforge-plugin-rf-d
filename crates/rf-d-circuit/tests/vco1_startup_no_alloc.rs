use rf_d_circuit::vco1_startup::startup;
use rf_d_circuit::vco1_newton::{solve,Boundary,Budget};
use rf_d_circuit::vco1_stamp::{Controls,Memory,Mode,N};
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
fn own_startup_and_steps_use_no_heap() {
 let c=Controls::default();let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;let mut x=[0.;N];
 for _ in 0..16 {let p=startup(std::hint::black_box(c)).unwrap();sum+=p.nodes[7];x=p.nodes;}
 for _ in 0..128 {let p=solve(c,Mode::Euler{dt_s:125e-9,previous:Memory{state:x}},Boundary::Free,x,Budget::default()).unwrap();sum+=p.nodes[43];x=p.nodes;}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());println!("VCO1_STARTUP_ALLOCATION,startups=16,steps=128,allocations={allocations}");
}
