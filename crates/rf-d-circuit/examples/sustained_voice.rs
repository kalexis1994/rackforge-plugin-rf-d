//! ON diagnostic: 4 us rest, 8 ms gate, 4 ms release; own public histories.
//! No audio-thread admission. See docs/VOZ_SOSTENIDA_PROTOCOLO.md.
use rf_d_circuit::{conditioned_voice as joint,conditioned_engine as temporal};
use std::{fs,io::Write,time::Instant};
fn scene()->joint::Parameters{
 rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution:rf_d_circuit::conditioned_recipe::Resolution::Half2Us}.parameters()
}
fn write_state(w:&mut impl Write,s:joint::State) {write!(w,"JOINT_STATE").unwrap();for v in s.high.into_iter().chain(s.low) {write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();}
fn same(a:&joint::Pair,b:&joint::Pair)->bool {
 a.residual_ratio.to_bits()==b.residual_ratio.to_bits()&&a.correction_ratio.to_bits()==b.correction_ratio.to_bits()&&a.iterations==b.iterations&&a.trials==b.trials&&a.candidates.iter().chain(a.increments.iter()).zip(b.candidates.iter().chain(b.increments.iter())).all(|(x,y)|x.high.iter().chain(x.low.iter()).zip(y.high.iter().chain(y.low.iter())).all(|(u,v)|u.to_bits()==v.to_bits()))
}
// All IO and replay storage belong to the laboratory caller.
const START:u64=4423942144;const REL:[u64;4]=[0,2097152,4196401152,6293553152];const CUT:u64=157286400;const SIZE:usize=3720;
const KEY:[f64;3]=[0.,10.,0.];const SHORT:[bool;3]=[false,true,false];
#[derive(Clone,Copy)]struct Saved{q:temporal::Checkpoint,phase:u32}
fn encode(s:Saved)->[u8;SIZE]{
 let q=s.q;let mut b=[0;SIZE];b[..8].copy_from_slice(b"RFHLD001");b[8..16].copy_from_slice(&q.elapsed_ticks.to_le_bytes());for(k,v)in[q.settings.maximum_half_ticks,q.settings.attempt_limit,q.next_full_ticks,s.phase,1,(q.parameters.final_decay as u32)|((q.parameters.short as u32)<<1)].into_iter().enumerate(){b[16+4*k..20+4*k].copy_from_slice(&v.to_le_bytes());}b[40..48].copy_from_slice(&q.parameters.keyboard.to_le_bytes());for(k,v)in q.state.high.into_iter().chain(q.state.low).enumerate(){b[56+8*k..64+8*k].copy_from_slice(&v.to_le_bytes());}b
}
fn decode(b:&[u8])->Result<Saved,String>{
 if b.len()!=SIZE||&b[..8]!=b"RFHLD001"||b[48..56]!=[0;8]{return Err("checkpoint format".into());}let u=|k:usize|u32::from_le_bytes(b[k..k+4].try_into().unwrap());let ticks=u64::from_le_bytes(b[8..16].try_into().unwrap());let max=u(16);let limit=u(20);let next=u(24);let phase=u(28);let flags=u(36);let key=f64::from_le_bytes(b[40..48].try_into().unwrap());
 if phase>=3||u(32)!=1||flags>3||![1048576,524288].contains(&max)||!(1..=20).contains(&limit)||ticks<START+REL[phase as usize]||ticks>START+REL[phase as usize+1]||ticks%8!=0||next<8||!next.is_power_of_two()||next>2*max||key.to_bits()!=KEY[phase as usize].to_bits()||((flags&2)!=0)!=SHORT[phase as usize]{return Err("checkpoint recipe".into());}
 let f=|k:usize|f64::from_le_bytes(b[56+8*k..64+8*k].try_into().unwrap());let state=joint::State{high:std::array::from_fn(f),low:std::array::from_fn(|k|f(k+229))};for k in 0..229{let(a,b)=(state.high[k],state.low[k]);let s=a+b;let v=s-a;let e=(a-(s-v))+(b-v);if !a.is_finite()||!b.is_finite()||s.to_bits()!=a.to_bits()||e.to_bits()!=b.to_bits(){return Err("checkpoint state".into());}}
 let mut p=scene();p.keyboard=key;p.short=(flags&2)!=0;p.final_decay=(flags&1)!=0;let q=temporal::Checkpoint{state,parameters:p,settings:temporal::Settings{maximum_half_ticks:max,attempt_limit:limit},elapsed_ticks:ticks,next_full_ticks:next};temporal::Engine::restore(q).map_err(|e|format!("checkpoint engine:{e:?}"))?;Ok(Saved{q,phase})
}
fn observations(s:joint::State,p:joint::Parameters)->Result<[f64;13],String>{
 let v=|i|s.high[i]+s.low[i];let t=joint::contour_closed_driver::linearize(std::array::from_fn(|k|v(if k<29{200+k}else{165})),p.keyboard,p.final_decay,p.short).map_err(|e|format!("observe:{e:?}"))?;Ok([v(205),v(203),v(194),v(221),v(217),v(223)-v(225),v(225),v(226),v(227),v(228),t.ports[4],t.ports[1],(v(203)-v(165))/68000.])
}
fn motor(o:temporal::Observations)->[f64;9]{[o.saw_v,o.ramp_v,o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.series_current_a,o.c27_current_a,o.bus_kcl_a]}
fn same_accepted(a:&temporal::Accepted,b:&temporal::Accepted)->bool{
 a.half_ticks==b.half_ticks&&a.attempts==b.attempts&&a.error_ratio.to_bits()==b.error_ratio.to_bits()&&same(&a.coarse,&b.coarse)&&a.endpoints.iter().zip(&b.endpoints).all(|(a,b)|a.elapsed_ticks==b.elapsed_ticks&&same(&a.pair,&b.pair)&&motor(a.observations).map(f64::to_bits)==motor(b.observations).map(f64::to_bits))
}
#[derive(Default)]struct Sum{value:f64,low:f64}impl Sum{fn add(&mut self,v:f64){let y=v-self.low;let t=self.value+y;self.low=(t-self.value)-y;self.value=t;}}
fn selected(w:&mut impl Write,old:joint::State,pair:&joint::Pair,h:f64){writeln!(w,"JOINT_ROOT,0,{h:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio).unwrap();for s in[old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]]{write_state(w,s);}}
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
