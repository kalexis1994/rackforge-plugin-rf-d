//! Frozen two-step reset histories and nonlinear event observations.
use rf_d_circuit::{joint_voice as j,chain_charge::Parameters as Chain,mixer_on::OnMixer,vco1_stamp::Controls};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
mod joint_history_tangent;
mod joint_history_propagation;
mod joint_history_event;
use joint_history_propagation::{COLS,R,Sensitivity};
use std::{fs::File,io::{Read,Write,BufWriter},path::Path,time::Instant};
const TICK:f64=125e-9/65536.;
const OBS:[usize;7]=[43,46,54,44,12,39,194];
fn scene()->j::Parameters {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let p=Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
 j::Parameters::new(Controls::default(),p,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap()
}
fn get<const N:usize>(r:&mut impl Read)->[u8;N] {let mut b=[0;N];r.read_exact(&mut b).unwrap();b}
fn u32(r:&mut impl Read)->u32 {u32::from_le_bytes(get(r))}
fn u64(r:&mut impl Read)->u64 {u64::from_le_bytes(get(r))}
fn f64(r:&mut impl Read)->f64 {let v=f64::from_le_bytes(get(r));assert!(v.is_finite());v}
fn state(r:&mut impl Read)->j::State {j::State{high:std::array::from_fn(|_|f64(r)),low:std::array::from_fn(|_|f64(r))}}
fn put(w:&mut impl Write,v:impl IntoIterator<Item=f64>) {for x in v {assert!(x.is_finite());w.write_all(&x.to_le_bytes()).unwrap();}}
fn put_state(w:&mut impl Write,s:j::State) {put(w,s.high);put(w,s.low);}
fn shifted(s:j::State,k:usize,e:f64)->j::State {s.advanced(std::array::from_fn(|i|if i==k {e} else {0.}))}
fn run(input:&Path,output:&Path)->Result<(),String> {
 let p=scene();let start=Instant::now();let guard=||->Result<(),String>{if start.elapsed().as_secs_f64()>300.||output.parent().unwrap().join("stop.flag").exists(){Err("ADMINISTRATIVE_BUDGET".into())}else{Ok(())}};
 let mut r=File::open(input).map_err(|e|e.to_string())?;assert_eq!(get::<8>(&mut r),*b"RFJHEIN1");assert_eq!(u32(&mut r),8);
 let mut w=BufWriter::new(File::create_new(output).map_err(|e|e.to_string())?);w.write_all(b"RFJHEVT1").unwrap();w.write_all(&8u32.to_le_bytes()).unwrap();
 for eid in 0..8 {
  guard()?;let metadata:[u32;4]=std::array::from_fn(|_|u32(&mut r));assert_eq!(metadata[0],eid);let start_ticks=u64(&mut r);let epsilon:[f64;R]=std::array::from_fn(|_|f64(&mut r));let initial=state(&mut r);
  let fixtures:[[j::State;5];2]=std::array::from_fn(|_|std::array::from_fn(|_|state(&mut r)));let clocks:[(u64,u32,[f64;7]);2]=std::array::from_fn(|_|{let t=u64(&mut r);let h=u32(&mut r);(t,h,std::array::from_fn(|_|f64(&mut r)))});
  for v in metadata {w.write_all(&v.to_le_bytes()).unwrap();}w.write_all(&start_ticks.to_le_bytes()).unwrap();put(&mut w,epsilon);
  let mut x=initial;let mut u=std::array::from_fn(|k|std::array::from_fn(|r|if k==COLS[r] {1.} else {0.}));let mut responses=Vec::new();let mut ends=Vec::new();let mut last=start_ticks;
  for n in 0..2 {
   let(ticks,half,obs)=clocks[n];assert_eq!(ticks-last,half as u64);last=ticks;let h=half as f64*TICK;let pair=j::step(p,x,h).map_err(|e|format!("BASE,{eid},{n},{e:?}"))?;
   let states=[x,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]];if states!=fixtures[n] {return Err(format!("BASE_BITS,{eid},{n}"));}
   for (a,k) in OBS.into_iter().enumerate(){if (pair.candidates[1].high[k]+pair.candidates[1].low[k]).to_bits()!=obs[a].to_bits(){return Err(format!("OBS_BITS,{eid},{n},{k}"));}}
   let s=joint_history_propagation::propagate(p,x,pair.increments,h,u).map_err(|e|format!("PROPAGATE,{eid},{n},{e:?}"))?;u=std::array::from_fn(|k|s[j::N+k]);x=pair.candidates[1];ends.push(x);responses.push(s);
   w.write_all(&ticks.to_le_bytes()).unwrap();w.write_all(&half.to_le_bytes()).unwrap();for state in states {put_state(&mut w,state);}put(&mut w,s.into_iter().flatten());
  }
  let h=clocks[1].1 as f64*TICK;let event=joint_history_event::crossing(ends[0],ends[1],h,responses[0],responses[1]);assert_eq!(event.dalpha[8],0.);assert_eq!(event.dt[8],0.);for k in 0..j::N {assert_eq!(event.response[k][8],0.);}
  put(&mut w,[event.alpha]);put_state(&mut w,event.state);put(&mut w,event.dalpha);put(&mut w,event.dt);put(&mut w,event.response.into_iter().flatten());
  for (direction,col) in COLS.into_iter().enumerate(){for scale in [1.,0.5]{for sign in [1.,-1.]{
   guard()?;let mut own=shifted(initial,col,sign*scale*epsilon[direction]);let mut own_ends=Vec::new();
   for n in 0..2{let pair=j::step(p,own,clocks[n].1 as f64*TICK).map_err(|e|format!("OWN,{eid},{col},{scale},{sign},{n},{e:?}"))?;own=pair.candidates[1];own_ends.push(own);}
   let zero:Sensitivity=[[0.;R];j::M];let own_event=joint_history_event::crossing(own_ends[0],own_ends[1],h,zero,zero);put(&mut w,[own_event.alpha]);for s in [own_ends[0],own_ends[1],own_event.state]{put_state(&mut w,s);}
  }}}
  w.flush().unwrap();eprintln!("HISTORY_EVENT,{eid},wall_s={:.3}",start.elapsed().as_secs_f64());
 }
 assert_eq!(r.read(&mut [0]).unwrap(),0);w.flush().unwrap();Ok(())
}
fn main(){let a:Vec<String>=std::env::args().collect();if let Err(e)=run(Path::new(&a[1]),Path::new(&a[2])){eprintln!("ERROR,{e}");std::process::exit(1);}}
