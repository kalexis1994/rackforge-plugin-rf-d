//! Laboratory exporter: disk I/O is outside the solver, not an audio callback.
use rf_d_circuit::{vco1_stamp::{Controls,C4,Memory,N},vco1_newton::Solution,vco1_adaptive,vco1_startup,vco_bjt::{self,Polarity},vco_jfet};
use std::io::{BufWriter,Write};
fn emit(w:&mut impl Write,t:f64,p:&Solution,old:Option<([f64;N],f64)>)->std::io::Result<()> {
 let x=p.nodes;
 let qa=[x[43],x[33],x[18],0.];let q10=[x[43],x[21],0.,0.];let j=[x[5],x[43],x[4]];
 let (ia,ib,ij)=if let Some((o,dt))=old {
  ({let q=vco_bjt::companion(Polarity::Npn,qa,[o[43],o[33],o[18],0.],125e-9).unwrap();q.candidate.current_a[0]-q.delta_charge_c[1]/dt},
   {let q=vco_bjt::companion(Polarity::Pnp,q10,[o[43],o[21],0.,0.],125e-9).unwrap();q.candidate.current_a[0]+q.delta_charge_c[1]/dt},
   {let q=vco_jfet::companion(j,[o[5],o[43],o[4]],125e-9).unwrap();q.candidate.current_a[1]+q.delta_charge_c[0]/dt+q.delta_charge_c[1]/dt})
 } else {(vco_bjt::evaluate(Polarity::Npn,qa).unwrap().current_a[0],vco_bjt::evaluate(Polarity::Pnp,q10).unwrap().current_a[0],vco_jfet::evaluate(j).unwrap().current_a[1])};
 for v in std::iter::once(t).chain(x).chain([ia,ib,ij,(x[46]-x[39])/12500.,p.residual_ratio,p.correction_ratio,p.iterations as f64,p.trials as f64]) {w.write_all(&v.to_le_bytes())?;}Ok(())
}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let args:Vec<String>=std::env::args().collect();if args.len()!=5 {return Err("arguments: dt_ns c4_pf output duration_ms".into());}
 let ns:u32=args[1].parse()?;if ![125,250,500].contains(&ns) {return Err("fixed step bank".into());}
 let dt=ns as f64*1e-9;let pf:u32=args[2].parse()?;let mut c=Controls::default();c.c4=match pf {10=>C4::Schematic10Pf,100=>C4::Bom100Pf,_=>return Err("C4".into())};
 let duration:f64=args[4].parse::<f64>()?*1e-3;if duration!=0.03 {return Err("fixed 30ms protocol".into());}
 let tick=vco1_adaptive::TICK_S;let limit=(duration/tick).round() as u32;let maximum=(dt/tick).round() as u32;let mut proposed=2*maximum;let mut elapsed=0_u32;let mut steps=0;let mut error=0_f64;let mut retries=0_u32;let start=std::time::Instant::now();
 let mut w=BufWriter::new(std::fs::File::create(&args[3])?);
 let initial=vco1_startup::startup(c).map_err(|e|format!("startup: {e:?}"))?;emit(&mut w,0.,&initial,None)?;let mut x=initial.nodes;let mut mi=0;let mut mt=0;
 while elapsed<limit {
  let p=match vco1_adaptive::advance(c,Memory{state:x},proposed,maximum,limit-elapsed) {Ok(p)=>p,Err(e)=>{w.flush()?;return Err(format!("ticks={elapsed},time_s={:.17e},error={e:?}",elapsed as f64*tick).into());}};
  error=error.max(p.error_ratio);retries+=p.attempts-1;proposed=p.next_full_ticks;
  let h=p.half_ticks as f64*tick;
  elapsed+=p.half_ticks;emit(&mut w,elapsed as f64*tick,&p.midpoint,Some((x,h)))?;
  elapsed+=p.half_ticks;emit(&mut w,elapsed as f64*tick,&p.endpoint,Some((p.midpoint.nodes,h)))?;
  mi=mi.max(p.midpoint.iterations).max(p.endpoint.iterations);mt=mt.max(p.midpoint.trials).max(p.endpoint.trials);x=p.endpoint.nodes;steps+=2;
  if steps%40000==0 {w.flush()?;println!("progress C4={pf} max_half_ns={ns} accepted_steps={steps} time_s={}",elapsed as f64*tick);}
 }
 w.flush()?;println!("COMPLETE,steps={steps},retries={retries},max_error_ratio={error},max_iterations={mi},max_trials={mt},wall_s={:.6}",start.elapsed().as_secs_f64());Ok(())
}
