use rf_d_circuit::junction_charge::Parameters;
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
fn charge_companions_use_no_heap() {
 let p=Parameters{zero_bias_capacitance_f:7e-12,potential_v:0.75,grading:0.5,forward_fraction:0.4};
 let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
 for i in 0..10000 {let v=-1.+(i%200) as f64*0.02;sum+=std::hint::black_box(p.companion(v,v-0.001,125e-9).unwrap().current_a);}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());
 println!("JUNCTION_ALLOCATION,companions=10000,allocations={allocations}");
}
