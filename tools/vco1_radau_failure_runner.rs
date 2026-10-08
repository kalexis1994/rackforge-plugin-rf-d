use rf_d_circuit::{vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton};
#[path="linear.rs"] mod output_conversion;
#[path="fine.rs"] mod fine;
#[path="radau.rs"] mod radau;
use vco1_stamp::{Controls,N};use fine::State;
const TICK:f64=125e-9/65536.;
fn report(label:&str,p:&radau::Pair){for (part,s) in [("stage",&p.stage),("endpoint",&p.endpoint)] {print!("ROOT,{label},{part},{:.17e},{:.17e}",s.residual_ratio,s.correction_ratio);for v in s.candidate.high.into_iter().chain(s.candidate.low) {print!(",{v:.17e}");}println!();}}
fn main()->Result<(),Box<dyn std::error::Error>> {let c=Controls::default();let content=std::fs::read_to_string(std::env::args().nth(1).ok_or("checkpoint")?)?;let a:Vec<f64>=content.split_whitespace().map(str::parse).collect::<Result<_,_>>()?;let old=State{high:a[..N].try_into()?,low:a[N..].try_into()?};
 for ticks in [8,16,32] {let h=ticks as f64*TICK/2.;
 match radau::step(c,old,2.*h){Ok(p)=>report(&format!("{ticks}/full"),&p),Err(e)=>println!("REJECT,{ticks}/full,{e:?}")}
 match radau::step(c,old,h){Ok(mid)=>{report(&format!("{ticks}/mid"),&mid);match radau::step(c,mid.endpoint.candidate,h){Ok(end)=>report(&format!("{ticks}/end"),&end),Err(e)=>println!("REJECT,{ticks}/end,{e:?}")}},Err(e)=>println!("REJECT,{ticks}/mid,{e:?}")}
 }Ok(())}
