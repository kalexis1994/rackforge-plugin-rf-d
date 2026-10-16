pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/nominal_render.rs"]mod render;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use render::{RenderSession,WavSink,Phase,producer::{US,stream::{Frame,startup::Workspace}}};
use std::{io::{Write,BufWriter},fs::OpenOptions,path::Path};
fn chain()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn progress(job:&RenderSession){let p=job.progress();println!("PROGRESS,{},{},{},{},{},{},{},{}",p.solved_ticks,p.consumed_ticks,p.target_ticks,p.invocations,p.accepted_steps,p.observed_frames,p.body_frames,p.pump_calls);std::io::stdout().flush().unwrap();}
fn run()->Result<i32,Box<dyn std::error::Error>>{
    let args:Vec<_>=std::env::args().collect();if args.len()!=5{return Err("expected provisional_path cancel_path quota body_ms".into());}
    let quota:usize=args[3].parse()?;let body_ms:u64=args[4].parse()?;if quota==0||quota>4096||!(1..=300).contains(&body_ms){return Err("invalid render arguments".into());}
    let cancel=Path::new(&args[2]);println!("INITIALIZING");std::io::stdout().flush()?;
    if cancel.try_exists()?{println!("CANCELLED,before_dc");return Ok(130);}
    let mut job=RenderSession::cold_start(chain(),body_ms).map_err(|e|format!("DC failed: {e:?}"))?;
    if cancel.try_exists()?{println!("CANCELLED,after_dc");return Ok(130);}
    let file=OpenOptions::new().write(true).create_new(true).open(&args[1])?;let mut sink=WavSink::new(BufWriter::with_capacity(8192,file),(body_ms*48)as u32)?;
    let mut work=Workspace::new();let mut frames=[Frame::EMPTY;128];let mut next_progress=0;
    loop{
        let batch=job.pump(&mut work,quota,&mut frames,cancel.try_exists()?);
        if batch.phase==Phase::Cancelled{progress(&job);println!("CANCELLED,between_quotas");return Ok(130);}
        if let Phase::Fault(e)=batch.phase{return Err(format!("electrical/render fault: {e:?}").into());}
        sink.write_frames(&frames[..batch.written])?;
        if job.progress().solved_ticks>=next_progress{progress(&job);next_progress=job.progress().solved_ticks+5000*US;}
        if batch.phase==Phase::Complete{
            sink.finish()?;let p=job.progress();let a=job.anchor().ok_or("missing anchor")?;
            println!("COMPLETE,{},{},{},{},{},{},{},{},{},{}",p.solved_ticks,p.consumed_ticks,p.invocations,p.accepted_steps,p.observed_frames,p.body_frames,job.producer().output().consumed(),a.source_index,a.ready_input_index,p.pump_calls);
            print!("STATE");let s=job.producer().state();for v in s.high.into_iter().chain(s.low){print!(",{v:.17e}");}println!();std::io::stdout().flush()?;return Ok(0);
        }
    }
}
fn main(){match run(){Ok(code)=>std::process::exit(code),Err(e)=>{eprintln!("NOMINAL_RENDER_ERROR: {e}");std::process::exit(2);}}}
