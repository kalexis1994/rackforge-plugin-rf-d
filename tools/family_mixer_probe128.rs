#[path="family_mixer_data128.rs"]mod data;
#[path="family_mixer_kernel128.rs"]mod coupling;
use std::alloc::{GlobalAlloc,Layout,System};use std::sync::atomic::{AtomicUsize,Ordering};
use std::io::{Write,BufWriter};
struct Count;static CALLS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Count{unsafe fn alloc(&self,l:Layout)->*mut u8{CALLS.fetch_add(1,Ordering::Relaxed);unsafe{System.alloc(l)}}unsafe fn dealloc(&self,p:*mut u8,l:Layout){unsafe{System.dealloc(p,l)}}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{CALLS.fetch_add(1,Ordering::Relaxed);unsafe{System.realloc(p,l,n)}}}
#[global_allocator]static A:Count=Count;
fn equal(a:coupling::State,b:coupling::State)->bool{a.phase.into_iter().chain(a.bus).zip(b.phase.into_iter().chain(b.bus)).all(|(x,y)|x.to_bits()==y.to_bits())}
fn emit(out:&mut impl Write,time:f64,s:coupling::State,o:coupling::Observation,rr:f64,cr:f64)->std::io::Result<()>{let v=o.value;for x in [time,s.phase[0]+s.phase[1],s.bus[0]+s.bus[1],v[1],v[2],v[3],v[8],v[11],o.other_a,o.board_a,v[4],v[14],rr,cr]{out.write_all(&x.to_le_bytes())?;}Ok(())}
fn main()->Result<(),Box<dyn std::error::Error>>{
 let a:Vec<_>=std::env::args().collect();if a.len()!=5{return Err("cv load initial_bus step_ns".into());}let cv:f64=a[1].parse()?;let load:usize=a[2].parse()?;let initial:f64=a[3].parse()?;let h=a[4].parse::<f64>()?*1e-9;
 let mut s=coupling::initialize(initial).map_err(|e|format!("{e:?}"))?;let original=s;
 let before=CALLS.load(Ordering::Relaxed);assert!(coupling::process(cv,load,&mut s,h,0).is_err());assert!(equal(s,original));assert!(coupling::process(f64::NAN,load,&mut s,h,32).is_err());assert!(equal(s,original));assert!(coupling::process(cv,99,&mut s,h,32).is_err());assert!(equal(s,original));assert_eq!(CALLS.load(Ordering::Relaxed),before);
 let q=coupling::process(cv,load,&mut s,h,32).unwrap();let retry=coupling::step(cv,load,original,h,32).unwrap();assert!(equal(s,retry.state));s=original;
 let mut out=BufWriter::with_capacity(65536,std::io::stdout().lock());emit(&mut out,0.,s,coupling::observe(cv,load,s).unwrap(),0.,0.)?;
 let(mut steps,mut maxr,mut maxc,mut maxk,mut charge,mut iterations)=(0_u64,0_f64,0_f64,0_f64,0_f64,0_usize);let start=CALLS.load(Ordering::Relaxed);
 while s.phase[0]+s.phase[1]<2.{if steps>=100000{return Err("endpoint budget".into());}let before=CALLS.load(Ordering::Relaxed);let q=coupling::process(cv,load,&mut s,h,32).map_err(|e|format!("step {steps}: {e:?}"))?;assert_eq!(CALLS.load(Ordering::Relaxed),before);
 steps+=1;maxr=maxr.max(q.residual_ratio);maxc=maxc.max(q.correction_ratio);maxk=maxk.max((q.observation.value[11]+q.observation.other_a+q.observation.board_a).abs());charge+=q.charge_residual_c;iterations=iterations.max(q.iterations);emit(&mut out,steps as f64*h,s,q.observation,q.residual_ratio,q.correction_ratio)?;
 }
 let allocated=CALLS.load(Ordering::Relaxed)-start;out.flush()?;assert_eq!(allocated,0);eprintln!("COMPLETE,{steps},{maxr:0.17e},{maxc:0.17e},{maxk:0.17e},{charge:0.17e},{iterations},{allocated},3,true");let _=q;Ok(())
}
