//! Laboratory IO adapter; the inherited engine remains free of IO/heap work.
use rf_d_circuit::{joint_engine::{self as temporal,Engine,Settings,Checkpoint,Accepted},joint_voice as joint,joint_currents,chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,vco1_startup,vco1_stamp::Controls};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use std::{fs::{self,File},io::{Write,BufWriter},path::Path,time::Instant};
const ANCHOR:u64=131072000;const GOAL:u64=5373952000;
const CHECK_BYTES:usize=3224;
fn scene()->Result<(joint::Parameters,joint::State),String> {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let p=Chain {circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
 let controls=Controls::default();let v=vco1_startup::startup(controls).map_err(|e|format!("startup:{e:?}"))?.nodes;
 let row:Vec<f64>=include_str!("../evidence/voice_chain_charge_vectors06.txt").lines().next().unwrap().split_whitespace().map(|x|x.parse().unwrap()).collect();
 let c=chain_charge::State::from_nodes(row[8..76].try_into().unwrap());
 Ok((joint::Parameters::new(controls,p,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap(),joint::State::lift(v,[0.;134],c)))
}
fn encode(q:Checkpoint)->[u8;CHECK_BYTES] {
 let mut bytes=[0;CHECK_BYTES];bytes[..8].copy_from_slice(&q.elapsed_ticks.to_le_bytes());
 for(i,v) in [q.next_full_ticks,q.settings.maximum_half_ticks,q.settings.attempt_limit,0].into_iter().enumerate() {bytes[8+4*i..12+4*i].copy_from_slice(&v.to_le_bytes());}
 for (k,v) in q.state.high.into_iter().chain(q.state.low).enumerate() {bytes[24+8*k..32+8*k].copy_from_slice(&v.to_le_bytes());}bytes
}
fn decode(bytes:&[u8],p:joint::Parameters)->Result<Checkpoint,String> {
 if bytes.len()!=CHECK_BYTES||bytes[20..24]!=[0;4] {return Err("checkpoint format".into());}
 let u=|k|u32::from_le_bytes(bytes[k..k+4].try_into().unwrap());let f=|k|f64::from_le_bytes(bytes[24+8*k..32+8*k].try_into().unwrap());
 Ok(Checkpoint{state:joint::State{high:std::array::from_fn(f),low:std::array::from_fn(|k|f(k+200))},parameters:p,settings:Settings{maximum_half_ticks:u(12),attempt_limit:u(16)},elapsed_ticks:u64::from_le_bytes(bytes[..8].try_into().unwrap()),next_full_ticks:u(8)})
}
fn selected(w:&mut impl Write,old:joint::State,a:&Accepted)->Result<(),String> {
 let h=f64::from(a.half_ticks)*temporal::TICK_S;
 for (dt,s,pair) in [(2.*h,old,&a.coarse),(h,old,&a.endpoints[0].pair),(h,a.endpoints[0].pair.candidates[1],&a.endpoints[1].pair)] {
  writeln!(w,"JOINT_ROOT,0,{dt:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio).map_err(|e|e.to_string())?;
  for x in [s,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]] {
   write!(w,"JOINT_STATE").map_err(|e|e.to_string())?;for v in x.high.into_iter().chain(x.low) {write!(w,",{v:.17e}").map_err(|e|e.to_string())?;}writeln!(w).map_err(|e|e.to_string())?;
  }
 }Ok(())
}
#[derive(Default)] struct Sum {value:f64,low:f64}
impl Sum {fn add(&mut self,v:f64) {let y=v-self.low;let t=self.value+y;self.low=(t-self.value)-y;self.value=t;}}
fn same(a:&Accepted,b:&Accepted)->bool {
 a.error_ratio==b.error_ratio&&a.half_ticks==b.half_ticks&&a.attempts==b.attempts&&a.coarse.candidates==b.coarse.candidates&&a.coarse.increments==b.coarse.increments&&(0..2).all(|i|a.endpoints[i].elapsed_ticks==b.endpoints[i].elapsed_ticks&&a.endpoints[i].pair.candidates==b.endpoints[i].pair.candidates&&a.endpoints[i].pair.increments==b.endpoints[i].pair.increments&&a.endpoints[i].observations==b.endpoints[i].observations)
}
fn state_bits(a:joint::State,b:joint::State)->bool {
 a.high.into_iter().chain(a.low).zip(b.high.into_iter().chain(b.low)).all(|(x,y)|x.to_bits()==y.to_bits())
}
fn same_bits(a:&Accepted,b:&Accepted)->bool {
 let pairs=[(&a.coarse,&b.coarse),(&a.endpoints[0].pair,&b.endpoints[0].pair),(&a.endpoints[1].pair,&b.endpoints[1].pair)];
 a.error_ratio.to_bits()==b.error_ratio.to_bits()&&pairs.into_iter().all(|(x,y)|x.residual_ratio.to_bits()==y.residual_ratio.to_bits()&&x.correction_ratio.to_bits()==y.correction_ratio.to_bits()&&(0..2).all(|k|state_bits(x.candidates[k],y.candidates[k])&&state_bits(x.increments[k],y.increments[k])))
}
fn run(maximum:u32,out:&Path,limit:usize,restore:&Path)->Result<(),String> {
 let(p,_)=scene()?;let q=decode(&fs::read(restore).map_err(|e|e.to_string())?,p)?;if q.settings.maximum_half_ticks!=maximum||q.elapsed_ticks!=0 {return Err("conditioned charge seed metadata".into());}let mut engine=Engine::restore(q).map_err(|e|format!("init:{e:?}"))?;let initial=engine.checkpoint().state;
 let mut trace=BufWriter::new(File::create(out.join("trace.bin")).map_err(|e|e.to_string())?);trace.write_all(b"RFJTRC01").map_err(|e|e.to_string())?;
 let mut checks=BufWriter::new(File::create(out.join("checkpoints.bin")).map_err(|e|e.to_string())?);checks.write_all(b"RFJCKP01").map_err(|e|e.to_string())?;checks.write_all(&encode(engine.checkpoint())).map_err(|e|e.to_string())?;
 let mut roots=BufWriter::new(File::create(out.join("selected.txt")).map_err(|e|e.to_string())?);
 let mut events=BufWriter::new(File::create(out.join("events.txt")).map_err(|e|e.to_string())?);writeln!(events,"RFJEVENT01").map_err(|e|e.to_string())?;let mut steps=0;let mut crossings=0;let mut restores=0;let mut max_lte=0_f64;let mut max_bus=0_f64;let mut max_c1=0_f64;let mut charge=Sum::default();let mut absolute=Sum::default();let mut means:[Sum;5]=std::array::from_fn(|_|Sum::default());let started=Instant::now();let mut last_ramp=initial.high[43]+initial.low[43];
 let result=(|| {
  while engine.checkpoint().elapsed_ticks<GOAL {
   let before=engine.checkpoint();let target=if before.elapsed_ticks<1048576 {1048576} else {((before.elapsed_ticks/ANCHOR+1)*ANCHOR).min(GOAL)};
   if steps>=limit||started.elapsed().as_secs_f64()>7200.||out.parent().unwrap().join("stop.flag").exists() {return Err("ADMINISTRATIVE_BUDGET".to_string());}
   let echo=if before.elapsed_ticks==ANCHOR||before.elapsed_ticks==9*ANCHOR||before.elapsed_ticks==29*ANCHOR {Some(Engine::restore(decode(&encode(before),p)?).map_err(|e|format!("restore:{e:?}"))?.advance_to(target).map_err(|e|format!("echo:{e:?}"))?)} else {None};
   let accepted=engine.advance_to(target).map_err(|e|format!("ENGINE_REJECT,{e:?}"))?;
   if let Some(echo)=echo {if !same(&accepted,&echo)||!same_bits(&accepted,&echo) {return Err("restore mismatch".into());}restores+=1;}
   steps+=1;max_lte=max_lte.max(accepted.error_ratio);let mut old=before.state;let h=f64::from(accepted.half_ticks)*temporal::TICK_S;let mut event=false;
   for e in &accepted.endpoints {
    let cur=joint_currents::stages(&e.pair,old,h).map_err(|e|format!("currents:{e:?}"))?;let d=&e.pair.increments;
    let c1=1e-8/h*(joint::B[1][0]*(d[0].high[43]+d[0].low[43])+joint::B[1][1]*(d[1].high[43]+d[1].low[43]));let c1_kcl=c1+cur[1].iter().sum::<f64>();
    for (i,weight) in [0.75,0.25].into_iter().enumerate() {charge.add(h*weight*cur[i].iter().sum::<f64>());absolute.add(h*weight*cur[i].iter().map(|v|v.abs()).sum::<f64>());}
    max_bus=max_bus.max(e.observations.bus_kcl_a.abs());max_c1=max_c1.max(c1_kcl.abs());
    if c1_kcl.abs()>1e-12||e.observations.bus_kcl_a.abs()>1e-12 {return Err(format!("KCL,{c1_kcl:e},{:e}",e.observations.bus_kcl_a));}
    for (stage,weight) in e.pair.candidates.into_iter().zip([0.75,0.25]) {
     let v=|k|stage.high[k]+stage.low[k];let saw=v(46);let bus=v(12);let input=v(joint::chain_index(6));let series=(v(39)-bus)/33000.;
     for(k,value)in [saw,bus,input,series,0.5*saw-bus].into_iter().enumerate() {means[k].add(h*weight*value);}
    }
    let s=e.pair.candidates[1];let v=|k|s.high[k]+s.low[k];let o=e.observations;
    trace.write_all(&e.elapsed_ticks.to_le_bytes()).map_err(|e|e.to_string())?;trace.write_all(&accepted.half_ticks.to_le_bytes()).map_err(|e|e.to_string())?;trace.write_all(&accepted.attempts.to_le_bytes()).map_err(|e|e.to_string())?;
    for x in [e.pair.residual_ratio,e.pair.correction_ratio,accepted.error_ratio,o.ramp_v,v(48),o.saw_v,v(54),v(44),o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.c27_current_a,o.bus_kcl_a,cur[1][0],cur[1][1],cur[1][2],c1_kcl] {trace.write_all(&x.to_le_bytes()).map_err(|e|e.to_string())?;}
    if last_ramp< -2.&&o.ramp_v>= -2. {crossings+=1;event=true;eprintln!("RESET,crossing={crossings},ticks={}",e.elapsed_ticks);}
    if last_ramp< -2.&&o.ramp_v>= -2. {
     write!(events,"EVENT,{},{},{:.17e},{:.17e}",e.elapsed_ticks-u64::from(accepted.half_ticks),e.elapsed_ticks,charge.value,absolute.value).map_err(|e|e.to_string())?;
     for mean in &means {write!(events,",{:.17e}",mean.value).map_err(|e|e.to_string())?;}writeln!(events).map_err(|e|e.to_string())?;
     for state in [old,s] {write!(events,"JOINT_STATE").map_err(|e|e.to_string())?;for x in state.high.into_iter().chain(state.low) {write!(events,",{x:.17e}").map_err(|e|e.to_string())?;}writeln!(events).map_err(|e|e.to_string())?;}
    }
    last_ramp=o.ramp_v;old=s;
   }
   if steps==1||event||engine.checkpoint().elapsed_ticks==GOAL {selected(&mut roots,before.state,&accepted)?;}
   if engine.checkpoint().elapsed_ticks%ANCHOR==0||engine.checkpoint().elapsed_ticks==1048576 {checks.write_all(&encode(engine.checkpoint())).map_err(|e|e.to_string())?;}
   if steps%2000==0 {trace.flush().map_err(|e|e.to_string())?;eprintln!("PROGRESS,intervals={steps},ticks={},wall_s={:.3}",engine.checkpoint().elapsed_ticks,started.elapsed().as_secs_f64());}
  }Ok(())
 })();
 events.flush().map_err(|e|e.to_string())?;trace.flush().map_err(|e|e.to_string())?;checks.flush().map_err(|e|e.to_string())?;roots.flush().map_err(|e|e.to_string())?;
 fs::write(out.join("final.ckp"),encode(engine.checkpoint())).map_err(|e|e.to_string())?;
 let delta=temporal::difference(engine.checkpoint().state,initial)[43];let balance=(charge.value+1e-8*delta).abs()/absolute.value;
 eprintln!("SUMMARY,intervals={steps},ticks={},crossings={crossings},restore_replays={restores},max_lte={max_lte:.17e},max_bus={max_bus:.17e},max_c1={max_c1:.17e},charge={:.17e},absolute={:.17e},delta_ramp={delta:.17e},balance={balance:.17e}",engine.checkpoint().elapsed_ticks,charge.value,absolute.value);
 if let Err(e)=result {let q=engine.checkpoint();let target=((q.elapsed_ticks/ANCHOR+1)*ANCHOR).min(GOAL);eprintln!("FAILURE,target_ticks={target},reason={e}");return Err(e);}
 eprint!("MEAN_LEDGER");for mean in &means {eprint!(",{:.17e}",mean.value);}eprintln!();
 if crossings!=4||restores!=3||balance>0.002 {return Err("final cycle/restore/balance gate".into());}Ok(())
}
fn replay(file:&Path,target:u64)->Result<(),String> {
 let(p,_)=scene()?;let q=decode(&fs::read(file).map_err(|e|e.to_string())?,p)?;let mut engine=Engine::restore(q).map_err(|e|format!("restore:{e:?}"))?;
 match engine.advance_to(target) {Ok(a)=>{eprintln!("REPLAY_ACCEPT,half_ticks={},error={:.17e}",a.half_ticks,a.error_ratio);Ok(())},Err(e)=>{if encode(engine.checkpoint())!=encode(q) {return Err("failed checkpoint mutated".into());}Err(format!("ENGINE_REJECT,{e:?}"))}}
}
fn main() {
 let a:Vec<String>=std::env::args().collect();let r=if a[1]=="run" {run(a[2].parse().unwrap(),Path::new(&a[3]),a[4].parse().unwrap(),Path::new(&a[5]))} else {replay(Path::new(&a[2]),a[3].parse().unwrap())};
 if let Err(e)=r {eprintln!("ERROR,{e}");std::process::exit(1);}
}
