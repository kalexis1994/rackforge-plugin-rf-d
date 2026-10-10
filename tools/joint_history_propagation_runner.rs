//! Fixed calendars and nonlinear own histories; IO only in laboratory.
use rf_d_circuit::{joint_voice as j,chain_charge::Parameters as Chain,mixer_on::OnMixer,vco1_stamp::Controls,joint_engine};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
mod joint_history_tangent;
mod joint_history_propagation;
use joint_history_propagation::{COLS,R,Sensitivity};
use std::{fs::{self,File},io::{Read,Write,BufWriter},path::Path,time::Instant};
const COUNT:usize=64;
const TICK:f64=125e-9/65536.;
const OBS:[usize;7]=[43,46,54,44,12,39,194];
fn scene()->j::Parameters {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let p=Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
 j::Parameters::new(Controls::default(),p,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap()
}
fn put(w:&mut impl Write,v:impl IntoIterator<Item=f64>) {for x in v {assert!(x.is_finite());w.write_all(&x.to_le_bytes()).unwrap();}}
fn put_state(w:&mut impl Write,s:j::State) {put(w,s.high);put(w,s.low);}
fn get<const N:usize>(r:&mut impl Read)->[u8;N] {let mut b=[0;N];r.read_exact(&mut b).unwrap();b}
fn u32(r:&mut impl Read)->u32 {u32::from_le_bytes(get(r))}
fn u64(r:&mut impl Read)->u64 {u64::from_le_bytes(get(r))}
fn f64(r:&mut impl Read)->f64 {let v=f64::from_le_bytes(get(r));assert!(v.is_finite());v}
fn get_state(r:&mut impl Read)->j::State {j::State{high:std::array::from_fn(|_|f64(r)),low:std::array::from_fn(|_|f64(r))}}
fn shifted(s:j::State,k:usize,e:f64)->j::State {s.advanced(std::array::from_fn(|i|if i==k {e} else {0.}))}
fn state(line:&str)->j::State {let v:Vec<f64>=line.split(',').skip(1).map(|v|v.parse().unwrap()).collect();assert_eq!(v.len(),400);j::State{high:std::array::from_fn(|k|v[k]),low:std::array::from_fn(|k|v[k+200])}}
struct Record {ticks:u64,half:u32,states:[j::State;5],s:Sensitivity}
fn run(inputs:&Path,selected:&Path,output:&Path)->Result<(),String> {
 let p=scene();let start=Instant::now();
 let guard=||->Result<(),String> {if start.elapsed().as_secs_f64()>900.||output.parent().unwrap().join("stop.flag").exists() {Err("ADMINISTRATIVE_BUDGET".into())} else {Ok(())}};
 let mut w=BufWriter::new(File::create_new(output).map_err(|e|e.to_string())?);w.write_all(b"RFJHPRO1").unwrap();w.write_all(&48u32.to_le_bytes()).unwrap();
 let mut case=0;
 for path in fs::read_to_string(selected).map_err(|e|e.to_string())?.lines() {
  let text=fs::read_to_string(path).map_err(|e|e.to_string())?;let lines:Vec<&str>=text.lines().collect();
  for i in 0..lines.len() {if !lines[i].starts_with("JOINT_ROOT,") {continue;}guard()?;
   let h:f64=lines[i].split(',').nth(2).unwrap().parse().unwrap();let s:[j::State;5]=std::array::from_fn(|k|state(lines[i+1+k]));
   let many=joint_history_propagation::units(p,s[0],[s[1],s[2]],h).map_err(|e|format!("BATCH,{case},{e:?}"))?;
   let m=joint_history_tangent::old_mass(p,s[0],h).map_err(|e|format!("MASS,{case},{e:?}"))?;
   for (r,col) in COLS.into_iter().enumerate() {let one=joint_history_tangent::response(p,s[0],[s[1],s[2]],h,&m,col).map_err(|e|format!("SCALAR,{case},{col},{e:?}"))?;for k in 0..j::M {if one[k].to_bits()!=many[k][r].to_bits() {return Err(format!("BATCH_BITS,{case},{col},{k}"));}}}
   w.write_all(&(case as u32).to_le_bytes()).unwrap();put(&mut w,many.into_iter().flatten());case+=1;
  }
 }assert_eq!(case,48);w.flush().unwrap();
 let mut input=File::open(inputs).map_err(|e|e.to_string())?;assert_eq!(get::<8>(&mut input),*b"RFJHPIN1");assert_eq!(u32(&mut input),12);assert_eq!(u32(&mut input),COUNT as u32);w.write_all(&12u32.to_le_bytes()).unwrap();w.write_all(&(COUNT as u32).to_le_bytes()).unwrap();
 for wid in 0..12 {
  guard()?;assert_eq!(u32(&mut input),wid);let profile=u32(&mut input);let location=u32(&mut input);let start_ticks=u64(&mut input);let initial=get_state(&mut input);
  let fixtures:[[j::State;5];2]=std::array::from_fn(|_|std::array::from_fn(|_|get_state(&mut input)));
  let clocks:Vec<(u64,u32,[f64;7])>=(0..COUNT).map(|_|{let t=u64(&mut input);let h=u32(&mut input);(t,h,std::array::from_fn(|_|f64(&mut input)))}).collect();
  let mut x=initial;let mut u=std::array::from_fn(|k|std::array::from_fn(|r|if k==COLS[r] {1.} else {0.}));let mut records=Vec::new();let mut last=start_ticks;let mut gain=[1_f64;R];
  for (n,(ticks,half,obs)) in clocks.into_iter().enumerate() {
   guard()?;assert_eq!(ticks-last,half as u64);last=ticks;let h=half as f64*TICK;
   let pair=j::step(p,x,h).map_err(|e|format!("BASE,{wid},{n},{e:?}"))?;let states=[x,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]];
   if n<2 && states!=fixtures[n] {return Err(format!("SEAM_BITS,{wid},{n}"));}
   for (a,k) in OBS.into_iter().enumerate() {if (pair.candidates[1].high[k]+pair.candidates[1].low[k]).to_bits()!=obs[a].to_bits() {return Err(format!("TRACE_BITS,{wid},{n},{k}"));}}
   let s=joint_history_propagation::propagate(p,x,pair.increments,h,u).map_err(|e|format!("PROPAGATE,{wid},{n},{e:?}"))?;
   for k in 0..j::M {assert_eq!(s[k][8],0.);for r in 0..R {let base=if (98..133).contains(&COLS[r]) {1e-10} else {1e-5};let target=if (98..133).contains(&(k%j::N)) {1e-8} else {1e-5};gain[r]=gain[r].max(base*s[k][r].abs()/target);}}
   u=std::array::from_fn(|k|s[j::N+k]);x=pair.candidates[1];records.push(Record{ticks,half,states,s});
  }
  let epsilon:[f64;R]=std::array::from_fn(|r|if (98..133).contains(&COLS[r]) {1e-10/gain[r]} else {1e-5/gain[r]});
  for v in [wid,profile,location] {w.write_all(&v.to_le_bytes()).unwrap();}w.write_all(&start_ticks.to_le_bytes()).unwrap();put(&mut w,epsilon);
  let mut own:Vec<[[j::State;2];2]>=COLS.into_iter().enumerate().map(|(r,col)|std::array::from_fn(|scale|std::array::from_fn(|sign|shifted(initial,col,epsilon[r]*[1.,0.5][scale]*[1.,-1.][sign])))).collect();
  for (n,rec) in records.into_iter().enumerate() {
   guard()?;w.write_all(&rec.ticks.to_le_bytes()).unwrap();w.write_all(&rec.half.to_le_bytes()).unwrap();for state in rec.states {put_state(&mut w,state);}put(&mut w,rec.s.into_iter().flatten());
   for r in 0..R {for scale in 0..2 {
    let h=rec.half as f64*TICK;let mut candidates=[[initial;2];2];
    for sign in 0..2 {let pair=j::step(p,own[r][scale][sign],h).map_err(|e|format!("OWN,{wid},{n},{},{scale},{sign},{e:?}",COLS[r]))?;candidates[sign]=pair.candidates;own[r][scale][sign]=pair.candidates[1];}
    let e=epsilon[r]*[1.,0.5][scale];for stage in 0..2 {put(&mut w,joint_engine::difference(candidates[0][stage],candidates[1][stage]).map(|v|v/(2.*e)));}
   }}w.flush().unwrap();
  }
  eprintln!("PROPAGATION_WINDOW,{wid},wall_s={:.3}",start.elapsed().as_secs_f64());
 }
 assert_eq!(input.read(&mut [0]).unwrap(),0);w.flush().unwrap();Ok(())
}
fn main() {let a:Vec<String>=std::env::args().collect();if let Err(e)=run(Path::new(&a[1]),Path::new(&a[2]),Path::new(&a[3])) {eprintln!("ERROR,{e}");std::process::exit(1);}}
