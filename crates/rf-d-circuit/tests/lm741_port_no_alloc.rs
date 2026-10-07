use rf_d_circuit::lm741::Mode;
use rf_d_circuit::lm741_port::{self as port,Budget};
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
fn full_solver_and_five_rhs_use_no_heap() {
 let p=[0.,0.001,12.,-12.,0.];let dc=port::dc(p).unwrap();let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;let mut previous=dc;
 for k in 0..1000 {let mut inputs=p;inputs[1]+=((k%20) as f64-10.)*1e-7;let next=port::solve(std::hint::black_box(inputs),Mode::Euler{dt_s:125e-9,previous:previous.candidate},previous.nodes,Budget::default()).unwrap();sum+=std::hint::black_box(next.current_a[4]+next.admittance[0][1]);previous=next;}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());println!("LM741_PORT_ALLOCATION,solves=1000,rhs=5,allocations={allocations}");
}
