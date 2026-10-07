use rf_d_circuit::{mixer_chain_port_direct::solve_input_port,mixer_on::OnMixer,SolverBudget};
#[allow(dead_code)]
#[path="support/mixer_chain_lab.rs"]mod lab;
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
#[global_allocator]static ALLOCATOR:Count=Count;
#[test]
fn loaded_source_currents_and_all_tangents_use_no_heap() {
    let(p,c,h)=lab::lab_parameters();
    for interval in [0.5e-6,0.25e-6,0.125e-6] {let mut b=lab::controlled_boundary(0,true);b.recovery.vca.second.output.output.dt_s=interval;
    let m=OnMixer::new([true;5],[0.5;4]).unwrap();
    let old=rf_d_circuit::mixer_chain66_direct::initial_state(m,[0.;5],p,c,h,b,lab::SEED).unwrap();
    let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
    for step in 0..16 {
        let source=[0.01*(step as f64*0.2).sin(),0.,0.,0.,0.];
        let port=solve_input_port(&old,m,source,p,c,h,b,SolverBudget::default()).unwrap();
        sum+=std::hint::black_box(port.current_a[0]+port.admittance_s[1][2]+port.node_gradient_v_per_v[6][0]);
    }
    let count=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(count,0);assert!(sum.is_finite());
    println!("DIRECT_PORT_ALLOCATION,dt={interval:.17e},solves=16,allocations={count}");
    }
}
