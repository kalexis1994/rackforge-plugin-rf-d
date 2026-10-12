//! Bounded fixed-step loaded-follower experiment. All IO belongs to this lab caller.
#[path="joint_loudness_kernel.rs"] mod joint;
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
// Laboratory checkpoint and schedule extension; appended to a protected caller prefix.
const START:u64=2753560576;
const SPAN:u64=1048576;
const SIZE:usize=3320;
const SOURCES:[[f64;2];5]=[[3.2,0.7],[6.,0.7],[6.,0.01],[0.8469345758149237,0.01],[3.2,0.7]];
#[derive(Clone,Copy)] struct Saved {state:joint::State,ticks:u64,half:u32,phase:u32,c2:f64,reset:f64}
fn encode(q:Saved)->[u8;SIZE] {
 let mut b=[0;SIZE];b[..8].copy_from_slice(b"RFLCTL01");b[8..16].copy_from_slice(&q.ticks.to_le_bytes());b[16..20].copy_from_slice(&q.half.to_le_bytes());b[20..24].copy_from_slice(&q.phase.to_le_bytes());
 for(k,v) in [q.c2,q.reset].into_iter().chain(q.state.high).chain(q.state.low).enumerate() {b[24+8*k..32+8*k].copy_from_slice(&v.to_le_bytes());}b
}
fn decode(b:&[u8])->Result<Saved,String> {
 if b.len()!=SIZE||&b[..8]!=b"RFLCTL01" {return Err("checkpoint format".into());}
 let ticks=u64::from_le_bytes(b[8..16].try_into().unwrap());let half=u32::from_le_bytes(b[16..20].try_into().unwrap());let phase=u32::from_le_bytes(b[20..24].try_into().unwrap());let f=|k|f64::from_le_bytes(b[24+8*k..32+8*k].try_into().unwrap());
 if phase>=5||![65536,32768].contains(&half)||ticks<START+u64::from(phase)*SPAN||ticks>START+u64::from(phase+1)*SPAN||(ticks-START)%u64::from(half)!=0 {return Err("checkpoint clock/settings".into());}
 if [f(0).to_bits(),f(1).to_bits()]!=SOURCES[phase as usize].map(f64::to_bits) {return Err("checkpoint source recipe".into());}
 let state=joint::State{high:std::array::from_fn(|k|f(k+2)),low:std::array::from_fn(|k|f(k+207))};
 for k in 0..205 {
  let(a,b)=(state.high[k],state.low[k]);let s=a+b;let v=s-a;let e=(a-(s-v))+(b-v);
  if !a.is_finite()||!b.is_finite()||s.to_bits()!=a.to_bits()||e.to_bits()!=b.to_bits() {return Err("checkpoint state".into());}
 }
 Ok(Saved{state,ticks,half,phase,c2:f(0),reset:f(1)})
}
fn parameters(q:Saved)->joint::Parameters {let mut p=scene();p.c2_v=q.c2;p.reset_v=q.reset;p}
#[derive(Default)] struct Sum {value:f64,low:f64}
impl Sum {fn add(&mut self,v:f64){let y=v-self.low;let t=self.value+y;self.low=(t-self.value)-y;self.value=t;}}
fn ports(s:joint::State,p:joint::Parameters)->[f64;3] {
 let v=|i|s.high[i]+s.low[i];let f=follower::Parameters::default();let vt=f.diode_ideality*1.380649e-23*f.temperature_k/1.602176634e-19;
 [(p.c2_v-v(200))/10000.,-f.germanium_is_a*((v(204)-p.reset_v)/vt).exp_m1(),(v(203)-v(165))/68000.]
}
fn selected(w:&mut impl Write,old:joint::State,pair:&joint::Pair,h:f64) {
 writeln!(w,"JOINT_ROOT,0,{h:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio).unwrap();
 for s in [old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]] {write_state(w,s);}
}
fn run()->Result<(),String> {
 let args:Vec<_>=std::env::args().collect();let directory=std::path::Path::new(&args[2]);fs::create_dir_all(directory).map_err(|e|e.to_string())?;
 let mut q=decode(&fs::read(&args[1]).map_err(|e|e.to_string())?)?;if q.ticks!=START||q.phase!=0 {return Err("seed metadata".into());}
 let bytes=encode(q);let mut corruptions=0;
 for kind in 0..4 {
  let mut b=bytes;
  match kind {0=>b[0]^=1,1=>b[40..48].copy_from_slice(&f64::NAN.to_le_bytes()),2=>b[20..24].copy_from_slice(&9_u32.to_le_bytes()),_=>b[24..32].copy_from_slice(&6_f64.to_le_bytes())}
  if decode(&b).is_ok() {return Err(format!("corruption accepted:{kind}"));}corruptions+=1;
 }
 let mut w=std::io::BufWriter::new(fs::File::create(directory.join("selected.txt")).map_err(|e|e.to_string())?);let mut checkpoints=fs::File::create(directory.join("checkpoints.bin")).map_err(|e|e.to_string())?;
 writeln!(w,"PROFILE,{}",q.half).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&bytes).unwrap();let started=Instant::now();let mut total=std::array::from_fn::<_,4,_>(|_|Sum::default());let mut restores=0;let mut replay_steps=0;let mut steps=0;
 for phase in 0..5 {
  let incoming=encode(q);q.phase=phase;q.c2=SOURCES[phase as usize][0];q.reset=SOURCES[phase as usize][1];let changed=encode(q);if incoming[40..]!=changed[40..] {return Err("source change rewrote state".into());}
  writeln!(w,"BOUNDARY,{phase},{},{:.17e},{:.17e}",q.ticks,q.c2,q.reset).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&changed).unwrap();fs::write(directory.join(format!("phase{phase}-start.ckp")),changed).unwrap();
  let initial=q;let p=parameters(q);let h=f64::from(q.half)*125e-9/65536.;let count=(SPAN/u64::from(q.half)) as usize;let mut pairs=Vec::new();let mut middle=None;let mut integrals=std::array::from_fn::<_,4,_>(|_|Sum::default());
  for k in 0..count {
   if started.elapsed().as_secs_f64()>300. {return Err("wall budget".into());}
   if k==count/2 {fs::write(directory.join(format!("phase{phase}-middle.ckp")),encode(q)).unwrap();middle=Some(q);}
   let pair=joint::step(p,q.state,h).map_err(|e|format!("step,phase={phase},k={k}:{e:?}"))?;
   if k==0||k+1==count {selected(&mut w,q.state,&pair,h);}
   for(i,weight) in [0.75,0.25].into_iter().enumerate() {
    let part=joint::parts(p,q.state,pair.increments[i],h).map_err(|e|format!("ledger:{e:?}"))?;let port=ports(pair.candidates[i],p);
    for(a,v) in [part.dc[195],part.dc[139],port[0],port[1]].into_iter().enumerate() {integrals[a].add(h*weight*v);total[a].add(h*weight*v);}
   }
   q.state=pair.candidates[1];q.ticks+=u64::from(q.half);let current=ports(q.state,p);let v=|i|q.state.high[i]+q.state.low[i];
   writeln!(w,"OBS,{},{phase},{:.17e},{:.17e},{:.17e},{:.17e},{:.17e}",q.ticks,v(203),v(194),current[0],current[1],current[2]).unwrap();pairs.push(pair);steps+=1;
  }
  writeln!(w,"LEDGER,{phase},{},{:.17e},{:.17e},{:.17e},{:.17e}",q.ticks,integrals[0].value,integrals[1].value,integrals[2].value,integrals[3].value).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&encode(q)).unwrap();
  for (k0,name,expected) in [(0,format!("phase{phase}-start.ckp"),initial),(count/2,format!("phase{phase}-middle.ckp"),middle.unwrap())] {
   let raw=fs::read(directory.join(name)).map_err(|e|e.to_string())?;let mut saved=decode(&raw)?;if encode(saved).as_slice()!=raw||encode(saved)!=encode(expected) {return Err("restore bytes".into());}
   for k in k0..count {
    let replay=joint::step(parameters(saved),saved.state,h).map_err(|e|format!("replay:{e:?}"))?;if !same(&pairs[k],&replay) {return Err(format!("restore pair mismatch:{phase},{k}"));}saved.state=replay.candidates[1];saved.ticks+=u64::from(saved.half);replay_steps+=1;
   }
   if encode(saved)!=encode(q) {return Err("restore final checkpoint".into());}restores+=1;
  }
 }
 writeln!(w,"TOTAL,{:.17e},{:.17e},{:.17e},{:.17e}",total[0].value,total[1].value,total[2].value,total[3].value).unwrap();write_state(&mut w,q.state);w.flush().unwrap();checkpoints.flush().unwrap();fs::write(directory.join("final.ckp"),encode(q)).unwrap();
 eprintln!("COMPLETED,half={},steps={steps},restores={restores},replay_steps={replay_steps},corruptions={corruptions},wall_s={}",q.half,started.elapsed().as_secs_f64());Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
