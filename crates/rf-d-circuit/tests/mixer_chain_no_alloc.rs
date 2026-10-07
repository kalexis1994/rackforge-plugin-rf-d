use rf_d_circuit::{mixer_chain66 as joint,mixer_on::OnMixer,SolverBudget};
#[allow(dead_code)]
#[path="support/mixer_chain_lab.rs"]
mod lab;
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
fn complete_loaded_chain_steps_use_no_heap() {
    let(p,c,h)=lab::lab_parameters();let b=lab::controlled_boundary(0,true);
    let m=OnMixer::new([true;5],[0.5;4]).unwrap();
    let mut state=joint::initial_state(m,[0.;5],p,c,h,b,lab::SEED).unwrap();
    let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
    for step in 0..32 {
        let source=[0.01*(step as f64*0.2).sin(),0.,0.,0.,0.];
        let r=joint::step(&mut state,m,source,p,c,h,b,SolverBudget::default()).unwrap();
        sum+=std::hint::black_box(r.chain.output.j7_v+r.mixer.current_a[5]);
    }
    let count=ALLOCATIONS.load(Ordering::Relaxed)-before;
    assert_eq!(count,0);assert!(sum.is_finite());
    println!("CHAIN_ALLOCATION,steps=32,allocations={count}");
}
