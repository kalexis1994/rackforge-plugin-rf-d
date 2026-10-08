//! Complete lab export with high/low state, actual delta and integer interval ticks.
use rf_d_circuit::{vco1_stamp::{Controls,C4,N},vco1_increment::{self,State},vco1_increment_adaptive as adaptive,vco1_startup};
use std::io::{BufWriter,Write};
fn emit(w:&mut impl Write,t:f64,now:State,old:State,delta:[f64;N],ticks:u32,res:f64,corr:f64,it:usize,trials:usize)->std::io::Result<()> {
 let dt=if ticks==0 {125e-9} else {ticks as f64*adaptive::TICK_S};let q=vco1_increment::observed_currents(now,old,dt).unwrap();
 let panel=(now.high[46]-now.high[39]+now.low[46]-now.low[39])/12500.;
 for v in std::iter::once(t).chain(now.high).chain(now.low).chain(delta).chain([q[0],q[1],q[2],panel,res,corr,it as f64,trials as f64,ticks as f64]) {w.write_all(&v.to_le_bytes())?;}Ok(())
}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let args:Vec<String>=std::env::args().collect();if args.len()!=5 {return Err("arguments: maximum_half_ns c4_pf output duration_ms".into());}
 let ns:u32=args[1].parse()?;if ![125,250,500].contains(&ns) {return Err("fixed maximum step bank".into());}
 let pf:u32=args[2].parse()?;let mut c=Controls::default();c.c4=match pf {10=>C4::Schematic10Pf,100=>C4::Bom100Pf,_=>return Err("C4".into())};
 let duration:f64=args[4].parse::<f64>()?*1e-3;if duration!=0.03 {return Err("fixed 30ms protocol".into());}
 let tick=adaptive::TICK_S;let limit=(duration/tick).round() as u32;let maximum=(ns as f64*1e-9/tick).round() as u32;let mut proposed=2*maximum;let mut elapsed=0_u32;let mut steps=0;let mut error=0_f64;let mut retries=0_u32;let start=std::time::Instant::now();
 let mut w=BufWriter::new(std::fs::File::create(&args[3])?);
 let initial=vco1_startup::startup(c).map_err(|e|format!("startup: {e:?}"))?;let mut old=State::from_nodes(initial.nodes);emit(&mut w,0.,old,old,[0.;N],0,initial.residual_ratio,initial.correction_ratio,initial.iterations,initial.trials)?;let mut mi=0;let mut mt=0;
 while elapsed<limit {
  let p=match adaptive::advance(c,old,proposed,maximum,limit-elapsed) {Ok(p)=>p,Err(e)=>{w.flush()?;return Err(format!("ticks={elapsed},time_s={:.17e},proposed={proposed},error={e:?}",elapsed as f64*tick).into());}};
  error=error.max(p.error_ratio);retries+=p.attempts-1;proposed=p.next_full_ticks;
  elapsed+=p.half_ticks;emit(&mut w,elapsed as f64*tick,p.midpoint.candidate,old,p.midpoint.delta,p.half_ticks,p.midpoint.residual_ratio,p.midpoint.correction_ratio,p.midpoint.iterations,p.midpoint.trials)?;
  elapsed+=p.half_ticks;emit(&mut w,elapsed as f64*tick,p.endpoint.candidate,p.midpoint.candidate,p.endpoint.delta,p.half_ticks,p.endpoint.residual_ratio,p.endpoint.correction_ratio,p.endpoint.iterations,p.endpoint.trials)?;
  mi=mi.max(p.midpoint.iterations).max(p.endpoint.iterations);mt=mt.max(p.midpoint.trials).max(p.endpoint.trials);old=p.endpoint.candidate;steps+=2;
  if steps%40000==0 {w.flush()?;println!("progress C4={pf} max_half_ns={ns} accepted_steps={steps} time_s={}",elapsed as f64*tick);}
 }
 w.flush()?;println!("COMPLETE,steps={steps},retries={retries},max_error_ratio={error},max_iterations={mi},max_trials={mt},wall_s={:.6}",start.elapsed().as_secs_f64());Ok(())
}
