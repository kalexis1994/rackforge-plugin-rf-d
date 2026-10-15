pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/nominal_chain_startup.rs"]mod startup;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use startup::*;
use std::{io::{self,Read},alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
fn raw()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn scene()->Parameters{Parameters::new(raw()).unwrap()}
fn retry(p:Parameters,x:State){let r=initialize(p,x,100).unwrap();assert_eq!(r.state,x);assert_eq!(r.iterations,1);}
fn main(){let mut bytes=Vec::new();io::stdin().read_to_end(&mut bytes).unwrap();assert_eq!(bytes.len(),16*M);let a:[f64;2*M]=std::array::from_fn(|k|f64::from_le_bytes(bytes[8*k..8*k+8].try_into().unwrap()));let state=|i:usize|State{high:std::array::from_fn(|k|a[i*M+k]),low:std::array::from_fn(|k|a[i*M+N+k]),optional:false};let x=state(0);let guess=state(1);let p=scene();let before=ALLOCS.load(Ordering::Relaxed);let mut rejects=0;
    for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut bad=x;bad.high[0]=value;assert!(initialize(p,bad,100).is_err());retry(p,x);bad=x;bad.low[0]=value;assert!(initialize(p,bad,100).is_err());retry(p,x);rejects+=2;}
    let mut bad=x;bad.low[0]=1e-3;assert!(initialize(p,bad,100).is_err());retry(p,x);bad=x;bad.high[0]=40.;assert!(initialize(p,bad,100).is_err());retry(p,x);bad=x;bad.optional=true;assert!(initialize(p,bad,100).is_err());retry(p,x);rejects+=3;
    for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY,-1.,1e-6]{let mut pp=p;pp.time=value;assert!(initialize(pp,x,100).is_err());retry(p,x);rejects+=1;}
    for budget in[0,101,usize::MAX]{assert!(initialize(p,x,budget).is_err());retry(p,x);rejects+=1;}
    assert!(matches!(initialize(p,guess,1),Err(StepError::IterationBudget)));retry(p,x);rejects+=1;

    assert!(startup::numerical_guess(raw(),2).is_err());assert_eq!(startup::cold_start(raw()).unwrap().state,x);rejects+=1;
    for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut bad=raw();bad.circuit.cutoff.q26.beta_forward=value;assert!(startup::cold_start(bad).is_err());assert_eq!(startup::cold_start(raw()).unwrap().state,x);rejects+=1;}
    let heap=ALLOCS.load(Ordering::Relaxed)-before;assert_eq!(heap,0);assert_eq!(rejects,22);println!("STARTUP_GUARDS,{rejects},{rejects},{heap}");
}
