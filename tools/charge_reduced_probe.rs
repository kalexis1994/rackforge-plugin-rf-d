pub use rf_d_circuit::{StepError,junction_charge};
#[path="charge_reduced_kernel.rs"]mod core;
#[path="../crates/rf-d-circuit/src/j7_stream_output.rs"]mod stream;
use std::{io::{Write,BufWriter},time::Instant,alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);unsafe{System.alloc(l)}}unsafe fn dealloc(&self,p:*mut u8,l:Layout){unsafe{System.dealloc(p,l)}}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);unsafe{System.realloc(p,l,n)}}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
fn input(k:usize)->f64{let t=k as f64/384000.;1e-3*((std::f64::consts::TAU*137.*t).sin()+0.3*(std::f64::consts::TAU*1103.*t).sin())}
fn same(a:core::State,b:core::State)->bool{a.q.into_iter().chain([a.input_v]).zip(b.q.into_iter().chain([b.input_v])).all(|(a,b)|a.to_bits()==b.to_bits())}
fn rejected(case:usize,s:core::State){for u in [f64::NAN,f64::INFINITY,0.00130001]{let mut x=s;let count=ALLOCS.load(Ordering::Relaxed);assert!(core::step(case,&mut x,u).is_err());assert!(same(x,s));let mut other=s;core::step(case,&mut x,0.).unwrap();core::step(case,&mut other,0.).unwrap();assert!(same(x,other));assert_eq!(count,ALLOCS.load(Ordering::Relaxed));}}
fn vectors()->Result<(),Box<dyn std::error::Error>>{let mut out=BufWriter::new(std::io::stdout().lock());for case in 0..2{let mut s=core::State::ZERO;s.q[0]=-0.;s.input_v=-0.;rejected(case,s);
 for k in 0..512{let before=ALLOCS.load(Ordering::Relaxed);let v=core::step(case,&mut s,input(k)).unwrap();let nodes=core::nodes(case,s).unwrap();assert_eq!(before,ALLOCS.load(Ordering::Relaxed));for x in [input(k),v.bus_v,v.base_v,v.j7_v,v.panel_a].into_iter().chain(s.q).chain(nodes){out.write_all(&x.to_le_bytes())?;}}rejected(case,s);}out.flush()?;Ok(())}
fn bench()->Result<(),Box<dyn std::error::Error>>{let mut out=BufWriter::new(std::io::stdout().lock());for case in 0..2{let setup=Instant::now();let mut s=core::State::ZERO;let mut fir=stream::Decimator::new(0.).unwrap();let setup=setup.elapsed().as_secs_f64();let mut raw=[0.;1024];let mut input_buffer=[0.;1024];let mut frames=[stream::Frame::EMPTY;128];let mut checksum=0.;
 writeln!(out,"SETUP,{case},{setup:.17e},{},{}",std::mem::size_of::<core::State>(),std::mem::size_of::<stream::Decimator>())?;
 for block in 0..1200{for k in 0..1024{input_buffer[k]=input(block*1024+k);}
  let count=ALLOCS.load(Ordering::Relaxed);let time=Instant::now();for k in 0..1024{raw[k]=core::step(case,&mut s,input_buffer[k]).unwrap().j7_v;}let n=fir.push(&raw,&mut frames).unwrap();let seconds=time.elapsed().as_secs_f64();let heap=ALLOCS.load(Ordering::Relaxed)-count;assert_eq!(heap,0);for f in &frames[..n]{checksum+=std::hint::black_box(f.voltage_v);}
  writeln!(out,"BLOCK,{case},{block},{seconds:.17e},{heap},{n}")?;
 }writeln!(out,"COMPLETE,{case},{checksum:.17e},{},{}",fir.consumed(),fir.produced())?;
 }out.flush()?;Ok(())}
fn main()->Result<(),Box<dyn std::error::Error>>{if std::env::args().nth(1).as_deref()==Some("vectors"){vectors()}else{bench()}}
