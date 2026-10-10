//! IO only in the laboratory caller; frozen physical library.
use rf_d_circuit::{joint_voice as j,chain_charge::Parameters as Chain,mixer_on::OnMixer,vco1_stamp::Controls,joint_engine};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
mod joint_history_tangent;
use std::{fs::{self,File},io::{Write,BufWriter},path::Path,time::Instant};
const COLS:[usize;9]=[43,5,12,139,199,194,157,117,98];
fn scene()->j::Parameters {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let p=Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
 j::Parameters::new(Controls::default(),p,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap()
}
fn state(line:&str)->j::State {
 let v:Vec<f64>=line.split(',').skip(1).map(|v|v.parse().unwrap()).collect();assert_eq!(v.len(),400);
 j::State{high:std::array::from_fn(|k|v[k]),low:std::array::from_fn(|k|v[k+200])}
}
fn shifted(s:j::State,k:usize,v:f64)->j::State {s.advanced(std::array::from_fn(|i|if i==k {v} else {0.}))}
fn eps(k:usize)->f64 {if (98..133).contains(&k) {1e-8} else {1e-5}}
fn put(w:&mut impl Write,values:impl IntoIterator<Item=f64>) {for v in values {assert!(v.is_finite());w.write_all(&v.to_le_bytes()).unwrap();}}
fn ds(a:j::State,b:j::State)->[f64;200] {joint_engine::difference(a,b)}
fn run(inputs:&Path,output:&Path)->Result<(),String> {
 let p=scene();let paths=fs::read_to_string(inputs).map_err(|e|e.to_string())?;let mut cases=Vec::new();
 for path in paths.lines() {let lines:Vec<String>=fs::read_to_string(path).map_err(|e|e.to_string())?.lines().map(str::to_owned).collect();
  for i in 0..lines.len() {if lines[i].starts_with("JOINT_ROOT,") {let f:Vec<&str>=lines[i].split(',').collect();assert_eq!(f[1],"0");let h:f64=f[2].parse().unwrap();let states:[j::State;5]=std::array::from_fn(|k|state(&lines[i+1+k]));cases.push((h,states));}}
 }
 assert_eq!(cases.len(),48);let mut w=BufWriter::new(File::create_new(output).map_err(|e|e.to_string())?);w.write_all(b"RFJHIST2").unwrap();w.write_all(&48u32.to_le_bytes()).unwrap();let start=Instant::now();
 let guard=||->Result<(),String> {if start.elapsed().as_secs_f64()>600.||output.parent().unwrap().join("stop.flag").exists() {Err("ADMINISTRATIVE_BUDGET".into())} else {Ok(())}};
 for (id,(h,s)) in cases.into_iter().enumerate() {
  guard()?;let x=s[0];let d=[s[1],s[2]];let original=j::step(p,x,h).map_err(|e|format!("BASE,{id},{e:?}"))?;
  if original.increments!=d||original.candidates!=[s[3],s[4]] {return Err(format!("BASE_BITS,{id}"));}
  let m=joint_history_tangent::old_mass(p,x,h).map_err(|e|format!("MASS,{id},{e:?}"))?;
  w.write_all(&(id as u32).to_le_bytes()).unwrap();put(&mut w,[h]);put(&mut w,m.into_iter().flatten());
  let mut leak=0_f64;
  for scale in [1.,0.5] {
   for col in 0..200 {
    if col%20==0 {guard()?;}
    let e=eps(col)*scale;let mut r=[[0.;400];2];
    for (n,sign) in [1.,-1.].into_iter().enumerate() {
     let xx=shifted(x,col,sign*e);let dd=d.map(|a|shifted(a,col,-sign*e));
     let stamp=j::linearize(p,xx,dd,h).map_err(|err|format!("FD,{id},{col},{sign},{err:?}"))?;r[n]=stamp.residual;
     for stage in 0..2 {for v in ds(stamp.candidates[stage],s[3+stage]) {leak=leak.max(v.abs()/e);}}
    }
    put(&mut w,(0..400).map(|k|(r[0][k]-r[1][k])/(2.*e)));
   }
  }
  put(&mut w,[leak]);
  for col in COLS {
   guard()?;let tangent=joint_history_tangent::response(p,x,d,h,&m,col).map_err(|e|format!("TANGENT,{id},{col},{e:?}"))?;
   let base=if (98..133).contains(&col) {1e-10} else {eps(col)};
   let gain=(0..400).fold(1_f64,|a,k|a.max(base*tangent[k].abs()/if (98..133).contains(&(k%200)) {1e-8} else {1e-5}));let epsilon=base/gain;
   w.write_all(&(col as u32).to_le_bytes()).unwrap();put(&mut w,[epsilon]);put(&mut w,tangent);
   for scale in [1.,0.5] {
    let e=epsilon*scale;let a=j::step(p,shifted(x,col,e),h).map_err(|e|format!("STEP_PLUS,{id},{col},{e:?}"))?;let b=j::step(p,shifted(x,col,-e),h).map_err(|e|format!("STEP_MINUS,{id},{col},{e:?}"))?;
    for stage in 0..2 {put(&mut w,ds(a.candidates[stage],b.candidates[stage]).map(|v|v/(2.*e)));}
   }
  }
  w.flush().unwrap();eprintln!("HISTORY_CASE,{id},h={h:.17e},leak={leak:.17e},wall_s={:.3}",start.elapsed().as_secs_f64());
 }
 w.flush().unwrap();Ok(())
}
fn main() {let args:Vec<String>=std::env::args().collect();if let Err(e)=run(Path::new(&args[1]),Path::new(&args[2])) {eprintln!("ERROR,{e}");std::process::exit(1);}}
