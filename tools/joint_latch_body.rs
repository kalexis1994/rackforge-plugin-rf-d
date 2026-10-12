// Full board2 joint laboratory caller; IO is excluded from the audio engine.
const START:u64=2790260736;const SPAN:u64=1048576;const SIZE:usize=3712;
const KEY:[f64;5]=[0.,10.,10.,0.,0.];const SHORT:[bool;5]=[false,false,true,false,false];
#[derive(Clone,Copy)]struct Saved{state:joint::State,ticks:u64,half:u32,phase:u32,key:f64,on:bool,short:bool}
fn encode(q:Saved)->[u8;SIZE]{
 let mut b=[0;SIZE];b[..8].copy_from_slice(b"RFLATCH1");b[8..16].copy_from_slice(&q.ticks.to_le_bytes());b[16..20].copy_from_slice(&q.half.to_le_bytes());b[20..24].copy_from_slice(&q.phase.to_le_bytes());b[24..32].copy_from_slice(&q.key.to_le_bytes());b[32..40].copy_from_slice(&1_f64.to_le_bytes());b[40..44].copy_from_slice(&((q.on as u32)|((q.short as u32)<<1)).to_le_bytes());for(k,v)in q.state.high.into_iter().chain(q.state.low).enumerate(){b[48+8*k..56+8*k].copy_from_slice(&v.to_le_bytes());}b
}
fn decode(b:&[u8])->Result<Saved,String>{
 if b.len()!=SIZE||&b[..8]!=b"RFLATCH1"||b[44..48]!=[0;4]||b[32..40]!=1_f64.to_le_bytes(){return Err("checkpoint format/model".into());}let ticks=u64::from_le_bytes(b[8..16].try_into().unwrap());let u=|k:usize|u32::from_le_bytes(b[k..k+4].try_into().unwrap());let half=u(16);let phase=u(20);let flags=u(40);let key=f64::from_le_bytes(b[24..32].try_into().unwrap());
 if flags>3||phase>=5||![8192,4096].contains(&half)||ticks<START+u64::from(phase)*SPAN||ticks>START+u64::from(phase+1)*SPAN||(ticks-START)%u64::from(half)!=0{return Err("checkpoint calendar".into());}
 if key.to_bits()!=KEY[phase as usize].to_bits()||((flags&2)!=0)!=SHORT[phase as usize]{return Err("checkpoint recipe".into());}
 let f=|k:usize|f64::from_le_bytes(b[48+8*k..56+8*k].try_into().unwrap());let state=joint::State{high:std::array::from_fn(f),low:std::array::from_fn(|k|f(k+229))};for k in 0..229{let(a,b)=(state.high[k],state.low[k]);let s=a+b;let v=s-a;let e=(a-(s-v))+(b-v);if !a.is_finite()||!b.is_finite()||s.to_bits()!=a.to_bits()||e.to_bits()!=b.to_bits(){return Err("checkpoint state".into());}}
 Ok(Saved{state,ticks,half,phase,key,on:(flags&1)!=0,short:(flags&2)!=0})
}
fn parameters(q:Saved)->joint::Parameters{let mut p=scene();p.keyboard=q.key;p.short=q.short;p.final_decay=q.on;p}
#[derive(Default)]struct Sum{value:f64,low:f64}impl Sum{fn add(&mut self,v:f64){let y=v-self.low;let t=self.value+y;self.low=(t-self.value)-y;self.value=t;}}
fn observations(s:joint::State,p:joint::Parameters)->Result<[f64;13],String>{
 let v=|i|s.high[i]+s.low[i];let t=joint::contour_closed_driver::linearize(std::array::from_fn(|k|v(if k<29{200+k}else{165})),p.keyboard,p.final_decay,p.short).map_err(|e|format!("observe:{e:?}"))?;
 Ok([v(205),v(203),v(194),v(221),v(217),v(223)-v(225),v(225),v(226),v(227),v(228),t.ports[4],t.ports[1],(v(203)-v(165))/68000.])
}
fn selected(w:&mut impl Write,old:joint::State,pair:&joint::Pair,h:f64){writeln!(w,"JOINT_ROOT,0,{h:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio).unwrap();for s in[old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]]{write_state(w,s);}}
fn run()->Result<(),String>{
 let args:Vec<_>=std::env::args().collect();let directory=std::path::Path::new(&args[2]);fs::create_dir_all(directory).map_err(|e|e.to_string())?;let mut q=decode(&fs::read(&args[1]).map_err(|e|e.to_string())?)?;if q.ticks!=START||q.phase!=0{return Err("seed metadata".into());}let bytes=encode(q);
 for kind in 0..4{let mut b=bytes;match kind{0=>b[0]^=1,1=>b[48+8*225..56+8*225].copy_from_slice(&f64::NAN.to_le_bytes()),2=>b[20..24].copy_from_slice(&9_u32.to_le_bytes()),_=>b[24..32].copy_from_slice(&10_f64.to_le_bytes())}if decode(&b).is_ok(){return Err("corruption accepted".into());}}
 let mut w=std::io::BufWriter::new(fs::File::create(directory.join("selected.txt")).map_err(|e|e.to_string())?);let mut checkpoints=fs::File::create(directory.join("checkpoints.bin")).map_err(|e|e.to_string())?;writeln!(w,"PROFILE,{},{}",q.on as u32,q.half).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&bytes).unwrap();let started=Instant::now();let mut total=std::array::from_fn::<_,9,_>(|_|Sum::default());let mut restores=0;let mut repeats=0;let mut steps=0;
 for phase in 0..5{
  let incoming=encode(q);q.phase=phase;q.key=KEY[phase as usize];q.short=SHORT[phase as usize];let changed=encode(q);if incoming[48..]!=changed[48..]{return Err("source changes state".into());}writeln!(w,"BOUNDARY,{phase},{},{:.17e},{}",q.ticks,q.key,q.short as u32).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&changed).unwrap();fs::write(directory.join(format!("phase{phase}-start.ckp")),changed).unwrap();let initial=q;let p=parameters(q);let h=f64::from(q.half)*125e-9/65536.;let count=(SPAN/u64::from(q.half))as usize;let mut pairs=Vec::new();let mut middle=None;let mut integrals=std::array::from_fn::<_,9,_>(|_|Sum::default());
  for k in 0..count{
   if started.elapsed().as_secs_f64()>300.{return Err("wall budget".into());}if k==count/2{fs::write(directory.join(format!("phase{phase}-middle.ckp")),encode(q)).unwrap();middle=Some(q);}
   let pair=joint::step(p,q.state,h).map_err(|e|format!("step,phase={phase},k={k}:{e:?}"))?;if k==0||k+1==count{selected(&mut w,q.state,&pair,h);}
   for(i,weight)in[0.75,0.25].into_iter().enumerate(){let part=joint::parts(p,q.state,pair.increments[i],h).map_err(|e|format!("ledger:{e:?}"))?;for(a,k)in[205,195,139,221,223,225,226,227,228].into_iter().enumerate(){integrals[a].add(h*weight*part.dc[k]);total[a].add(h*weight*part.dc[k]);}}
   q.state=pair.candidates[1];q.ticks+=u64::from(q.half);let o=observations(q.state,p)?;write!(w,"OBS,{},{phase}",q.ticks).unwrap();for v in o{write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();pairs.push(pair);steps+=1;
  }
  write!(w,"LEDGER,{phase},{}",q.ticks).unwrap();for a in &integrals{write!(w,",{:.17e}",a.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,q.state);checkpoints.write_all(&encode(q)).unwrap();
  for(k0,name,expected)in[(0,format!("phase{phase}-start.ckp"),initial),(count/2,format!("phase{phase}-middle.ckp"),middle.unwrap())]{let raw=fs::read(directory.join(name)).map_err(|e|e.to_string())?;let mut saved=decode(&raw)?;if encode(saved).as_slice()!=raw||encode(saved)!=encode(expected){return Err("restore bytes".into());}for k in k0..count{let replay=joint::step(parameters(saved),saved.state,h).map_err(|e|format!("replay:{e:?}"))?;if !same(&pairs[k],&replay){return Err(format!("restore pair:{phase},{k}"));}saved.state=replay.candidates[1];saved.ticks+=u64::from(saved.half);repeats+=1;}if encode(saved)!=encode(q){return Err("restore final".into());}restores+=1;}
 }
 write!(w,"TOTAL").unwrap();for a in &total{write!(w,",{:.17e}",a.value).unwrap();}writeln!(w).unwrap();write_state(&mut w,q.state);w.flush().unwrap();checkpoints.flush().unwrap();fs::write(directory.join("final.ckp"),encode(q)).unwrap();eprintln!("COMPLETED,on={},half={},steps={steps},restores={restores},replay_steps={repeats},corruptions=4,wall_s={}",q.on as u32,q.half,started.elapsed().as_secs_f64());Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
