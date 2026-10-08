use rf_d_circuit::vco1_stamp::{linearize,Controls,Memory,Mode,N};
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
fn full_vco1_stamps_use_no_heap() {
 let mut it=include_str!("../../../evidence/voice_vco1_stamp_startup08.txt").lines().next().unwrap().split_whitespace().map(|s|s.parse::<f64>().unwrap());
 let _:Vec<f64>=it.by_ref().take(11).collect();let x:[f64;N]=std::array::from_fn(|_|it.next().unwrap());let previous=Memory{state:x};
 let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
 for _ in 0..1000 {let s=linearize(std::hint::black_box(x),Controls::default(),Mode::Euler{dt_s:125e-9,previous}).unwrap();sum+=std::hint::black_box(s.residual[0]+s.jacobian[35][35]);}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());println!("VCO1_ALLOCATION,stamps=1000,allocations={allocations}");
}
