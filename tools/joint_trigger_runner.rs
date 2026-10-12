//! Bounded fixed-step loaded-follower experiment. All IO belongs to this lab caller.
#[path="joint_trigger_kernel.rs"] mod joint;
use rf_d_circuit::{chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,vco1_stamp::Controls,loudness_follower as follower,SolverBudget};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use std::{fs,io::Write,time::Instant};
fn scene()->joint::Parameters {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let mut p=Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
 p.boundary.panel.cutoff_fraction_from_neg10=1.;joint::Parameters::new(Controls::default(),p,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap()
}
fn write_state(w:&mut impl Write,s:joint::State) {write!(w,"JOINT_STATE").unwrap();for v in s.high.into_iter().chain(s.low) {write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();}
fn same(a:&joint::Pair,b:&joint::Pair)->bool {
 a.residual_ratio.to_bits()==b.residual_ratio.to_bits()&&a.correction_ratio.to_bits()==b.correction_ratio.to_bits()&&a.iterations==b.iterations&&a.trials==b.trials&&a.candidates.iter().chain(a.increments.iter()).zip(b.candidates.iter().chain(b.increments.iter())).all(|(x,y)|x.high.iter().chain(x.low.iter()).zip(y.high.iter().chain(y.low.iter())).all(|(u,v)|u.to_bits()==v.to_bits()))
}
// Conditioned trigger-scene serialization and phase replay; lab IO only.
const START:u64=2785017856;const SPAN:u64=1048576;const SIZE:usize=3664;
const SOURCES:[[f64;3];5]=[[8.3,0.,0.01],[8.3,10.,0.01],[8.3,10.,0.01],[8.3,0.,0.01],[8.3,0.,0.7]];const SHORT:[bool;5]=[false,false,true,false,false];
#[derive(Clone,Copy)]struct Saved{state:joint::State,ticks:u64,half:u32,phase:u32,q25:f64,key:f64,reset:f64,set_base:f64,on:bool,short:bool}
fn encode(q:Saved)->[u8;SIZE]{
 let mut b=[0;SIZE];b[..8].copy_from_slice(b"RFLTRG01");b[8..16].copy_from_slice(&q.ticks.to_le_bytes());b[16..20].copy_from_slice(&q.half.to_le_bytes());b[20..24].copy_from_slice(&q.phase.to_le_bytes());
 for(k,v)in[q.q25,q.key,q.reset,q.set_base].into_iter().enumerate(){b[24+8*k..32+8*k].copy_from_slice(&v.to_le_bytes());}b[56..60].copy_from_slice(&((q.on as u32)|((q.short as u32)<<1)).to_le_bytes());for(k,v)in q.state.high.into_iter().chain(q.state.low).enumerate(){b[64+8*k..72+8*k].copy_from_slice(&v.to_le_bytes());}b
}
fn decode(b:&[u8])->Result<Saved,String>{
 if b.len()!=SIZE||&b[..8]!=b"RFLTRG01"||b[60..64]!=[0;4]{return Err("checkpoint format".into());}let ticks=u64::from_le_bytes(b[8..16].try_into().unwrap());let u=|k:usize|u32::from_le_bytes(b[k..k+4].try_into().unwrap());let half=u(16);let phase=u(20);let flags=u(56);let source=|k:usize|f64::from_le_bytes(b[24+8*k..32+8*k].try_into().unwrap());
 if flags>3||phase>=5||![65536,32768].contains(&half)||ticks<START+u64::from(phase)*SPAN||ticks>START+u64::from(phase+1)*SPAN||(ticks-START)%u64::from(half)!=0{return Err("checkpoint calendar".into());}
 if [source(0),source(1),source(2)].map(f64::to_bits)!=SOURCES[phase as usize].map(f64::to_bits)||source(3).to_bits()!=0.01_f64.to_bits()||((flags&2)!=0)!=SHORT[phase as usize]{return Err("checkpoint recipe".into());}
 let f=|k:usize|f64::from_le_bytes(b[64+8*k..72+8*k].try_into().unwrap());let state=joint::State{high:std::array::from_fn(f),low:std::array::from_fn(|k|f(k+225))};for k in 0..225{let(a,b)=(state.high[k],state.low[k]);let s=a+b;let v=s-a;let e=(a-(s-v))+(b-v);if !a.is_finite()||!b.is_finite()||s.to_bits()!=a.to_bits()||e.to_bits()!=b.to_bits(){return Err("checkpoint state".into());}}
 Ok(Saved{state,ticks,half,phase,q25:source(0),key:source(1),reset:source(2),set_base:source(3),on:(flags&1)!=0,short:(flags&2)!=0})
}
fn parameters(q:Saved)->joint::Parameters{let mut p=scene();p.q25=q.q25;p.keyboard=q.key;p.reset_v=q.reset;p.set_base=q.set_base;p.short=q.short;p.final_decay=q.on;p}
#[derive(Default)]struct Sum{value:f64,low:f64}impl Sum{fn add(&mut self,v:f64){let y=v-self.low;let t=self.value+y;self.low=(t-self.value)-y;self.value=t;}}
fn observations(s:joint::State,p:joint::Parameters,c4:f64)->Result<[f64;16],String>{
 let v=|i|s.high[i]+s.low[i];let d=joint::c2_charge_driver::linearize(std::array::from_fn(|k|v(205+k)),joint::c2_charge_driver::Controls{q25:p.q25,reset_driver:v(217),final_decay:p.final_decay}).map_err(|e|format!("driver observe:{e:?}"))?;let t=joint::trigger_charge_driver::linearize(std::array::from_fn(|k|v(217+k)),joint::trigger_charge_driver::Controls{keyboard:p.keyboard,reset_base:p.reset_v,short:p.short}).map_err(|e|format!("trigger observe:{e:?}"))?;
 let vt=1.5*1.380649e-23*298.15/1.602176634e-19;let fast=if p.final_decay{0.}else{1e-12*((v(205)-v(216))/vt).exp_m1()};let reset=-1e-8*((v(204)-p.reset_v)/vt).exp_m1()+t.ports[3];let supply=d.ports[1]+t.ports[1]+(9.3-v(202))/560.;
 Ok([v(205),v(203),v(194),(v(205)-v(208))/10000.,(v(205)-v(211))/100000.,(v(205)-v(200))/10000.,fast,d.ports[4],d.ports[5],reset,t.ports[2],-c4,supply,v(221),v(217),v(223)-p.set_base])
}
fn selected(w:&mut impl Write,old:joint::State,pair:&joint::Pair,h:f64){writeln!(w,"JOINT_ROOT,0,{h:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio).unwrap();for s in[old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]]{write_state(w,s);}}
fn run()->Result<(),String>{
 let args:Vec<_>=std::env::args().collect();let directory=std::path::Path::new(&args[2]);fs::create_dir_all(directory).map_err(|e|e.to_string())?;let mut q=decode(&fs::read(&args[1]).map_err(|e|e.to_string())?)?;if q.ticks!=START||q.phase!=0{return Err("seed metadata".into());}let bytes=encode(q);
 for kind in 0..4{let mut b=bytes;match kind{0=>b[0]^=1,1=>b[64+8*221..72+8*221].copy_from_slice(&f64::NAN.to_le_bytes()),2=>b[20..24].copy_from_slice(&9_u32.to_le_bytes()),_=>b[32..40].copy_from_slice(&10_f64.to_le_bytes())}if decode(&b).is_ok(){return Err("corruption accepted".into());}}
 let mut w=std::io::BufWriter::new(fs::File::create(directory.join("selected.txt")).map_err(|e|e.to_string())?);let mut checkpoints=fs::File::create(directory.join("checkpoints.bin")).map_err(|e|e.to_string())?;writeln!(w,"PROFILE,{},{}",q.on as u32,q.half).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&bytes).unwrap();let started=Instant::now();let mut total=std::array::from_fn::<_,15,_>(|_|Sum::default());let mut restores=0;let mut repeats=0;let mut steps=0;
 for phase in 0..5{
  let incoming=encode(q);q.phase=phase;[q.q25,q.key,q.reset]=SOURCES[phase as usize];q.short=SHORT[phase as usize];let changed=encode(q);if incoming[64..]!=changed[64..]{return Err("source changes state".into());}writeln!(w,"BOUNDARY,{phase},{},{:.17e},{:.17e},{:.17e},{}",q.ticks,q.q25,q.key,q.reset,q.short as u32).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&changed).unwrap();fs::write(directory.join(format!("phase{phase}-start.ckp")),changed).unwrap();let initial=q;let p=parameters(q);let h=f64::from(q.half)*125e-9/65536.;let count=(SPAN/u64::from(q.half))as usize;let mut pairs=Vec::new();let mut middle=None;let mut integrals=std::array::from_fn::<_,15,_>(|_|Sum::default());
  for k in 0..count{
   if started.elapsed().as_secs_f64()>300.{return Err("wall budget".into());}if k==count/2{fs::write(directory.join(format!("phase{phase}-middle.ckp")),encode(q)).unwrap();middle=Some(q);}
   let pair=joint::step(p,q.state,h).map_err(|e|format!("step,phase={phase},k={k}:{e:?}"))?;if k==0||k+1==count{selected(&mut w,q.state,&pair,h);}
   let cap=|i:usize|1e-8/h*(joint::B[i][0]*(pair.increments[0].high[223]+pair.increments[0].low[223])+joint::B[i][1]*(pair.increments[1].high[223]+pair.increments[1].low[223]));
   for(i,weight)in[0.75,0.25].into_iter().enumerate(){let part=joint::parts(p,q.state,pair.increments[i],h).map_err(|e|format!("ledger:{e:?}"))?;let o=observations(pair.candidates[i],p,cap(i))?;for(a,v)in[part.dc[205],part.dc[195],part.dc[139],o[7],o[8],o[9],o[3],o[4],o[5],o[6],part.dc[221],part.dc[223],o[10],o[11],o[12]].into_iter().enumerate(){integrals[a].add(h*weight*v);total[a].add(h*weight*v);}}
   let c4=cap(1);q.state=pair.candidates[1];q.ticks+=u64::from(q.half);let o=observations(q.state,p,c4)?;write!(w,"OBS,{},{phase}",q.ticks).unwrap();for v in o{write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();pairs.push(pair);steps+=1;
  }
  write!(w,"LEDGER,{phase},{}",q.ticks).unwrap();for a in &integrals{write!(w,",{:.17e}",a.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&encode(q)).unwrap();
  for(k0,name,expected)in[(0,format!("phase{phase}-start.ckp"),initial),(count/2,format!("phase{phase}-middle.ckp"),middle.unwrap())]{let raw=fs::read(directory.join(name)).map_err(|e|e.to_string())?;let mut saved=decode(&raw)?;if encode(saved).as_slice()!=raw||encode(saved)!=encode(expected){return Err("restore bytes".into());}for k in k0..count{let replay=joint::step(parameters(saved),saved.state,h).map_err(|e|format!("replay:{e:?}"))?;if !same(&pairs[k],&replay){return Err(format!("restore pair:{phase},{k}"));}saved.state=replay.candidates[1];saved.ticks+=u64::from(saved.half);repeats+=1;}if encode(saved)!=encode(q){return Err("restore final".into());}restores+=1;}
 }
 write!(w,"TOTAL").unwrap();for a in &total{write!(w,",{:.17e}",a.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,q.state);w.flush().unwrap();checkpoints.flush().unwrap();fs::write(directory.join("final.ckp"),encode(q)).unwrap();eprintln!("COMPLETED,on={},half={},steps={steps},restores={restores},replay_steps={repeats},corruptions=4,wall_s={}",q.on as u32,q.half,started.elapsed().as_secs_f64());Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
