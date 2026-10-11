//! One complete observed interval; compact IO and fixed saved calendars.
use rf_d_circuit::{joint_voice as j,chain_charge::Parameters as Chain,mixer_on::OnMixer,vco1_stamp::Controls,joint_engine};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
mod joint_history_tangent;
mod joint_history_propagation;
mod joint_history_event;
use joint_history_propagation::{R,COLS,Sensitivity};
use joint_history_event::Event;
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
fn put_event(w:&mut impl Write,e:&Event) {put(w,[e.alpha]);put_state(w,e.state);put(w,e.dalpha);put(w,e.dt);put(w,e.response.into_iter().flatten());}
fn shifted(s:j::State,k:usize,e:f64)->j::State {s.advanced(std::array::from_fn(|i|if i==k {e} else {0.}))}
fn failed(label:&str,x:j::State,h:f64,e:rf_d_circuit::StepError)->String {
 eprint!("FAILED_STEP,{label},{h:.17e}");for v in x.high.into_iter().chain(x.low){eprint!(",{v:.17e}");}eprintln!();format!("{label},{e:?}")
}
fn run(input:&Path,output:&Path)->Result<(),String> {
 let p=scene();let start=Instant::now();let guard=||->Result<(),String>{if start.elapsed().as_secs_f64()>2300.||output.parent().unwrap().join("stop.flag").exists(){Err("ADMINISTRATIVE_BUDGET".into())}else{Ok(())}};
 let mut r=File::open(input).map_err(|e|e.to_string())?;assert_eq!(get::<8>(&mut r),*b"RFJFINT1");let n=u32(&mut r) as usize;assert_eq!(n,22356);let start_ticks=u64(&mut r);let initial=state(&mut r);
 let fixtures:[[j::State;5];4]=std::array::from_fn(|_|std::array::from_fn(|_|state(&mut r)));let count=u32(&mut r);assert_eq!(count,15);let points:Vec<usize>=(0..count).map(|_|u32(&mut r) as usize).collect();
 let clocks:Vec<(u64,u32,[f64;7])>=(0..n).map(|_|{let t=u64(&mut r);let h=u32(&mut r);(t,h,std::array::from_fn(|_|f64(&mut r)))}).collect();assert_eq!(r.read(&mut [0]).unwrap(),0);
 let mut w=BufWriter::new(File::create_new(output).map_err(|e|e.to_string())?);w.write_all(b"RFJRET01").unwrap();w.write_all(&(n as u32).to_le_bytes()).unwrap();w.write_all(&start_ticks.to_le_bytes()).unwrap();
 let mut x=initial;let mut u=std::array::from_fn(|k|std::array::from_fn(|r|if k==COLS[r] {1.} else {0.}));let mut gain=[1_f64;R];let mut ends=[initial;4];let mut sensitivities=[[[0.;R];j::M];4];let mut last=start_ticks;
 for step in 0..n {
  guard()?;let(ticks,half,obs)=clocks[step];assert_eq!(ticks-last,half as u64);last=ticks;let h=half as f64*TICK;let pair=j::step(p,x,h).map_err(|e|failed(&format!("BASE,{step}"),x,h,e))?;
  let states=[x,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]];let fixture=if step<2 {Some(step)} else if step>=n-2 {Some(step-(n-2)+2)} else {None};
  if let Some(k)=fixture {if states!=fixtures[k] {return Err(format!("FIXTURE_BITS,{step}"));}}
  let observed=OBS.map(|k|pair.candidates[1].high[k]+pair.candidates[1].low[k]);for k in 0..7 {if observed[k].to_bits()!=obs[k].to_bits() {return Err(format!("TRACE_BITS,{step},{k}"));}}
  let s=joint_history_propagation::propagate(p,x,pair.increments,h,u).map_err(|e|failed(&format!("PROPAGATE,{step}"),x,h,e))?;
  for k in 0..j::M {assert_eq!(s[k][8],0.);for direction in 0..R {let base=if (98..133).contains(&COLS[direction]) {1e-10} else {1e-5};let target=if (98..133).contains(&(k%j::N)) {1e-8} else {1e-5};gain[direction]=gain[direction].max(base*s[k][direction].abs()/target);}}
  w.write_all(&(step as u32).to_le_bytes()).unwrap();w.write_all(&ticks.to_le_bytes()).unwrap();w.write_all(&half.to_le_bytes()).unwrap();put(&mut w,observed);let sample=points.contains(&step);w.write_all(&[sample as u8]).unwrap();
  if sample {for state in states {put_state(&mut w,state);}put(&mut w,u.into_iter().flatten());put(&mut w,s.into_iter().flatten());}
  if let Some(k)=fixture {ends[k]=pair.candidates[1];sensitivities[k]=s;}
  u=std::array::from_fn(|k|s[j::N+k]);x=pair.candidates[1];
  if step%1024==0||step+1==n {w.flush().unwrap();eprintln!("RETURN_BASE,{step},wall_s={:.3}",start.elapsed().as_secs_f64());}
 }
 let epsilon:[f64;R]=std::array::from_fn(|r|if (98..133).contains(&COLS[r]) {1e-10/gain[r]} else {1e-5/gain[r]});put(&mut w,gain);put(&mut w,epsilon);
 let h1=clocks[1].1 as f64*TICK;let h2=clocks[n-1].1 as f64*TICK;let first=joint_history_event::crossing(ends[0],ends[1],h1,sensitivities[0],sensitivities[1]);let second=joint_history_event::crossing(ends[2],ends[3],h2,sensitivities[2],sensitivities[3]);put_event(&mut w,&first);put_event(&mut w,&second);
 let fixed=(clocks[n-2].0-clocks[0].0) as f64*TICK;put(&mut w,[fixed+h2*second.alpha-h1*first.alpha]);put(&mut w,joint_engine::difference(second.state,first.state));put(&mut w,(0..R).map(|r|second.dt[r]-first.dt[r]));put(&mut w,(0..j::N).flat_map(|k|(0..R).map(move |r|second.response[k][r]-first.response[k][r])));w.flush().unwrap();
 for scale in [1.,0.5] {for sign in [1.,-1.] {
  put(&mut w,[scale,sign]);let mut own=shifted(initial,139,sign*scale*epsilon[3]);let mut own_ends=[initial;4];
  for step in 0..n {guard()?;let h=clocks[step].1 as f64*TICK;let pair=j::step(p,own,h).map_err(|e|failed(&format!("OWN,{scale},{sign},{step}"),own,h,e))?;own=pair.candidates[1];
   if step<2 {own_ends[step]=own;} else if step>=n-2 {own_ends[step-(n-2)+2]=own;}
   if step%2048==0||step+1==n {eprintln!("RETURN_OWN,{scale},{sign},{step},wall_s={:.3}",start.elapsed().as_secs_f64());}
  }
  let zero:Sensitivity=[[0.;R];j::M];let a=joint_history_event::crossing(own_ends[0],own_ends[1],h1,zero,zero);let b=joint_history_event::crossing(own_ends[2],own_ends[3],h2,zero,zero);
  for state in own_ends {put_state(&mut w,state);}put(&mut w,[a.alpha]);put_state(&mut w,a.state);put(&mut w,[b.alpha]);put_state(&mut w,b.state);put(&mut w,[fixed+h2*b.alpha-h1*a.alpha]);w.flush().unwrap();
 }}w.flush().unwrap();Ok(())
}
fn main(){let a:Vec<String>=std::env::args().collect();if let Err(e)=run(Path::new(&a[1]),Path::new(&a[2])){eprintln!("ERROR,{e}");std::process::exit(1);}}
