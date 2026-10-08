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
fn coupled_vco1_solves_use_no_heap() {
 let mut it=include_str!("../../../evidence/voice_vco1_newton_startup01.txt").lines().next().unwrap().split_whitespace().map(|s|s.parse::<f64>().unwrap());let _:Vec<f64>=it.by_ref().take(11+N).collect();let mut x:[f64;N]=std::array::from_fn(|_|it.next().unwrap());let c=Controls::default();
 let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
 for _ in 0..128 {let p=solve(c,Mode::Euler{dt_s:125e-9,previous:Memory{state:x}},Boundary::Free,std::hint::black_box(x),Budget::default()).unwrap();sum+=std::hint::black_box(p.nodes[43]);x=p.nodes;}
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());println!("VCO1_NEWTON_ALLOCATION,solves=128,allocations={allocations}");
}
