#[path="vco_family_data.rs"] mod data;
#[path="vco_family_kernel.rs"] mod kernel;
use std::alloc::{GlobalAlloc,Layout,System};
use std::sync::atomic::{AtomicUsize,Ordering};
struct Count;
static CALLS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Count {
    unsafe fn alloc(&self,l:Layout)->*mut u8 { CALLS.fetch_add(1,Ordering::Relaxed); unsafe{System.alloc(l)} }
    unsafe fn dealloc(&self,p:*mut u8,l:Layout) { unsafe{System.dealloc(p,l)} }
    unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8 { CALLS.fetch_add(1,Ordering::Relaxed); unsafe{System.realloc(p,l,n)} }
}
#[global_allocator]static ALLOCATOR:Count=Count;
fn main(){
    for cv in [-3.1,-2.6,-2.1,-1.6,-1.1,-0.6,-0.1] {
        for bus in [-0.125,-0.0625,0.,0.0625,0.125] { for phase in [0.,0.001,0.125,0.333,0.5,0.999,1.] {
            let before=CALLS.load(Ordering::Relaxed);
            let q=kernel::evaluate(cv,bus,phase).unwrap();
            assert_eq!(before,CALLS.load(Ordering::Relaxed));
            print!("Q,{cv:.17e},{bus:.17e},{phase:.17e}");
            for v in q.values.into_iter().chain(q.dcv).chain(q.dbus) { print!(",{v:.17e}"); } println!();
        } }
    }
    for(cv,bus,p)in [(f64::NAN,0.,0.),(-3.10001,0.,0.),(-0.09999,0.,0.),(-2.,-0.12501,0.),(-2.,0.12501,0.),(-2.,f64::INFINITY,0.),(-2.,0.,f64::NAN),(-2.,0.,-0.001),(-2.,0.,1.001)] {
        let before=CALLS.load(Ordering::Relaxed);assert!(kernel::evaluate(cv,bus,p).is_err());assert_eq!(before,CALLS.load(Ordering::Relaxed));
    }
    eprintln!("COMPLETE,245,9,0");
}
