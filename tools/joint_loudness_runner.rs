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
fn run()->Result<(),String> {
 let args:Vec<_>=std::env::args().collect();let bytes=fs::read(&args[1]).map_err(|e|e.to_string())?;if bytes.len()!=3224 {return Err("seed length".into());}
 let seed=joint::State{high:std::array::from_fn(|k|if k<200 {f64::from_le_bytes(bytes[24+8*k..32+8*k].try_into().unwrap())} else {0.}),low:std::array::from_fn(|k|if k<200 {f64::from_le_bytes(bytes[1624+8*k..1632+8*k].try_into().unwrap())} else {0.})};
 let mut w=std::io::BufWriter::new(fs::File::create(&args[2]).map_err(|e|e.to_string())?);let t=Instant::now();
 for c2 in [0.8469345758149237,3.2,6.] {for reset in [0.01,0.7] {for h in [125e-9,62.5e-9] {
  let mut p=scene();p.c2_v=c2;p.reset_v=reset;let mut old=seed;
  let base=c2-0.02;let mid=base-0.55;let out=base-1.2;let feedback=((out/6800.-10./16900.)/(1./6800.+1./16900.)).min(reset+0.4);
  let b=follower::Boundary{c2_v:c2,reset_base_v:reset,supply_v:9.3,load_conductance_s:1./68000.,load_reference_v:seed.high[165]+seed.low[165]};
  let prepared=follower::solve_port([base,mid,9.05,out,feedback],follower::Parameters::default(),b,SolverBudget{iterations:32,line_search_halvings:24}).map_err(|e|format!("prepare,{c2},{reset},{h}:{e:?}"))?;
  old.high[200..].copy_from_slice(&prepared.node_v);let initial=old;let count=if h==125e-9 {16} else {32};
  writeln!(w,"PROFILE,{c2:.17e},{reset:.17e},{h:.17e},{count}").unwrap();write_state(&mut w,initial);
  for k in 0..count {
   if t.elapsed().as_secs_f64()>300. {return Err("wall budget".into());}
   let pair=joint::step(p,old,h).map_err(|e|format!("step,{c2},{reset},{h},{k}:{e:?}"))?;
   if k==0 {let replay=joint::step(p,old,h).map_err(|e|format!("restore:{e:?}"))?;if !same(&pair,&replay) {return Err("first step bit replay".into());}}
   if k==0||k+1==count {
    writeln!(w,"JOINT_ROOT,0,{h:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio).unwrap();
    for s in [old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]] {write_state(&mut w,s);}
   }
   old=pair.candidates[1];
   let v=|i|old.high[i]+old.low[i];let fp=follower::Parameters::default();let nvt=fp.diode_ideality*1.380649e-23*fp.temperature_k/1.602176634e-19;
   writeln!(w,"OBS,{k},{:.17e},{:.17e},{:.17e},{:.17e},{:.17e},{:.17e}",v(203),v(194),(c2-v(200))/10000.,-fp.germanium_is_a*((v(204)-reset)/nvt).exp_m1(),(v(203)-v(165))/68000.,pair.residual_ratio).unwrap();
  }
  writeln!(w,"FINAL").unwrap();write_state(&mut w,old);
 }}}
 w.flush().map_err(|e|e.to_string())?;eprintln!("COMPLETED,profiles=12,steps=288,bit_replays=12,wall_s={}",t.elapsed().as_secs_f64());Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
