pub use rf_d_circuit::StepError;
#[path="../crates/rf-d-circuit/src/j7_antialias.rs"]mod aa;
use std::{io::{Write,BufWriter},alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
fn main(){
    let mut out=BufWriter::new(std::io::stdout());let mut heap=0;
    for factor in[4,8]{let fs=48000.*factor as f64;
        for hz in[0.,1000.,19000.,20000.,24000.,30000.,47000.,60000.,90000.,180000.]{
            let x: [f64;3073]=std::array::from_fn(|i|(std::f64::consts::TAU*hz*i as f64/fs).cos());let mut y=[0.;257];let count=ALLOCS.load(Ordering::Relaxed);
            aa::convert(&x,&mut y,factor).unwrap();heap+=ALLOCS.load(Ordering::Relaxed)-count;
            for (n,v) in y.into_iter().enumerate(){writeln!(out,"TONE,{factor},{hz},{n},{v:0.17e}").unwrap();}
        }
    }
    assert_eq!(heap,0);writeln!(out,"FILTER_HEAP,{heap}").unwrap();out.flush().unwrap();
}
