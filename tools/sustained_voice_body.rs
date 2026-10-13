// Offline replay storage is bounded; accepted pairs are never accumulated.
struct Probe{engine:temporal::Engine,start:u64,name:String,count:u32}
fn add_probe(probes:&mut Vec<Probe>,saved:Saved,name:String,dir:&std::path::Path)->Result<(),String>{
 if probes.len()>=3{return Err("bounded replay capacity".into());}
 let bytes=encode(saved);fs::write(dir.join(&name),bytes).map_err(|e|e.to_string())?;
 let restored=decode(&fs::read(dir.join(&name)).map_err(|e|e.to_string())?)?;
 if encode(restored)!=bytes{return Err("checkpoint roundtrip".into());}
 probes.push(Probe{engine:temporal::Engine::restore(restored.q).map_err(|e|format!("restore:{e:?}"))?,start:saved.q.elapsed_ticks,name,count:0});Ok(())
}
fn cuts(phase:usize)->Vec<u64>{
 let end=START+REL[phase+1];if phase==0{return vec![end];}
 let mut out=Vec::new();let mut cut=START+REL[phase]+CUT;
 while cut<end{out.push(cut);cut+=CUT;}out.push(end);out
}
fn run()->Result<(),String>{
 let args:Vec<_>=std::env::args().collect();if args.len()!=3{return Err("usage: sustained_voice <1|2> <new-output-directory>".into());}
 let resolution=match args[1].as_str(){"1"=>rf_d_circuit::conditioned_recipe::Resolution::Half1Us,"2"=>rf_d_circuit::conditioned_recipe::Resolution::Half2Us,_=>return Err("resolution 1|2 us".into())};
 let recipe=rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution};
 let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).map_err(|e|e.to_string())?;
 let mut engine=recipe.engine().map_err(|e|format!("own history:{e:?}"))?;let mut workspace=joint::Workspace::new();
 let mut saved=Saved{q:engine.checkpoint(),phase:0};let bytes=encode(saved);
 for kind in 0..4{let mut b=bytes;match kind{0=>b[0]^=1,1=>b[56+8*225..64+8*225].copy_from_slice(&f64::NAN.to_le_bytes()),2=>b[28..32].copy_from_slice(&9_u32.to_le_bytes()),_=>b[24..28].copy_from_slice(&3_u32.to_le_bytes())}if decode(&b).is_ok(){return Err("corruption accepted".into());}}
 if engine.advance_to(&mut workspace,START).is_ok()||encode(Saved{q:engine.checkpoint(),phase:0})!=bytes{return Err("invalid destination rollback".into());}
 let mut w=std::io::BufWriter::new(fs::File::create(dir.join("selected.txt")).map_err(|e|e.to_string())?);
 let mut cps=fs::File::create(dir.join("checkpoints.bin")).map_err(|e|e.to_string())?;
 let mut replay_log=std::io::BufWriter::new(fs::File::create(dir.join("replays.txt")).map_err(|e|e.to_string())?);
 writeln!(w,"PROFILE,1,{}",saved.q.settings.maximum_half_ticks).unwrap();write_state(&mut w,saved.q.state);cps.write_all(&bytes).unwrap();
 let started=Instant::now();let mut last_ramp=saved.q.state.high[43]+saved.q.state.low[43];let mut last_ticks=START;
 let mut total=std::array::from_fn::<_,9,_>(|_|Sum::default());let(mut accepted_count,mut replay_count,mut restores,mut rollbacks,mut crossings,mut max_probes)=(0,0,0,1,0,0);
 for phase in 0..3{
  let incoming=encode(saved);engine.trigger(KEY[phase],SHORT[phase]).map_err(|e|format!("source:{e:?}"))?;
  saved=Saved{q:engine.checkpoint(),phase:phase as u32};let changed=encode(saved);if incoming[56..]!=changed[56..]{return Err("source changed accepted charges".into());}
  writeln!(w,"BOUNDARY,{phase},{},{:.17e},{}",saved.q.elapsed_ticks,KEY[phase],SHORT[phase] as u32).unwrap();write_state(&mut w,saved.q.state);cps.write_all(&changed).unwrap();
  let end=START+REL[phase+1];let p=saved.q.parameters;let mut probes=Vec::with_capacity(3);let mut phase_count=0;let mut integrals=std::array::from_fn::<_,9,_>(|_|Sum::default());
  add_probe(&mut probes,saved,format!("phase{phase}-start.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());
  let targets=cuts(phase);
  if phase==1{
   let mut q=saved.q;q.settings.attempt_limit=1;let snapshot=encode(Saved{q,phase:1});let mut limited=temporal::Engine::restore(q).map_err(|e|format!("limited:{e:?}"))?;
   let failure=limited.advance_to(&mut workspace,targets[0]);if failure.is_ok()||encode(Saved{q:limited.checkpoint(),phase:1})!=snapshot{return Err("attempt rollback".into());}
   writeln!(w,"ROLLBACK,{:?}",failure.err().unwrap()).unwrap();fs::write(dir.join("attempt-rollback.ckp"),snapshot).unwrap();rollbacks+=1;
  }
  for target in targets{
   while engine.checkpoint().elapsed_ticks<target{
    if started.elapsed().as_secs_f64()>1500.{fs::write(dir.join("budget.ckp"),encode(Saved{q:engine.checkpoint(),phase:phase as u32})).unwrap();return Err("1500 s wall budget".into());}
    let old=engine.checkpoint();let a=match engine.advance_to(&mut workspace,target){Ok(a)=>a,Err(e)=>{
     if encode(Saved{q:old,phase:phase as u32})!=encode(Saved{q:engine.checkpoint(),phase:phase as u32}){return Err("rejection mutated state".into());}
     fs::write(dir.join("rejected.ckp"),encode(Saved{q:old,phase:phase as u32})).unwrap();fs::write(dir.join("rejected-target.bin"),target.to_le_bytes()).unwrap();return Err(format!("advance phase={phase} ticks={}:{e:?}",old.elapsed_ticks));}};
    let after=engine.checkpoint();let h=f64::from(a.half_ticks)*temporal::TICK_S;
    writeln!(w,"STEP,{phase},{},{},{},{:.17e},{},{}",old.elapsed_ticks,after.elapsed_ticks,a.half_ticks,a.error_ratio,a.attempts,after.next_full_ticks).unwrap();
    let mut ramp=last_ramp;let reset=a.endpoints.iter().any(|ep|{let next=ep.observations.ramp_v;let crossed=ramp< -2.&&next>= -2.;ramp=next;crossed});
    if reset{add_probe(&mut probes,Saved{q:old,phase:phase as u32},format!("phase{phase}-reset{crossings}.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());}
    if phase_count==0||after.elapsed_ticks==end||reset||after.elapsed_ticks==START+788529152{
     writeln!(w,"SELECT,{phase}").unwrap();selected(&mut w,old.state,&a.coarse,2.*h);selected(&mut w,old.state,&a.endpoints[0].pair,h);selected(&mut w,a.endpoints[0].pair.candidates[1],&a.endpoints[1].pair,h);
    }
    let mut predecessor=old.state;
    for ep in &a.endpoints{
     for(i,weight)in[0.75,0.25].into_iter().enumerate(){let part=joint::parts(p,predecessor,ep.pair.increments[i],h).map_err(|e|format!("ledger:{e:?}"))?;
      for(k,row)in[205,195,139,221,223,225,226,227,228].into_iter().enumerate(){let q=h*weight*part.dc[row];integrals[k].add(q);total[k].add(q);}}
     let o=observations(ep.pair.candidates[1],p)?;write!(w,"OBS,{},{phase}",ep.elapsed_ticks).unwrap();for v in o.into_iter().chain(motor(ep.observations)){write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();
     if last_ramp< -2.&&ep.observations.ramp_v>= -2.{writeln!(w,"RESET,{phase},{last_ticks},{},{last_ramp:.17e},{:.17e}",ep.elapsed_ticks,ep.observations.ramp_v).unwrap();crossings+=1;}
     last_ramp=ep.observations.ramp_v;last_ticks=ep.elapsed_ticks;predecessor=ep.pair.candidates[1];
    }
    for probe in &mut probes{
     let replay=probe.engine.advance_to(&mut workspace,target).map_err(|e|format!("replay:{e:?}"))?;
     if !same_accepted(&a,&replay)||encode(Saved{q:after,phase:phase as u32})!=encode(Saved{q:probe.engine.checkpoint(),phase:phase as u32}){return Err(format!("replay mismatch phase={phase} start={}",probe.start));}
     probe.count+=1;replay_count+=1;
    }
    let mut index=0;while index<probes.len(){if probes[index].count==16{let probe=probes.swap_remove(index);writeln!(replay_log,"REPLAY,{phase},{},{},{}",probe.name,probe.start,probe.count).unwrap();}else{index+=1;}}
    phase_count+=1;accepted_count+=1;
   }
   writeln!(w,"GRID,{phase},{target}").unwrap();write_state(&mut w,engine.checkpoint().state);cps.write_all(&encode(Saved{q:engine.checkpoint(),phase:phase as u32})).unwrap();
   if phase>0&&target==START+REL[phase]+CUT{add_probe(&mut probes,Saved{q:engine.checkpoint(),phase:phase as u32},format!("phase{phase}-inside.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());}
   w.flush().unwrap();cps.flush().unwrap();eprintln!("PROGRESS,phase={phase},ticks={target},accepted={accepted_count}");
  }
  for probe in probes{writeln!(replay_log,"REPLAY,{phase},{},{},{}",probe.name,probe.start,probe.count).unwrap();}
  write!(w,"LEDGER,{phase},{end}").unwrap();for q in &integrals{write!(w,",{:.17e}",q.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,engine.checkpoint().state);
  saved=Saved{q:engine.checkpoint(),phase:phase as u32};
 }
 write!(w,"TOTAL").unwrap();for q in &total{write!(w,",{:.17e}",q.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,engine.checkpoint().state);
 w.flush().unwrap();cps.flush().unwrap();replay_log.flush().unwrap();fs::write(dir.join("final.ckp"),encode(saved)).unwrap();
 eprintln!("COMPLETED,on=1,max={},accepted={accepted_count},restores={restores},replays={replay_count},corruptions=4,rollbacks={rollbacks},crossings={crossings},max_probes={max_probes},wall_s={}",saved.q.settings.maximum_half_ticks,started.elapsed().as_secs_f64());Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
