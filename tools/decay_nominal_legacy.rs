//! Continue released ON history by 8 ms; no new source event.
//! No audio-thread admission. See docs/VOZ_LIBERACION_PROTOCOLO.md.
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
const START:u64=10717495296;const REL:[u64;2]=[0,4194304000];const CUT:u64=157286400;const SIZE:usize=3720;
const KEY:[f64;1]=[0.];const SHORT:[bool;1]=[false];
#[derive(Clone,Copy)]struct Saved{q:temporal::Checkpoint,phase:u32}
fn encode(s:Saved)->[u8;SIZE]{
 let q=s.q;let mut b=[0;SIZE];b[..8].copy_from_slice(b"RFREL001");b[8..16].copy_from_slice(&q.elapsed_ticks.to_le_bytes());for(k,v)in[q.settings.maximum_half_ticks,q.settings.attempt_limit,q.next_full_ticks,s.phase,1,(q.parameters.final_decay as u32)|((q.parameters.short as u32)<<1)].into_iter().enumerate(){b[16+4*k..20+4*k].copy_from_slice(&v.to_le_bytes());}b[40..48].copy_from_slice(&q.parameters.keyboard.to_le_bytes());for(k,v)in q.state.high.into_iter().chain(q.state.low).enumerate(){b[56+8*k..64+8*k].copy_from_slice(&v.to_le_bytes());}b
}
fn decode(b:&[u8])->Result<Saved,String>{
 if b.len()!=SIZE||&b[..8]!=b"RFREL001"||b[48..56]!=[0;8]{return Err("checkpoint format".into());}let u=|k:usize|u32::from_le_bytes(b[k..k+4].try_into().unwrap());let ticks=u64::from_le_bytes(b[8..16].try_into().unwrap());let max=u(16);let limit=u(20);let next=u(24);let phase=u(28);let flags=u(36);let key=f64::from_le_bytes(b[40..48].try_into().unwrap());
 if phase!=0||u(32)!=1||flags!=1||![1048576,524288].contains(&max)||!(1..=20).contains(&limit)||ticks<START+REL[phase as usize]||ticks>START+REL[phase as usize+1]||ticks%8!=0||next<8||!next.is_power_of_two()||next>2*max||key.to_bits()!=KEY[phase as usize].to_bits()||((flags&2)!=0)!=SHORT[phase as usize]{return Err("checkpoint recipe".into());}
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

fn nominal_blob(a:&temporal::Accepted,q:temporal::Checkpoint)->Vec<u8>{
 let mut b=Vec::new();for p in [&a.coarse,&a.endpoints[0].pair,&a.endpoints[1].pair]{
  for s in p.candidates.iter().chain(p.increments.iter()){for v in s.high.iter().chain(s.low.iter()){b.extend_from_slice(&v.to_le_bytes());}}
  for v in [p.residual_ratio,p.correction_ratio]{b.extend_from_slice(&v.to_le_bytes());}for v in [p.iterations,p.trials]{b.extend_from_slice(&(v as u64).to_le_bytes());}
 }
 for ep in &a.endpoints{b.extend_from_slice(&ep.elapsed_ticks.to_le_bytes());let o=ep.observations;for v in [o.saw_v,o.ramp_v,o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.series_current_a,o.c27_current_a,o.bus_kcl_a]{b.extend_from_slice(&v.to_le_bytes());}}
 b.extend_from_slice(&a.half_ticks.to_le_bytes());b.extend_from_slice(&a.error_ratio.to_le_bytes());b.extend_from_slice(&a.attempts.to_le_bytes());
 for v in q.state.high.iter().chain(q.state.low.iter()){b.extend_from_slice(&v.to_le_bytes());}b.extend_from_slice(&q.elapsed_ticks.to_le_bytes());for v in [q.settings.maximum_half_ticks,q.settings.attempt_limit,q.next_full_ticks]{b.extend_from_slice(&v.to_le_bytes());}
 b.extend_from_slice(&q.parameters.keyboard.to_le_bytes());b.push(q.parameters.final_decay as u8);b.push(q.parameters.short as u8);b
}
fn main(){let args:Vec<_>=std::env::args().collect();let q=decode(&fs::read(&args[1]).unwrap()).unwrap().q;let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).unwrap();let mut e=temporal::Engine::restore(q).unwrap();let mut w=joint::Workspace::new();let mut out=Vec::new();for _ in 0..4{let a=e.advance_to(&mut w,q.elapsed_ticks+419430400).unwrap();out.extend(nominal_blob(&a,e.checkpoint()));}fs::write(dir.join("nominal.bin"),out).unwrap();eprintln!("NOMINAL_LEGACY,{},4",q.settings.maximum_half_ticks);}
