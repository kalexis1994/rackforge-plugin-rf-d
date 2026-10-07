#[path = "../src/mixer_on.rs"]
mod mixer_on;
#[path = "../src/mixer_c27.rs"]
mod mixer_c27;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};
struct Count;
static ALLOCATIONS: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Count {
    unsafe fn alloc(&self,l:Layout)->*mut u8 { ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.alloc(l)} }
    unsafe fn alloc_zeroed(&self,l:Layout)->*mut u8 { ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.alloc_zeroed(l)} }
    unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8 { ALLOCATIONS.fetch_add(1,Ordering::Relaxed);unsafe {System.realloc(p,l,n)} }
    unsafe fn dealloc(&self,p:*mut u8,l:Layout) { unsafe {System.dealloc(p,l)} }
}
#[global_allocator]
static ALLOCATOR:Count=Count;
#[test]
fn ten_thousand_dynamic_port_evaluations_use_no_heap() {
    let before=ALLOCATIONS.load(Ordering::Relaxed);
    let mut sum=0.0;
    for i in 0..10000 {
        let alpha=(i%101) as f64/100.0;
        let p=mixer_c27::C27OnPort::new(mixer_on::OnMixer::new([true;5],[alpha;4]).unwrap()).unwrap();
        let r=p.evaluate([1.0,-0.4,0.3,-0.2,0.5],0.2,-0.3,20e-6).unwrap();
        sum+=std::hint::black_box(r.current_a[5]+r.jacobian_s[1][2]+r.next_capacitor_v);
    }
    let count=ALLOCATIONS.load(Ordering::Relaxed)-before;
    assert_eq!(count,0);assert!(sum.is_finite());
    println!("C27_ALLOCATION,evaluations=10000,allocations={count}");
}
