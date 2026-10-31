pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/monophonic_voice.rs"]mod mono;
#[path="../crates/rf-d-circuit/src/pitch_program_producer.rs"]mod reference;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use mono::{Voice,Workspace,Event,Message,stream::Frame};
use std::{io::{Write,BufWriter},time::Instant,alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);unsafe{System.alloc(l)}}unsafe fn dealloc(&self,p:*mut u8,l:Layout){unsafe{System.dealloc(p,l)}}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);unsafe{System.realloc(p,l,n)}}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
fn parameters()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
const SCORE:[Event;6]=[
 Event{offset:48,message:Message::NoteOn{note:69,velocity:100}},
 Event{offset:96,message:Message::NoteOn{note:67,velocity:100}},
 Event{offset:144,message:Message::NoteOff{note:67}},
 Event{offset:192,message:Message::NoteOff{note:69}},
 Event{offset:288,message:Message::NoteOn{note:72,velocity:100}},
 Event{offset:336,message:Message::NoteOff{note:72}},
];
fn state(out:&mut impl Write,tag:&str,s:mono::stream::startup::State)->std::io::Result<()>{write!(out,"{tag}")?;for v in s.high.into_iter().chain(s.low){write!(out,",{:016x}",v.to_bits())?;}writeln!(out)}
fn same(a:mono::stream::startup::State,b:mono::stream::startup::State)->bool{a.optional==b.optional&&a.high.into_iter().chain(a.low).zip(b.high.into_iter().chain(b.low)).all(|(x,y)|x.to_bits()==y.to_bits())}
fn rejection(v:&mut Voice,w:&mut Workspace){
 let bad:[&[Event];4]=[&[Event{offset:0,message:Message::NoteOn{note:0,velocity:1}}],&[Event{offset:64,message:Message::AllNotesOff}],&[Event{offset:2,message:Message::AllNotesOff},Event{offset:1,message:Message::AllNotesOff}],&[Event{offset:0,message:Message::NoteOff{note:255}}]];
 for e in bad{let old=v.clone();let mut out=[-0.;64];let before=ALLOCS.load(Ordering::Relaxed);assert_eq!(v.render_block(w,e,&mut out).unwrap_err(),StepError::InvalidInput);assert_eq!(before,ALLOCS.load(Ordering::Relaxed));assert!(same(v.state(),old.state()));assert_eq!(v.notes(),old.notes());assert_eq!(v.phase_law(),old.phase_law());assert_eq!(v.samples(),old.samples());assert_eq!(v.ticks(),old.ticks());assert!(v.output()==old.output());assert!(out.iter().all(|v|v.to_bits()==(-0_f64).to_bits()));}
}
fn run(block:usize,refined:bool,end:usize)->Result<(),Box<dyn std::error::Error>>{
 let clock=Instant::now();let mut v=Voice::cold_start_refined(parameters(),refined).map_err(|e|format!("DC:{e:?}"))?;let setup=clock.elapsed().as_secs_f64();let mut work=Workspace::new();let mut out=BufWriter::new(std::io::stdout().lock());writeln!(out,"SETUP,{setup:.17e},{},{},{}",std::mem::size_of::<Voice>(),std::mem::size_of::<Workspace>(),std::mem::size_of::<mono::Stats>())?;
 rejection(&mut v,&mut work);state(&mut out,"INITIAL",v.state())?;
 let mut start=0;let mut audio=[0.;128];let mut events=[Event{offset:0,message:Message::AllNotesOff};6];
 while start<end{
  let n=block.min(end-start);let mut ne=0;for e in SCORE{if(start..start+n).contains(&e.offset){events[ne]=Event{offset:e.offset-start,..e};ne+=1;}}
  let heap=ALLOCS.load(Ordering::Relaxed);let begin=Instant::now();let q=v.render_block(&mut work,&events[..ne],&mut audio[..n]);let seconds=begin.elapsed().as_secs_f64();let heap=ALLOCS.load(Ordering::Relaxed)-heap;
  let q=q.map_err(|e|format!("BLOCK {start}:{e:?}"))?;assert_eq!(heap,0);assert!(q.max_residual_a<=1e-12&&q.max_correction_v<=2e-9&&q.max_error<=1.);
  writeln!(out,"BLOCK,{start},{n},{seconds:.17e},{heap},{},{},{},{:.17e},{:.17e},{:.17e}",q.calls,q.attempts,q.iterations,q.max_residual_a,q.max_correction_v,q.max_error)?;
  for(i,x)in audio[..n].iter().enumerate(){writeln!(out,"AUDIO,{},{}",start+i,x)?;}
  start+=n;out.flush()?;
 }
 rejection(&mut v,&mut work);state(&mut out,"FINAL",v.state())?;writeln!(out,"COMPLETE,{},{},{:?}",v.samples(),v.ticks(),v.notes().lowest())?;out.flush()?;Ok(())
}
fn reference(end:usize)->Result<(),Box<dyn std::error::Error>>{
 use reference::{Producer,Stop,US,schedule::{Program,Event as E,Profile}};
 let mut score=[E::INITIAL;7];let mut notes=mono::Notes::default();let mut hz=mono::stream::startup::voice::phase::NOMINAL_HZ;
 for(k,e)in SCORE.into_iter().enumerate(){notes.apply(e.message).unwrap();if let Some(n)=notes.lowest(){hz=mono::Notes::hz(n).unwrap();}score[k+1]=E{ticks:e.offset as u64/48*1000*US,hz,key_on:notes.lowest().is_some()};}
 let program=Program::new(&score,end as u64/48*1000*US).unwrap();let mut p=Producer::cold_start(parameters(),program,Profile::HalfUs).map_err(|e|format!("DC:{e:?}"))?;let mut w=reference::stream::startup::Workspace::new();let mut frames=[reference::stream::Frame::EMPTY;128];let mut out=BufWriter::new(std::io::stdout().lock());let mut samples=0;
 loop{let r=p.pump(&mut w,128,&mut frames);for f in &frames[..r.written]{writeln!(out,"AUDIO,{},{}",f.source_index+48,f.voltage_v)?;samples+=1;}match r.stop{Stop::Complete=>break,Stop::Fault(e)=>return Err(format!("REFERENCE:{e:?}").into()),_=>{}}out.flush()?;}
 let s=p.state();write!(out,"FINAL")?;for v in s.high.into_iter().chain(s.low){write!(out,",{:016x}",v.to_bits())?;}writeln!(out,"\nCOMPLETE,{samples}")?;out.flush()?;Ok(())
}
fn main()->Result<(),Box<dyn std::error::Error>>{let a:Vec<_>=std::env::args().collect();if a.len()==3&&a[1]=="reference"{reference(a[2].parse()?)}else if a.len()==4{let block:usize=a[1].parse()?;let end:usize=a[3].parse()?;if ![64,128].contains(&block)||!(64..=480).contains(&end){return Err("bounded block/end".into());}run(block,a[2]=="refined",end)}else{Err("block coarse/refined samples | reference samples".into())}}
