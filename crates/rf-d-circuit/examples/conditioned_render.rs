//! Offline caller: raw volts and exact clocks, no circuit I/O in processing.
//! Usage: conditioned_render <on|off> <1|2> <output-directory>
use rf_d_circuit::{conditioned_recipe::{self as recipe, Recipe, FinalDecay, Resolution},
    conditioned_voice::Workspace};
use std::{fs::{self,File},io::{self,Write,BufWriter},path::Path,time::Instant};

fn record(w:&mut impl Write,ticks:u64,values:[f64;5])->io::Result<()> {
    w.write_all(&ticks.to_le_bytes())?;
    for v in values { if !v.is_finite(){return Err(io::Error::other("nonfinite observation"));} w.write_all(&v.to_le_bytes())?; }
    Ok(())
}
fn state(w:&mut impl Write,q:rf_d_circuit::conditioned_engine::Checkpoint)->io::Result<()> {
    w.write_all(&q.elapsed_ticks.to_le_bytes())?;
    for v in q.state.high.into_iter().chain(q.state.low) {w.write_all(&v.to_le_bytes())?;}
    Ok(())
}
fn run()->Result<(),Box<dyn std::error::Error>> {
    let args:Vec<_>=std::env::args().collect();
    if args.len()!=4 {return Err("usage: conditioned_render <on|off> <1|2> <output-directory>".into());}
    let final_decay=match args[1].as_str(){"on"=>FinalDecay::On,"off"=>FinalDecay::Off,_=>return Err("final decay: on|off".into())};
    let resolution=match args[2].as_str(){"1"=>Resolution::Half1Us,"2"=>Resolution::Half2Us,_=>return Err("maximum half-step: 1|2 us".into())};
    let recipe=Recipe{final_decay,resolution};
    // Exclusive output directory preserves any failed or previous render.
    let dir=Path::new(&args[3]);fs::create_dir(dir)?;
    let mut trace=BufWriter::new(File::create(dir.join("j7.bin"))?);
    let mut steps=BufWriter::new(File::create(dir.join("steps.bin"))?);
    let mut grids=BufWriter::new(File::create(dir.join("grids.bin"))?);
    let mut events=BufWriter::new(File::create(dir.join("events.txt"))?);
    trace.write_all(b"RFJ7TR01")?;steps.write_all(b"RFSTPS01")?;grids.write_all(b"RFGRID01")?;
    let mut engine=recipe.engine().map_err(|e|format!("history:{e:?}"))?;
    let mut workspace=Workspace::new();let q=engine.checkpoint();
    record(&mut trace,q.elapsed_ticks,[194,46,43,12,39].map(|i|q.state.high[i]+q.state.low[i]))?;
    state(&mut grids,q)?;
    let started=Instant::now();let(mut phase,mut accepted)=(0,0);
    recipe.apply(&mut engine,phase).map_err(|e|format!("source:{e:?}"))?;
    writeln!(events,"EVENT,{phase},{},0,false",q.elapsed_ticks)?;
    for target in recipe::TARGETS {
        while engine.checkpoint().elapsed_ticks<target {
            if started.elapsed().as_secs_f64()>900.0 {return Err("900 s offline wall budget".into());}
            let old=engine.checkpoint();
            let a=engine.advance_to(&mut workspace,target).map_err(|e|format!("advance at {}:{e:?}",old.elapsed_ticks))?;
            let after=engine.checkpoint();
            for n in [old.elapsed_ticks,after.elapsed_ticks] {steps.write_all(&n.to_le_bytes())?;}
            for n in [a.half_ticks,a.attempts] {steps.write_all(&n.to_le_bytes())?;}
            steps.write_all(&a.error_ratio.to_le_bytes())?;steps.write_all(&after.next_full_ticks.to_le_bytes())?;
            for ep in a.endpoints {
                let o=ep.observations;
                record(&mut trace,ep.elapsed_ticks,[o.j7_v,o.saw_v,o.ramp_v,o.bus_v,o.cursor_v])?;
            }
            accepted+=1;
        }
        state(&mut grids,engine.checkpoint())?;
        if phase+1<recipe::EVENTS.len() && target==recipe::EVENTS[phase+1].elapsed_ticks {
            phase+=1;recipe.apply(&mut engine,phase).map_err(|e|format!("source:{e:?}"))?;
            let e=recipe::EVENTS[phase];writeln!(events,"EVENT,{phase},{},{},{}",e.elapsed_ticks,e.keyboard_v,e.short)?;
        }
    }
    trace.flush()?;steps.flush()?;grids.flush()?;events.flush()?;
    println!("COMPLETE,recipe={},accepted={accepted},fine={},start={},end={}",recipe::ID,2*accepted,recipe::START_TICKS,recipe::END_TICKS);
    Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
