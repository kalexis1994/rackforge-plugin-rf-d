use rf_d_circuit::vco_jfet::companion;
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
fn full_jfet_stamps_use_no_heap() {
 let before=ALLOCATIONS.load(Ordering::Relaxed);let mut sum=0.;
 for i in 0..10000 {
  let h=0.5+(i%100) as f64*0.001;
  let nodes=if i%2==0 {[h,0.,1.]} else {[1.,0.,h]};
  let result=companion(nodes,[1.5,0.,1.],125e-9).unwrap();
  sum+=std::hint::black_box(result.current_a[0]+result.jacobian_s[1][1]);
 }
 let allocations=ALLOCATIONS.load(Ordering::Relaxed)-before;assert_eq!(allocations,0);assert!(sum.is_finite());
 println!("VCO_JFET_ALLOCATION,stamps=10000,allocations={allocations}");
}
