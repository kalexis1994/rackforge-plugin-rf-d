//! Private-domain diagnostic: original source copies live beside this runner.
use rf_d_circuit::{vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton};
#[path="linear.rs"] mod output_conversion;
#[path="fine.rs"] mod fine;
#[path="adaptive.rs"] mod adaptive;
use vco1_stamp::{Controls,N};use fine::State;use std::io::{Write,BufWriter};
fn emit(w:&mut impl Write,elapsed:u32,state:State,ticks:u32,res:f64,corr:f64,error:f64,attempts:u32)->std::io::Result<()> {for v in [elapsed as f64,ticks as f64,res,corr,error,attempts as f64].into_iter().chain(state.high).chain(state.low) {w.write_all(&v.to_le_bytes())?;}Ok(())}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let a:Vec<f64>=include_str!("history.txt").split_whitespace().map(|x|x.parse().unwrap()).collect();let old=State{high:a[..N].try_into().unwrap(),low:a[N..].try_into().unwrap()};let c=Controls::default();let oldtick=125e-9/4096.;
 for power in 0..=4 {
  let h=oldtick/2_f64.powi(power);let full=fine::solve(c,old,2.*h,vco1_newton::Budget::default()).map_err(|e|format!("full p={power}: {e:?}"))?;let mid=fine::solve(c,old,h,vco1_newton::Budget::default()).map_err(|e|format!("mid p={power}: {e:?}"))?;let end=fine::solve(c,mid.candidate,h,vco1_newton::Budget::default()).map_err(|e|format!("end p={power}: {e:?}"))?;
  for (label,s) in [("full",full),("mid",mid),("end",end)] {print!("ROOT,{power},{label},{:.17e},{:.17e},{},{}",s.residual_ratio,s.correction_ratio,s.iterations,s.trials);for v in s.candidate.high.into_iter().chain(s.candidate.low) {print!(",{v:.17e}");}println!();}
 }
 let path=std::env::args().nth(1).ok_or("output")?;let mut w=BufWriter::new(std::fs::File::create(path)?);emit(&mut w,0,old,0,0.,0.,0.,0)?;let limit=(50e-6/adaptive::TICK_S).round() as u32;let max=(500e-9/adaptive::TICK_S).round() as u32;let mut proposal=2*max;let mut elapsed=0;let mut current=old;let mut steps=0;let mut smallest=u32::MAX;
 while elapsed<limit {
  let p=match adaptive::advance(c,current,proposal,max,limit-elapsed) {Ok(p)=>p,Err(e)=>{w.flush()?;return Err(format!("elapsed={elapsed},time_s={:.17e},proposed={proposal},error={e:?}",elapsed as f64*adaptive::TICK_S).into());}};
  proposal=p.next_full_ticks;elapsed+=p.half_ticks;emit(&mut w,elapsed,p.midpoint.candidate,p.half_ticks,p.midpoint.residual_ratio,p.midpoint.correction_ratio,p.error_ratio,p.attempts)?;elapsed+=p.half_ticks;emit(&mut w,elapsed,p.endpoint.candidate,p.half_ticks,p.endpoint.residual_ratio,p.endpoint.correction_ratio,p.error_ratio,p.attempts)?;current=p.endpoint.candidate;steps+=2;smallest=smallest.min(p.half_ticks);
 }
 w.flush()?;println!("COMPLETE,steps={steps},ticks={elapsed},minimum_half_ticks={smallest}");Ok(())
}
