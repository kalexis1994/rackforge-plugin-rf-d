use rf_d_circuit::{vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton};
#[path="linear.rs"] mod output_conversion;
#[path="fine.rs"] mod fine;
#[path="radau.rs"] mod radau;
use vco1_stamp::{Controls,N};use fine::State;use std::io::{Write,BufWriter};
const TICK:f64=125e-9/65536.;
fn state(v:&str)->State {let a:Vec<f64>=v.split_whitespace().map(|x|x.parse().unwrap()).collect();State{high:a[..N].try_into().unwrap(),low:a[N..].try_into().unwrap()}}
fn report(scene:usize,power:i32,label:&str,p:&radau::Pair) {
 for (part,s) in [("stage",&p.stage),("endpoint",&p.endpoint)] {print!("ROOT,{scene},{power},{label},{part},{:.17e},{:.17e},{},{}",s.residual_ratio,s.correction_ratio,s.iterations,s.trials);for v in s.candidate.high.into_iter().chain(s.candidate.low) {print!(",{v:.17e}");}println!();}

}
fn emit(w:&mut impl Write,elapsed:u32,ticks:u32,p:&radau::Pair,error:f64,attempts:u32)->std::io::Result<()> {
 for v in [elapsed as f64,ticks as f64,p.stage.residual_ratio.max(p.endpoint.residual_ratio),p.stage.correction_ratio.max(p.endpoint.correction_ratio),error,attempts as f64].into_iter().chain(p.endpoint.candidate.high).chain(p.endpoint.candidate.low).chain(p.stage.candidate.high).chain(p.stage.candidate.low) {w.write_all(&v.to_le_bytes())?;}Ok(())
}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let args:Vec<String>=std::env::args().collect();let c=Controls::default();let histories=[state(include_str!("history0.txt")),state(include_str!("history1.txt"))];
 if args[1]=="roots" {
  for (scene,old) in histories.into_iter().enumerate() {for power in 0..=3 {
   let h=4.*TICK*2_f64.powi(power);let full=radau::step(c,old,2.*h).map_err(|e|format!("full {scene}/{power}:{e:?}"))?;let mid=radau::step(c,old,h).map_err(|e|format!("mid {scene}/{power}:{e:?}"))?;let end=radau::step(c,mid.endpoint.candidate,h).map_err(|e|format!("end {scene}/{power}:{e:?}"))?;
   report(scene,power,"full",&full);report(scene,power,"mid",&mid);report(scene,power,"end",&end);
  }}return Ok(());
 }
 if args[1]!="walk" {return Err("mode".into());}let mut w=BufWriter::new(std::fs::File::create(&args[2])?);let limit=(1e-6/TICK).round() as u32;let maximum=262144;let mut proposal=2*maximum;let mut old=histories[1];let mut elapsed=0;let mut steps=0;
 for v in [0.;6].into_iter().chain(old.high).chain(old.low).chain(old.high).chain(old.low) {w.write_all(&v.to_le_bytes())?;}
 while elapsed<limit {
  if steps>=20000 {w.flush()?;return Err(format!("ENDPOINT_BUDGET,elapsed={elapsed},steps={steps}").into());}
  let mut ticks=proposal;while ticks>limit-elapsed {ticks/=2;}
  let mut accepted=None;
  for attempts in 1..=20 {
   let trial=(|| {let full=radau::step(c,old,ticks as f64*TICK)?;let mid=radau::step(c,old,(ticks/2) as f64*TICK)?;let end=radau::step(c,mid.endpoint.candidate,(ticks/2) as f64*TICK)?;let difference=full.endpoint.candidate.difference(end.endpoint.candidate);let error=(0..N).fold(0_f64,|a,k|a.max(difference[k].abs()/if k<98 {2e-6} else {2e-9}));Ok::<_,vco1_newton::Error>((mid,end,error))})();
   if let Ok((mid,end,error))=trial {if error<=1. {accepted=Some((mid,end,error,attempts));break;}}
   if ticks<=8 {w.flush()?;return Err(format!("elapsed={elapsed},dt_ticks={ticks},time_s={:.17e},LocalStepReject",elapsed as f64*TICK).into());}ticks/=2;
  }
  let (mid,end,error,attempts)=accepted.ok_or("attempt limit")?;proposal=if error<=0.25 {(ticks*2).min(2*maximum)} else {ticks};elapsed+=ticks/2;emit(&mut w,elapsed,ticks/2,&mid,error,attempts)?;elapsed+=ticks/2;emit(&mut w,elapsed,ticks/2,&end,error,attempts)?;old=end.endpoint.candidate;steps+=2;
 }
 w.flush()?;println!("COMPLETE,steps={steps},ticks={elapsed}");Ok(())
}
