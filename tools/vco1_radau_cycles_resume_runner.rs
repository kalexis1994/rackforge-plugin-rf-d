//! Own circuit-derived startup; 30ms Radau lab, complete accepted states.
use rf_d_circuit::{vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton,vco1_startup};
#[path="linear.rs"] mod output_conversion;
#[path="fine.rs"] mod fine;
#[path="radau.rs"] mod radau;
use vco1_stamp::{Controls,N};use fine::State;use std::io::{Write,BufWriter};
const TICK:f64=125e-9/65536.;
fn currents(p:&radau::Pair,old:State,h:f64)->Result<[f64;3],vco1_stamp::Error> {
 let a=p.stage.candidate;let b=p.endpoint.candidate;
 let fa=fine::observed_currents(a,a,h)?;let ea=fine::observed_currents(a,old,h)?;
 let fb=fine::observed_currents(b,b,h)?;let eb=fine::observed_currents(b,old,h)?;
 Ok(std::array::from_fn(|k|fb[k]+radau::B[1][0]*(ea[k]-fa[k])+radau::B[1][1]*(eb[k]-fb[k])))
}
fn emit(w:&mut impl Write,elapsed:u64,ticks:u32,p:&radau::Pair,old:State,error:f64,attempts:u32)->Result<(),Box<dyn std::error::Error>> {
 let s=p.endpoint.candidate;let cur=currents(p,old,ticks as f64*TICK).map_err(|e|format!("currents:{e:?}"))?;
 let panel=(s.high[46]-s.high[39]+s.low[46]-s.low[39])/12500.;
 for v in [elapsed as f64,ticks as f64,p.stage.residual_ratio.max(p.endpoint.residual_ratio),p.stage.correction_ratio.max(p.endpoint.correction_ratio),error,attempts as f64].into_iter().chain(s.high).chain(s.low).chain(p.stage.candidate.high).chain(p.stage.candidate.low).chain(cur).chain([panel]) {w.write_all(&v.to_le_bytes())?;}Ok(())
}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let args:Vec<String>=std::env::args().collect();let maximum:u32=args[1].parse()?;if ![65536,131072].contains(&maximum) {return Err("maximum".into());}
 let c=Controls::default();let initial=vco1_startup::startup(c).map_err(|e|format!("startup:{e:?}"))?;
 if initial.residual_ratio>1.||initial.correction_ratio>1. {return Err("startup gate".into());}
 eprintln!("STARTUP,forcing_a={:.17e},residual_ratio={:.17e},correction_ratio={:.17e}",initial.startup_current_a.ok_or("missing startup forcing")?,initial.residual_ratio,initial.correction_ratio);
 let mut old=State::from_nodes(initial.nodes);let mut elapsed=0_u64;
 if args.len()==5 {let content=std::fs::read_to_string(&args[2])?;let a:Vec<f64>=content.split_whitespace().map(str::parse).collect::<Result<_,_>>()?;if a.len()!=2*N {return Err("checkpoint shape".into());}old=State{high:a[..N].try_into()?,low:a[N..].try_into()?};elapsed=args[3].parse()?;eprintln!("RESUME,ticks={elapsed}");}else if args.len()!=2 {return Err("arguments".into());}
let mut steps=0;let limit=(0.03/TICK).round() as u64;let mut proposal=if args.len()==5 {args[4].parse()?} else {2*maximum};if proposal<8||proposal>2*maximum||!proposal.is_power_of_two()||elapsed>=limit {return Err("checkpoint clock/proposal".into());}
 let mut w=BufWriter::new(std::io::stdout().lock());let cur=fine::observed_currents(old,old,TICK*4.).map_err(|e|format!("startup currents:{e:?}"))?;
 let panel=(old.high[46]-old.high[39])/12500.;
 for v in [elapsed as f64,0.,0.,0.,0.,0.].into_iter().chain(old.high).chain(old.low).chain(old.high).chain(old.low).chain(cur).chain([panel]) {w.write_all(&v.to_le_bytes())?;}
 while elapsed<limit {
  if steps>=400000 {w.flush()?;return Err(format!("ENDPOINT_BUDGET,elapsed={elapsed},steps={steps}").into());}
  let mut ticks=proposal;while ticks as u64>limit-elapsed {ticks/=2;}
  let mut accepted=None;let mut reason=String::new();
  for attempts in 1..=20 {
   let trial=(|| {let full=radau::step(c,old,ticks as f64*TICK)?;let mid=radau::step(c,old,(ticks/2) as f64*TICK)?;let end=radau::step(c,mid.endpoint.candidate,(ticks/2) as f64*TICK)?;let difference=full.endpoint.candidate.difference(end.endpoint.candidate);let error=(0..N).fold(0_f64,|a,k|a.max(difference[k].abs()/if k<98 {2e-6} else {2e-9}));Ok::<_,vco1_newton::Error>((mid,end,error))})();
   match trial {Ok((mid,end,error))=>{if error<=1. {accepted=Some((mid,end,error,attempts));break;}reason=format!("LTE,{error:.17e}");},Err(e)=>reason=format!("nonlinear:{e:?}")}
   if ticks<=8 {w.flush()?;return Err(format!("elapsed={elapsed},dt_ticks={ticks},time_s={:.17e},{reason}",elapsed as f64*TICK).into());}ticks/=2;
  }
  let (mid,end,error,attempts)=accepted.ok_or(format!("attempt limit:{reason}"))?;proposal=if error<=0.25 {(ticks*2).min(2*maximum)} else {ticks};
  elapsed+= (ticks/2) as u64;emit(&mut w,elapsed,ticks/2,&mid,old,error,attempts)?;
  elapsed+= (ticks/2) as u64;emit(&mut w,elapsed,ticks/2,&end,mid.endpoint.candidate,error,attempts)?;
  old=end.endpoint.candidate;steps+=2;
  if steps%10000==0 {eprintln!("PROGRESS,steps={steps},time_s={:.9e}",elapsed as f64*TICK);}
 }
 w.flush()?;eprintln!("COMPLETE,steps={steps},ticks={elapsed}");Ok(())
}
