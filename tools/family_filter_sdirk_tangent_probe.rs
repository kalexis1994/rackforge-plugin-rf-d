#[path="family_mixer_data128.rs"]mod data;
#[path="family_filter_sdirk_kernel.rs"]mod core;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use core::{State,N,BUS,PHASE};use rf_d_circuit::{chain_charge,StepError};
use std::{io::{Write,BufWriter},alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static CALLS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{CALLS.fetch_add(1,Ordering::Relaxed);unsafe{System.alloc(l)}}unsafe fn dealloc(&self,p:*mut u8,l:Layout){unsafe{System.dealloc(p,l)}}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{CALLS.fetch_add(1,Ordering::Relaxed);unsafe{System.realloc(p,l,n)}}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
fn parameters(r61:f64,load:usize)->chain_charge::Parameters{let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=r61;chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new(if load==0{[false,false,false,false,true]}else{[false,true,true,true,true]},[0.5;4]).unwrap()}}
fn initial(p:chain_charge::Parameters,cv:f64)->Result<State,StepError>{let s=rf_d_circuit::circuit66::initial_state(p.circuit,p.conversion,p.headphone,p.boundary,lab::SEED)?;let mut x=[0.;N];x[..66].copy_from_slice(&s.node_v);x[BUS]=-0.01;x[67]=s.node_v[22];Ok(core::solve(p,cv,State::new(x),1e-6,true,64)?.state)}
fn values(out:&mut impl Write,s:State)->std::io::Result<()>{for v in s.high.into_iter().chain(s.low){write!(out,",{v:.17e}")?;}Ok(())}
fn roots()->Result<(),Box<dyn std::error::Error>>{let mut out=BufWriter::new(std::io::stdout().lock());for r61 in [200.,200000.]{for load in [0,1]{for cv in [-2.6,-1.6,-0.6]{let p=parameters(r61,load);let dc=initial(p,cv).map_err(|e|format!("DC {r61} {load} {cv}: {e:?}"))?;write!(out,"DC,{r61},{load},{cv}")?;values(&mut out,dc)?;writeln!(out)?;if cv==-1.6{for phase in [0.,0.37]{let mut old=dc;old.high[PHASE]=phase;for h in [0.5e-6,2e-6]{let q=core::solve(p,cv,old,h,false,64).map_err(|e|format!("ROOT {r61} {load} {phase} {h}: {e:?}"))?;write!(out,"ROOT,{r61},{load},{cv},{phase},{h:.17e},{:.17e},{:.17e}",q.residual_ratio,q.correction_ratio)?;values(&mut out,old)?;values(&mut out,q.state)?;writeln!(out)?;}}}}}}out.flush()?;Ok(())}
fn walk(cv:f64,h:f64)->Result<(),Box<dyn std::error::Error>>{let p=parameters(200.,1);let mut s=initial(p,cv).map_err(|e|format!("DC {e:?}"))?;let saved=s;let count=CALLS.load(Ordering::Relaxed);assert!(core::process(p,cv,&mut s,h,0).is_err());assert_eq!(s,saved);assert!(core::process(p,f64::NAN,&mut s,h,64).is_err());assert_eq!(s,saved);assert_eq!(count,CALLS.load(Ordering::Relaxed));let a=core::process(p,cv,&mut s,h,64).map_err(|e|format!("FIRST {e:?}"))?;let mut retry=saved;let b=core::process(p,cv,&mut retry,h,64).unwrap();assert_eq!(s,retry);assert_eq!(a.residual_ratio.to_bits(),b.residual_ratio.to_bits());s=saved;
 let mut out=BufWriter::with_capacity(65536,std::io::stdout().lock());let mut steps=0_u64;let(mut maxr,mut maxc)=(0_f64,0_f64);let begin=CALLS.load(Ordering::Relaxed);let mut stage_board=0.;
 loop{let current=core::current(cv,s).unwrap();let other=p.mixer.admittance_s()[5][5]*s.value(BUS);let board=-current-other;for v in [steps as f64*h,s.value(PHASE),s.value(BUS),s.value(6),s.value(61),current,board,s.value(5),s.value(65),stage_board,if steps==0{0.}else{core::algebraic(p,cv,s).unwrap()}]{out.write_all(&v.to_le_bytes())?;}
  if s.value(PHASE)>=1.{break;}if steps>=40000{return Err("endpoint budget".into());}
  let start=CALLS.load(Ordering::Relaxed);let q=core::process(p,cv,&mut s,h,64).map_err(|e|format!("STEP {steps}: {e:?}"))?;assert_eq!(start,CALLS.load(Ordering::Relaxed));maxr=maxr.max(q.residual_ratio);maxc=maxc.max(q.correction_ratio);stage_board=-core::current(cv,q.stage).unwrap()-p.mixer.admittance_s()[5][5]*q.stage.value(BUS);steps+=1;
 }
 let heap=CALLS.load(Ordering::Relaxed)-begin;out.flush()?;assert_eq!(heap,0);eprintln!("COMPLETE,{steps},{maxr:.17e},{maxc:.17e},{heap},2,true");Ok(())}
fn historical_main()->Result<(),Box<dyn std::error::Error>>{let a:Vec<_>=std::env::args().collect();if a.len()==2&&a[1]=="roots"{roots()}else if a.len()==3{walk(a[1].parse()?,a[2].parse::<f64>()?*1e-9)}else{Err("roots or cv step_ns".into())}}

fn main()->Result<(),Box<dyn std::error::Error>>{
 use std::io::BufRead;
 for line in std::io::stdin().lock().lines(){let line=line?;let z:Vec<_>=line.split(',').collect();let index:usize=z[0].parse()?;let p=parameters(z[1].parse()?,z[2].parse()?);let cv:f64=z[3].parse()?;let h:f64=z[5].parse()?;
 let v:Vec<f64>=z[8..].iter().map(|s|s.parse().unwrap()).collect();assert_eq!(v.len(),276);let old=State{high:std::array::from_fn(|k|v[k]),low:std::array::from_fn(|k|v[69+k])};let delta=State::new(std::array::from_fn(|k|(v[138+k]-v[k])+(v[207+k]-v[69+k])));
 let s=core::linearize(p,cv,old,delta,h,false).map_err(|e|format!("{e:?}"))?;print!("J,{index}");for row in 0..N{for col in [6,66,68]{print!(",{:.17e}",s.j[row][col]);}}println!();
 }Ok(())}
