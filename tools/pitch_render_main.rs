pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/pitch_program_render.rs"]mod render;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use render::{RenderSession,WavSink,Phase,producer::{US,schedule::{Program,Event,Profile},stream::{self,Frame,startup::{voice,Workspace}}}};
use voice::phase::NOMINAL_HZ;
use std::{io::{Write,BufWriter},fs::OpenOptions,path::Path,alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
struct Counter;static ALLOCS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter{unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}}
#[global_allocator]static ALLOCATOR:Counter=Counter;
fn chain()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn score()->Program{Program::new(&[Event::INITIAL,Event{ticks:1000*US,key_on:true,..Event::INITIAL},Event{ticks:100000*US,hz:1.5*NOMINAL_HZ,key_on:true},Event{ticks:200000*US,hz:0.5*NOMINAL_HZ,key_on:true},Event{ticks:250000*US,hz:0.5*NOMINAL_HZ,key_on:false}],301000*US).unwrap()}
fn progress(job:&RenderSession){let p=job.progress();println!("PROGRESS,{},{},{},{},{},{},{},{}",p.solved_ticks,p.consumed_ticks,p.target_ticks,p.invocations,p.accepted_steps,p.observed_frames,p.body_frames,p.pump_calls);std::io::stdout().flush().unwrap();}
fn run()->Result<i32,Box<dyn std::error::Error>>{
    let args:Vec<_>=std::env::args().collect();if args.len()!=6{return Err("expected provisional_path cancel_path quota profile audit".into());}
    let quota:usize=args[3].parse()?;let profile=match args[4].as_str(){"1"=>Profile::OneUs,"0.5"=>Profile::HalfUs,_=>return Err("profile must be 1 or 0.5 us".into())};let audit=match args[5].as_str(){"audit"=>true,"render"=>false,_=>return Err("invalid mode".into())};if quota==0||quota>4096{return Err("invalid quota".into());}
    let cancel=Path::new(&args[2]);println!("INITIALIZING");std::io::stdout().flush()?;
    if cancel.try_exists()?{println!("CANCELLED,before_dc");return Ok(130);}
    let mut job=RenderSession::cold_start(chain(),score(),profile,300).map_err(|e|format!("DC failed: {e:?}"))?;
    if cancel.try_exists()?{println!("CANCELLED,after_dc");return Ok(130);}
    let file=OpenOptions::new().write(true).create_new(true).open(&args[1])?;let mut sink=WavSink::new(BufWriter::with_capacity(8192,file),14400)?;
    let mut work=Workspace::new();let mut frames=[Frame::EMPTY;128];let mut all=[0.;14401];let mut count=0;
    let mut raw=stream::reference_readout::Buffer::<115585>::new(job.producer().state()).unwrap();
    let(mut heap,mut residual,mut correction,mut error,mut min_h)=(0_usize,0_f64,0_f64,0_f64,1_f64);let mut events=[[0.;236];4];let event_ticks=[1000*US,100000*US,200000*US,250000*US];let(mut time,mut event_count,mut late_cancel)=(0_u64,0_usize,false);
    let before=job.progress();let z=job.pump(&mut work,0,&mut frames,false);assert_eq!(z.invocations,0);assert_eq!(z.written,0);assert_eq!(job.progress().solved_ticks,before.solved_ticks);
    let mut next_progress=0;
    loop{
        let cancelled=cancel.try_exists()?;let n=ALLOCS.load(Ordering::Relaxed);
        let batch=if audit{job.run(&mut work,quota,&mut frames,cancelled,|w,p,s,c,h|{
            assert_eq!(p.time.to_bits(),(time as f64*stream::reference_readout::TICK_S).to_bits());let old=*s;let q=voice::advance(w,p,s,c,h)?;let span=(q.h/stream::reference_readout::TICK_S).round()as u64;
            raw.append(old,&q,time,span)?;time+=span;min_h=min_h.min(q.h);error=error.max(q.error);for pair in [&q.coarse,&q.fine[0],&q.fine[1]]{residual=residual.max(pair.residual_a);correction=correction.max(pair.correction_v);}
            if event_count<4{assert!(time<=event_ticks[event_count]);if time==event_ticks[event_count]{events[event_count][..118].copy_from_slice(&s.high);events[event_count][118..].copy_from_slice(&s.low);event_count+=1;}}
            Ok(q)
        })}else{job.pump(&mut work,quota,&mut frames,cancelled)};
        heap+=ALLOCS.load(Ordering::Relaxed)-n;
        if batch.phase==Phase::Cancelled{progress(&job);println!("CANCELLED,between_quotas");return Ok(130);}
        if let Phase::Fault(e)=batch.phase{return Err(format!("electrical/render fault: {e:?}").into());}
        if audit{for f in &frames[..batch.written]{assert_eq!(f.source_index,count as u64);all[count]=f.voltage_v;count+=1;}}
        sink.write_frames(&frames[..batch.written])?;
        if audit&&!late_cancel&&job.progress().solved_ticks>=100000*US{
            let mut branch=job.clone();let old=branch.progress();let state=branch.producer().state();let output=branch.producer().output().clone();let mut out=[Frame::EMPTY;1];let sentinel=out;
            for flag in [true,false,true]{let n=ALLOCS.load(Ordering::Relaxed);let b=branch.pump(&mut work,4096,&mut out,flag);heap+=ALLOCS.load(Ordering::Relaxed)-n;assert_eq!(b.phase,Phase::Cancelled);assert_eq!(b.written,0);assert_eq!(b.invocations,0);assert_eq!(branch.progress(),old);assert!(branch.producer().state()==state);assert!(branch.producer().output()==&output);assert_eq!(out,sentinel);}
            late_cancel=true;
        }
        if job.progress().solved_ticks>=next_progress{progress(&job);next_progress=job.progress().solved_ticks+10000*US;}
        if batch.phase==Phase::Complete{
            sink.finish()?;let p=job.progress();let a=job.anchor().ok_or("missing anchor")?;
            println!("COMPLETE,{},{},{},{},{},{},{},{},{},{}",p.solved_ticks,p.consumed_ticks,p.invocations,p.accepted_steps,p.observed_frames,p.body_frames,job.producer().output().consumed(),a.source_index,a.ready_input_index,p.pump_calls);
            print!("STATE");let s=job.producer().state();for v in s.high.into_iter().chain(s.low){print!(",{v:.17e}");}println!();
            if audit{
                assert_eq!(heap,0);assert!(late_cancel);assert_eq!(event_count,4);assert_eq!(count,14400);all[count]=a.voltage_v;assert_eq!(raw.samples().len(),115585);let mut aa8=[0.;14401];let mut half=[0.;57793];for(k,v)in raw.samples().iter().step_by(2).enumerate(){half[k]=*v;}let mut aa4=[0.;14401];
                stream::reference_filter::convert(raw.samples(),&mut aa8,8).unwrap();stream::reference_filter::convert(&half,&mut aa4,4).unwrap();for k in 0..14401{assert_eq!(all[k].to_bits(),aa8[k].to_bits());}
                println!("AUDIT,{heap},{residual:.17e},{correction:.17e},{error:.17e},{min_h:.17e},{event_count},{late_cancel}");
                let stdout=std::io::stdout();let mut out=BufWriter::new(stdout.lock());for(k,t)in event_ticks.into_iter().enumerate(){write!(out,"EVENT,{t}")?;for x in events[k]{write!(out,",{x:.17e}")?;}writeln!(out)?;}
                for(tag,values)in [("RAW",raw.samples()),("AA4",&aa4[..]),("AA8",&aa8[..])]{for(k,v)in values.iter().enumerate(){writeln!(out,"{tag},{k},{v:.17e}")?;}}out.flush()?;
            }
            std::io::stdout().flush()?;return Ok(0);
        }
    }
}
fn main(){match run(){Ok(code)=>std::process::exit(code),Err(e)=>{eprintln!("PITCH_RENDER_ERROR: {e}");std::process::exit(2);}}}
#[cfg(test)]mod render_tests{
    use super::*;
    #[test]fn scene_body_requires_its_actual_right_support(){for body in [0,1,299,301,u64::MAX]{assert!(RenderSession::cold_start(chain(),score(),Profile::HalfUs,body).is_err());}}
}
