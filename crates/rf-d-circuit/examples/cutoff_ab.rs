//! Counterfactual open branch from the exact pre-cutoff state; 8 ms.
//! No audio-thread admission. See docs/VOZ_CUTOFF_AB_PROTOCOLO.md.
use rf_d_circuit::{assembly_decay_voice as joint,assembly_decay_engine as temporal};
use std::{fs,io::Write,time::Instant};
fn nominal(alpha:f64)->rf_d_circuit::conditioned_voice::Parameters{
 let original=rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution:rf_d_circuit::conditioned_recipe::Resolution::Half2Us}.parameters();
 let mut chain=original.chain();chain.boundary.panel.cutoff_fraction_from_neg10=alpha;
 rf_d_circuit::conditioned_voice::Parameters::new(original.controls,chain,[false;4],[0.5;4],original.sources).expect("declared cutoff recipe")
}
fn scene(alpha:f64)->joint::Parameters{joint::Parameters::from_nominal(nominal(alpha))}
fn write_state(w:&mut impl Write,s:joint::State) {write!(w,"JOINT_STATE").unwrap();for v in s.high.into_iter().chain(s.low) {write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();}
fn same(a:&joint::Pair,b:&joint::Pair)->bool {
 a.residual_ratio.to_bits()==b.residual_ratio.to_bits()&&a.correction_ratio.to_bits()==b.correction_ratio.to_bits()&&a.iterations==b.iterations&&a.trials==b.trials&&a.candidates.iter().chain(a.increments.iter()).zip(b.candidates.iter().chain(b.increments.iter())).all(|(x,y)|x.high.iter().chain(x.low.iter()).zip(y.high.iter().chain(y.low.iter())).all(|(u,v)|u.to_bits()==v.to_bits()))
}
// All IO and replay storage belong to the laboratory caller.
const START:u64=82024857600;const REL:[u64;2]=[0,4194304000];const CUT:u64=419430400;const SIZE:usize=3736;const DECAY:f64=1000.;
const KEY:[f64;1]=[0.];const SHORT:[bool;1]=[false];const ALPHA:[f64;1]=[1.];
#[derive(Clone,Copy)]struct Saved{q:temporal::Checkpoint,phase:u32}
fn encode(s:Saved)->[u8;SIZE]{
 let q=s.q;let mut b=[0;SIZE];b[..8].copy_from_slice(b"RFCTF001");b[8..16].copy_from_slice(&q.elapsed_ticks.to_le_bytes());for(k,v)in[q.settings.maximum_half_ticks,q.settings.attempt_limit,q.next_full_ticks,s.phase,1,(q.parameters.final_decay as u32)|((q.parameters.short as u32)<<1)].into_iter().enumerate(){b[16+4*k..20+4*k].copy_from_slice(&v.to_le_bytes());}b[40..48].copy_from_slice(&q.parameters.keyboard.to_le_bytes());b[56..64].copy_from_slice(&q.parameters.decay_ohm.to_le_bytes());b[64..72].copy_from_slice(&q.parameters.chain().boundary.panel.cutoff_fraction_from_neg10.to_le_bytes());for(k,v)in q.state.high.into_iter().chain(q.state.low).enumerate(){b[72+8*k..80+8*k].copy_from_slice(&v.to_le_bytes());}b
}
fn decode(b:&[u8])->Result<Saved,String>{
 if b.len()!=SIZE||&b[..8]!=b"RFCTF001"||b[48..56]!=[0;8]{return Err("checkpoint format".into());}let u=|k:usize|u32::from_le_bytes(b[k..k+4].try_into().unwrap());let ticks=u64::from_le_bytes(b[8..16].try_into().unwrap());let max=u(16);let limit=u(20);let next=u(24);let phase=u(28);let flags=u(36);let key=f64::from_le_bytes(b[40..48].try_into().unwrap());
 if phase>=1||u(32)!=1||!matches!(flags,1|3)||![1048576,524288].contains(&max)||!(1..=20).contains(&limit)||ticks<START+REL[phase as usize]||ticks>START+REL[phase as usize+1]||ticks%8!=0||next<8||!next.is_power_of_two()||next>2*max||key.to_bits()!=KEY[phase as usize].to_bits()||((flags&2)!=0)!=SHORT[phase as usize]{return Err("checkpoint recipe".into());}
 let f=|k:usize|f64::from_le_bytes(b[72+8*k..80+8*k].try_into().unwrap());let state=joint::State{high:std::array::from_fn(f),low:std::array::from_fn(|k|f(k+229))};for k in 0..229{let(a,b)=(state.high[k],state.low[k]);let s=a+b;let v=s-a;let e=(a-(s-v))+(b-v);if !a.is_finite()||!b.is_finite()||s.to_bits()!=a.to_bits()||e.to_bits()!=b.to_bits(){return Err("checkpoint state".into());}}
 let alpha=f64::from_le_bytes(b[64..72].try_into().unwrap());if alpha.to_bits()!=ALPHA[phase as usize].to_bits(){return Err("cutoff recipe".into());}let mut p=scene(alpha);p.decay_ohm=f64::from_le_bytes(b[56..64].try_into().unwrap());if !joint::Parameters::valid_decay(p.decay_ohm){return Err("decay resistance".into());}p.keyboard=key;p.short=(flags&2)!=0;p.final_decay=(flags&1)!=0;let q=temporal::Checkpoint{state,parameters:p,settings:temporal::Settings{maximum_half_ticks:max,attempt_limit:limit},elapsed_ticks:ticks,next_full_ticks:next};temporal::Engine::restore(q).map_err(|e|format!("checkpoint engine:{e:?}"))?;Ok(Saved{q,phase})
}
fn observations(s:joint::State,p:joint::Parameters)->Result<[f64;13],String>{
 let v=|i|s.high[i]+s.low[i];let t=joint::contour_closed_driver::linearize(std::array::from_fn(|k|v(if k<29{200+k}else{165})),p.keyboard,p.final_decay,p.short,p.decay_ohm).map_err(|e|format!("observe:{e:?}"))?;Ok([v(205),v(203),v(194),v(221),v(217),v(223)-v(225),v(225),v(226),v(227),v(228),t.ports[4],t.ports[1],(v(203)-v(165))/68000.])
}
fn motor(o:temporal::Observations)->[f64;9]{[o.saw_v,o.ramp_v,o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.series_current_a,o.c27_current_a,o.bus_kcl_a]}
fn same_accepted(a:&temporal::Accepted,b:&temporal::Accepted)->bool{
 a.half_ticks==b.half_ticks&&a.attempts==b.attempts&&a.error_ratio.to_bits()==b.error_ratio.to_bits()&&same(&a.coarse,&b.coarse)&&a.endpoints.iter().zip(&b.endpoints).all(|(a,b)|a.elapsed_ticks==b.elapsed_ticks&&same(&a.pair,&b.pair)&&motor(a.observations).map(f64::to_bits)==motor(b.observations).map(f64::to_bits))
}
#[derive(Default)]struct Sum{value:f64,low:f64}impl Sum{fn add(&mut self,v:f64){let y=v-self.low;let t=self.value+y;self.low=(t-self.value)-y;self.value=t;}}
fn selected(w:&mut impl Write,old:joint::State,pair:&joint::Pair,h:f64){writeln!(w,"JOINT_ROOT,0,{h:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio).unwrap();for s in[old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]]{write_state(w,s);}}

use rf_d_circuit::{block_decay_voice as legacy_joint,block_decay_engine as legacy_temporal};
fn new_blob(a:&temporal::Accepted,q:temporal::Checkpoint)->Vec<u8>{
 let mut b=Vec::new();for p in [&a.coarse,&a.endpoints[0].pair,&a.endpoints[1].pair]{
  for s in p.candidates.iter().chain(p.increments.iter()){for v in s.high.iter().chain(s.low.iter()){b.extend_from_slice(&v.to_le_bytes());}}
  for v in [p.residual_ratio,p.correction_ratio]{b.extend_from_slice(&v.to_le_bytes());}for v in [p.iterations,p.trials]{b.extend_from_slice(&(v as u64).to_le_bytes());}
 }
 for ep in &a.endpoints{b.extend_from_slice(&ep.elapsed_ticks.to_le_bytes());let o=ep.observations;for v in [o.saw_v,o.ramp_v,o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.series_current_a,o.c27_current_a,o.bus_kcl_a]{b.extend_from_slice(&v.to_le_bytes());}}
 b.extend_from_slice(&a.half_ticks.to_le_bytes());b.extend_from_slice(&a.error_ratio.to_le_bytes());b.extend_from_slice(&a.attempts.to_le_bytes());
 for v in q.state.high.iter().chain(q.state.low.iter()){b.extend_from_slice(&v.to_le_bytes());}b.extend_from_slice(&q.elapsed_ticks.to_le_bytes());for v in [q.settings.maximum_half_ticks,q.settings.attempt_limit,q.next_full_ticks]{b.extend_from_slice(&v.to_le_bytes());}
 b.extend_from_slice(&q.parameters.keyboard.to_le_bytes());b.push(q.parameters.final_decay as u8);b.push(q.parameters.short as u8);b
}
fn old_blob(a:&legacy_temporal::Accepted,q:legacy_temporal::Checkpoint)->Vec<u8>{
 let mut b=Vec::new();for p in [&a.coarse,&a.endpoints[0].pair,&a.endpoints[1].pair]{
  for s in p.candidates.iter().chain(p.increments.iter()){for v in s.high.iter().chain(s.low.iter()){b.extend_from_slice(&v.to_le_bytes());}}
  for v in [p.residual_ratio,p.correction_ratio]{b.extend_from_slice(&v.to_le_bytes());}for v in [p.iterations,p.trials]{b.extend_from_slice(&(v as u64).to_le_bytes());}
 }
 for ep in &a.endpoints{b.extend_from_slice(&ep.elapsed_ticks.to_le_bytes());let o=ep.observations;for v in [o.saw_v,o.ramp_v,o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.series_current_a,o.c27_current_a,o.bus_kcl_a]{b.extend_from_slice(&v.to_le_bytes());}}
 b.extend_from_slice(&a.half_ticks.to_le_bytes());b.extend_from_slice(&a.error_ratio.to_le_bytes());b.extend_from_slice(&a.attempts.to_le_bytes());
 for v in q.state.high.iter().chain(q.state.low.iter()){b.extend_from_slice(&v.to_le_bytes());}b.extend_from_slice(&q.elapsed_ticks.to_le_bytes());for v in [q.settings.maximum_half_ticks,q.settings.attempt_limit,q.next_full_ticks]{b.extend_from_slice(&v.to_le_bytes());}
 b.extend_from_slice(&q.parameters.keyboard.to_le_bytes());b.push(q.parameters.final_decay as u8);b.push(q.parameters.short as u8);b
}
fn flux(s:joint::State,slope:f64)->[f64;7]{
 let v=|k|s.high[k]+s.low[k];
 [v(205),slope,(v(208)-v(205))/10000.,(v(211)-v(205))/DECAY,(v(205)-v(200))/10000.,v(226)-v(228),v(218)]
}
#[inline(never)]
fn initial_flux(p:joint::Parameters,s:joint::State)->Result<[f64;7],String>{
 let part=joint::parts(p,s,joint::State::from_nodes([0.;229]),joint::MIN_DT_S).map_err(|e|format!("incoming flux:{e:?}"))?;
 Ok(flux(s,-part.dc[205]/1e-5))
}
fn endpoint_flux(ep:&temporal::Endpoint,h:f64)->[f64;7]{
 let d=|i:usize|ep.pair.increments[i].high[205]+ep.pair.increments[i].low[205];
 flux(ep.pair.candidates[1],(-4.5*d(0)+2.5*d(1))/h)
}
fn write_flux(w:&mut impl Write,tick:u64,x:[f64;7])->Result<(),String>{
 if x.iter().any(|v|!v.is_finite()){return Err("nonfinite flux".into());}
 w.write_all(&tick.to_le_bytes()).map_err(|e|e.to_string())?;
 for v in x{w.write_all(&v.to_le_bytes()).map_err(|e|e.to_string())?;}Ok(())
}
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
 let end=START+REL[phase+1];
 let mut out=Vec::new();let mut cut=START+REL[phase]+CUT;
 while cut<end{out.push(cut);cut+=CUT;}out.push(end);out
}
fn compare_previous(q:temporal::Checkpoint,dir:&std::path::Path,name:&str,target:u64)->Result<(),String>{
 // Compare four complete advances with the admitted original assembly at the seam.
 let mut p=legacy_joint::Parameters::from_nominal(nominal(q.parameters.chain().boundary.panel.cutoff_fraction_from_neg10));p.decay_ohm=q.parameters.decay_ohm;p.keyboard=q.parameters.keyboard;p.short=q.parameters.short;
 let oq=legacy_temporal::Checkpoint{state:legacy_joint::State{high:q.state.high,low:q.state.low},parameters:p,settings:legacy_temporal::Settings{maximum_half_ticks:q.settings.maximum_half_ticks,attempt_limit:q.settings.attempt_limit},elapsed_ticks:q.elapsed_ticks,next_full_ticks:q.next_full_ticks};
 let mut old=legacy_temporal::Engine::restore(oq).map_err(|e|format!("legacy:{e:?}"))?;let mut ow=legacy_joint::Workspace::new();let mut new=temporal::Engine::restore(q).map_err(|e|format!("optimized:{e:?}"))?;let mut nw=joint::Workspace::new();let mut old_bits=Vec::new();let mut new_bits=Vec::new();
 for _ in 0..4{let a=old.advance_to(&mut ow,target).map_err(|e|format!("legacy step:{e:?}"))?;let b=new.advance_to(&mut nw,target).map_err(|e|format!("optimized step:{e:?}"))?;old_bits.extend(old_blob(&a,old.checkpoint()));new_bits.extend(new_blob(&b,new.checkpoint()));}
 if old_bits!=new_bits{return Err("seam full accepted bits".into());}fs::write(dir.join(format!("{name}-old.bin")),old_bits).unwrap();fs::write(dir.join(format!("{name}-new.bin")),new_bits).unwrap();
 Ok(())
}
fn run()->Result<(),String>{
 let args:Vec<_>=std::env::args().collect();if args.len()!=3{return Err("usage: cutoff_ab <cutoff-event1-before.ckp> <new-output-directory>".into());}
 let raw=fs::read(&args[1]).map_err(|e|e.to_string())?;
 let restored=decode(&raw)?;
 if restored.q.elapsed_ticks!=START||restored.q.parameters.decay_ohm.to_bits()!=DECAY.to_bits()||encode(restored).as_slice()!=raw.as_slice(){return Err("own final source recipe/bytes".into());}
 let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).map_err(|e|e.to_string())?;fs::write(dir.join("incoming-original.ckp"),&raw).map_err(|e|e.to_string())?;
 compare_previous(restored.q,dir,"seam",START+REL[1])?;
 let mut engine=temporal::Engine::restore(restored.q).map_err(|e|format!("own restore:{e:?}"))?;let mut saved=restored;let bytes=encode(saved);let mut workspace=joint::Workspace::new();
 for kind in 0..4{let mut b=bytes;match kind{0=>b[0]^=1,1=>b[72+8*225..80+8*225].copy_from_slice(&f64::NAN.to_le_bytes()),2=>b[28..32].copy_from_slice(&9_u32.to_le_bytes()),_=>b[24..28].copy_from_slice(&3_u32.to_le_bytes())}if decode(&b).is_ok(){return Err("corruption accepted".into());}}
 if engine.advance_to(&mut workspace,START).is_ok()||encode(Saved{q:engine.checkpoint(),phase:0})!=bytes{return Err("invalid destination rollback".into());}
 let mut w=std::io::BufWriter::new(fs::File::create(dir.join("selected.txt")).map_err(|e|e.to_string())?);
 let mut cps=fs::File::create(dir.join("checkpoints.bin")).map_err(|e|e.to_string())?;
 let mut replay_log=std::io::BufWriter::new(fs::File::create(dir.join("replays.txt")).map_err(|e|e.to_string())?);
 writeln!(w,"PROFILE,1,{}",saved.q.settings.maximum_half_ticks).unwrap();write_state(&mut w,saved.q.state);cps.write_all(&bytes).unwrap();
 let mut flux_file=std::io::BufWriter::new(fs::File::create(dir.join("flux.bin")).map_err(|e|e.to_string())?);flux_file.write_all(b"RFRELFX1").unwrap();
 let mut event_file=std::io::BufWriter::new(fs::File::create(dir.join("transitions.txt")).map_err(|e|e.to_string())?);
 let initial=initial_flux(saved.q.parameters,saved.q.state)?;write_flux(&mut flux_file,START,initial)?;
 let(mut last_slope,mut last_latch,mut last_c2,mut transition_count)=(initial[1],initial[5],initial[0],0);
 let started=Instant::now();let mut last_ramp=saved.q.state.high[43]+saved.q.state.low[43];let mut last_ticks=START;
 let mut total=std::array::from_fn::<_,9,_>(|_|Sum::default());let(mut accepted_count,mut replay_count,mut restores,mut rollbacks,mut crossings,mut max_probes)=(0,0,0,1,0,0);
 for phase in 0..1{
  let incoming=encode(saved);let mut q=engine.checkpoint();let mut p=scene(ALPHA[phase]);p.keyboard=q.parameters.keyboard;p.short=q.parameters.short;p.decay_ohm=q.parameters.decay_ohm;q.parameters=p;engine=temporal::Engine::restore(q).map_err(|e|format!("cutoff event:{e:?}"))?;
  saved=Saved{q:engine.checkpoint(),phase:phase as u32};let changed=encode(saved);if incoming[72..]!=changed[72..]||incoming[56..64]!=changed[56..64]||incoming[8..28]!=changed[8..28]||incoming[32..56]!=changed[32..56]{return Err("source changed accepted charges".into());}
  writeln!(w,"BOUNDARY,{phase},{},{:.17e},{}",saved.q.elapsed_ticks,KEY[phase],SHORT[phase] as u32).unwrap();write_state(&mut w,saved.q.state);cps.write_all(&changed).unwrap();
  if phase>0{fs::write(dir.join(format!("event{phase}-before.ckp")),incoming).unwrap();fs::write(dir.join(format!("event{phase}-after.ckp")),changed).unwrap();compare_previous(saved.q,dir,&format!("event{phase}"),START+REL[phase+1])?;}
  let end=START+REL[phase+1];let p=saved.q.parameters;let mut probes=Vec::with_capacity(3);let mut phase_count=0;let mut integrals=std::array::from_fn::<_,9,_>(|_|Sum::default());
  add_probe(&mut probes,saved,format!("phase{phase}-start.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());
  let targets=cuts(phase);
  let first_target=targets[0];for target in targets{
   while engine.checkpoint().elapsed_ticks<target{
    if started.elapsed().as_secs_f64()>1800.{fs::write(dir.join("budget.ckp"),encode(Saved{q:engine.checkpoint(),phase:phase as u32})).unwrap();return Err("1800 s wall budget".into());}
    let old=engine.checkpoint();let a=match engine.advance_to(&mut workspace,target){Ok(a)=>a,Err(e)=>{
     if encode(Saved{q:old,phase:phase as u32})!=encode(Saved{q:engine.checkpoint(),phase:phase as u32}){return Err("rejection mutated state".into());}
     fs::write(dir.join("rejected.ckp"),encode(Saved{q:old,phase:phase as u32})).unwrap();fs::write(dir.join("rejected-target.bin"),target.to_le_bytes()).unwrap();return Err(format!("advance phase={phase} ticks={}:{e:?}",old.elapsed_ticks));}};
    let after=engine.checkpoint();let h=f64::from(a.half_ticks)*temporal::TICK_S;
    writeln!(w,"STEP,{phase},{},{},{},{:.17e},{},{}",old.elapsed_ticks,after.elapsed_ticks,a.half_ticks,a.error_ratio,a.attempts,after.next_full_ticks).unwrap();
    let mut ramp=last_ramp;let reset=a.endpoints.iter().any(|ep|{let next=ep.observations.ramp_v;let crossed=ramp< -2.&&next>= -2.;ramp=next;crossed});
    let values=[endpoint_flux(&a.endpoints[0],h),endpoint_flux(&a.endpoints[1],h)];
    let(mut slope,mut latch)=(last_slope,last_latch);let(mut turn,mut flip)=(false,false);
    for x in values{turn|=slope>0.&&x[1]<=0.;flip|=(latch<0.&&x[5]>=0.)||(latch>=0.&&x[5]<0.);slope=x[1];latch=x[5];}
    if (turn||flip)&&!reset{add_probe(&mut probes,Saved{q:old,phase:phase as u32},format!("phase{phase}-transition{transition_count}.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());transition_count+=1;}
    if reset{add_probe(&mut probes,Saved{q:old,phase:phase as u32},format!("phase{phase}-reset{crossings}.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());}
    if phase_count==0||after.elapsed_ticks==end||reset||turn||flip{
     writeln!(w,"SELECT,{phase}").unwrap();selected(&mut w,old.state,&a.coarse,2.*h);selected(&mut w,old.state,&a.endpoints[0].pair,h);selected(&mut w,a.endpoints[0].pair.candidates[1],&a.endpoints[1].pair,h);
    }
    let mut predecessor=old.state;
    for (ep,x) in a.endpoints.iter().zip(values){
     for(i,weight)in[0.75,0.25].into_iter().enumerate(){let part=joint::parts(p,predecessor,ep.pair.increments[i],h).map_err(|e|format!("ledger:{e:?}"))?;
      for(k,row)in[205,195,139,221,223,225,226,227,228].into_iter().enumerate(){let q=h*weight*part.dc[row];integrals[k].add(q);total[k].add(q);}}
     let o=observations(ep.pair.candidates[1],p)?;write!(w,"OBS,{},{phase}",ep.elapsed_ticks).unwrap();for v in o.into_iter().chain(motor(ep.observations)){write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();
     if last_ramp< -2.&&ep.observations.ramp_v>= -2.{writeln!(w,"RESET,{phase},{last_ticks},{},{last_ramp:.17e},{:.17e}",ep.elapsed_ticks,ep.observations.ramp_v).unwrap();crossings+=1;}
     write_flux(&mut flux_file,ep.elapsed_ticks,x)?;
     if last_slope>0.&&x[1]<=0.{writeln!(event_file,"TURN,{last_ticks},{},{last_slope:.17e},{:.17e},{last_c2:.17e},{:.17e}",ep.elapsed_ticks,x[1],x[0]).unwrap();}
     if (last_latch<0.&&x[5]>=0.)||(last_latch>=0.&&x[5]<0.){writeln!(event_file,"LATCH,{last_ticks},{},{last_latch:.17e},{:.17e},{last_c2:.17e},{:.17e}",ep.elapsed_ticks,x[5],x[0]).unwrap();}
     last_slope=x[1];last_latch=x[5];last_c2=x[0];
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
   if target==first_target{add_probe(&mut probes,Saved{q:engine.checkpoint(),phase:phase as u32},format!("phase{phase}-inside.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());}
   w.flush().unwrap();cps.flush().unwrap();eprintln!("PROGRESS,phase={phase},ticks={target},accepted={accepted_count}");
  }
  for probe in probes{writeln!(replay_log,"REPLAY,{phase},{},{},{}",probe.name,probe.start,probe.count).unwrap();}
  write!(w,"LEDGER,{phase},{end}").unwrap();for q in &integrals{write!(w,",{:.17e}",q.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,engine.checkpoint().state);
  saved=Saved{q:engine.checkpoint(),phase:phase as u32};
 }
 write!(w,"TOTAL").unwrap();for q in &total{write!(w,",{:.17e}",q.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,engine.checkpoint().state);
 flux_file.flush().unwrap();event_file.flush().unwrap();w.flush().unwrap();cps.flush().unwrap();replay_log.flush().unwrap();fs::write(dir.join("final.ckp"),encode(saved)).unwrap();
 eprintln!("COMPLETED,on=1,max={},accepted={accepted_count},restores={restores},replays={replay_count},corruptions=4,rollbacks={rollbacks},crossings={crossings},max_probes={max_probes},wall_s={}",saved.q.settings.maximum_half_ticks,started.elapsed().as_secs_f64());Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
