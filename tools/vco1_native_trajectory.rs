//! Laboratory exporter: disk I/O is outside the solver, not an audio callback.
use rf_d_circuit::{vco1_stamp::{Controls,C4,Memory,Mode,N},vco1_newton::{self,Boundary,Budget,Solution},vco1_startup,vco_bjt::{self,Polarity},vco_jfet};
use std::io::{BufWriter,Write};
fn emit(w:&mut impl Write,t:f64,p:&Solution,old:Option<([f64;N],f64)>)->std::io::Result<()> {
 let x=p.nodes;
 let qa=[x[43],x[33],x[18],0.];let q10=[x[43],x[21],0.,0.];let j=[x[5],x[43],x[4]];
 let (ia,ib,ij)=if let Some((o,dt))=old {
  (vco_bjt::companion(Polarity::Npn,qa,[o[43],o[33],o[18],0.],dt).unwrap().current_a[0],
   vco_bjt::companion(Polarity::Pnp,q10,[o[43],o[21],0.,0.],dt).unwrap().current_a[0],
   vco_jfet::companion(j,[o[5],o[43],o[4]],dt).unwrap().current_a[1])
 } else {(vco_bjt::evaluate(Polarity::Npn,qa).unwrap().current_a[0],vco_bjt::evaluate(Polarity::Pnp,q10).unwrap().current_a[0],vco_jfet::evaluate(j).unwrap().current_a[1])};
 for v in std::iter::once(t).chain(x).chain([ia,ib,ij,(x[46]-x[39])/12500.,p.residual_ratio,p.correction_ratio,p.iterations as f64,p.trials as f64]) {w.write_all(&v.to_le_bytes())?;}Ok(())
}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let args:Vec<String>=std::env::args().collect();if args.len()!=5 {return Err("arguments: dt_ns c4_pf output duration_ms".into());}
 let ns:u32=args[1].parse()?;if ![125,250,500].contains(&ns) {return Err("fixed step bank".into());}
 let dt=ns as f64*1e-9;let pf:u32=args[2].parse()?;let mut c=Controls::default();c.c4=match pf {10=>C4::Schematic10Pf,100=>C4::Bom100Pf,_=>return Err("C4".into())};
 let duration:f64=args[4].parse::<f64>()?*1e-3;if duration!=0.03 {return Err("fixed 30ms protocol".into());}
 let steps=(duration/dt).round() as usize;let start=std::time::Instant::now();
 let mut w=BufWriter::new(std::fs::File::create(&args[3])?);
 let initial=vco1_startup::startup(c).map_err(|e|format!("startup: {e:?}"))?;emit(&mut w,0.,&initial,None)?;let mut x=initial.nodes;let mut mi=0;let mut mt=0;
 for k in 1..=steps {
  let p=match vco1_newton::solve(c,Mode::Euler{dt_s:dt,previous:Memory{state:x}},Boundary::Free,x,Budget::default()) {Ok(p)=>p,Err(e)=>{w.flush()?;return Err(format!("step={k},time_s={:.17e},error={e:?}",k as f64*dt).into());}};
  emit(&mut w,k as f64*dt,&p,Some((x,dt)))?;mi=mi.max(p.iterations);mt=mt.max(p.trials);x=p.nodes;
  if k%40000==0 {w.flush()?;println!("progress C4={pf} dt_ns={ns} step={k}/{steps}");}
 }
 w.flush()?;println!("COMPLETE,steps={steps},max_iterations={mi},max_trials={mt},wall_s={:.6}",start.elapsed().as_secs_f64());Ok(())
}
