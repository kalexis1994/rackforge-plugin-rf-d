
mod joint_history_tangent;
mod joint_history_propagation;
mod joint_charge_basis_propagation;
use std::{fs::File,io::{Read,Write,BufWriter},path::Path,time::Instant};
const TICK:f64=125e-9/65536.;
fn get<const N:usize>(r:&mut impl Read)->[u8;N] {let mut b=[0;N];r.read_exact(&mut b).unwrap();b}
fn read_f(r:&mut impl Read)->f64 {let v=f64::from_le_bytes(get(r));assert!(v.is_finite());v}
fn read_state(r:&mut impl Read)->joint::State {joint::State{high:std::array::from_fn(|_|read_f(r)),low:std::array::from_fn(|_|read_f(r))}}
fn put(w:&mut impl Write,values:impl IntoIterator<Item=f64>) {for v in values {assert!(v.is_finite());w.write_all(&v.to_le_bytes()).unwrap();}}
fn put_state(w:&mut impl Write,s:joint::State) {put(w,s.high);put(w,s.low);}
fn put_root(w:&mut impl Write,z:Aug,m:[f64;5]) {put_state(w,z.x);put(w,(0..K).flat_map(|k|[z.i.high[k],z.i.low[k]]));put(w,m);}
fn root_bits(a:Aug,b:Aug)->bool {a.x.high.into_iter().chain(a.x.low).zip(b.x.high.into_iter().chain(b.x.low)).all(|(a,b)|a.to_bits()==b.to_bits())&&(0..K).all(|k|a.i.high[k].to_bits()==b.i.high[k].to_bits()&&a.i.low[k].to_bits()==b.i.low[k].to_bits())}
fn run()->Result<(),String> {
 let args:Vec<String>=std::env::args().collect();let output=Path::new(&args[2]);let started=Instant::now();
 let guard=||->Result<(),String>{if started.elapsed().as_secs_f64()>600.||output.parent().unwrap().join("stop.flag").exists(){Err("ADMINISTRATIVE_BUDGET".into())}else{Ok(())}};
 let(p,seed)=scene()?;let mut input=File::open(&args[1]).map_err(|e|e.to_string())?;assert_eq!(get::<8>(&mut input),*b"RFJCBIN1");let mut w=BufWriter::new(File::create_new(output).map_err(|e|e.to_string())?);w.write_all(b"RFJCBO01").unwrap();
 let rows:Vec<Vec<f64>>=include_str!("../evidence/voice_joint_charge_response_targets01.txt").lines().map(|l|l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect();assert_eq!(rows.len(),2);
 for id in 0..2 {
  guard()?;let mut expected=Aug{x:read_state(&mut input),i:joint::State::from_nodes([0.;200])};for k in 0..K {expected.i.high[k]=read_f(&mut input);expected.i.low[k]=read_f(&mut input);}
  let clocks:[(u64,u32,[joint::State;5]);2]=std::array::from_fn(|_|(u64::from_le_bytes(get(&mut input)),u32::from_le_bytes(get(&mut input)),std::array::from_fn(|_|read_state(&mut input))));
  let target=std::array::from_fn(|k|(rows[id][2*k],rows[id][2*k+1]));let(z,it,tr,res,corr,f)=condition(p,seed,target).map_err(|e|format!("base:{id}:{e:?}"))?;assert!(root_bits(z,expected));
  w.write_all(&(id as u32).to_le_bytes()).unwrap();put_root(&mut w,z,[it as f64,tr as f64,res,corr,f]);let(_,matrix,_)=system(p,z,target).map_err(|e|format!("matrix:{e:?}"))?;let mut basis=[[0.;K];M];
  for k in 0..K {let mut rhs=[0.;M];rhs[200+k]=1.;let b=solve(matrix,rhs).map_err(|e|format!("basis:{id}:{k}:{e:?}"))?;for row in 0..M {basis[row][k]=b[row];}}
  put(&mut w,basis.into_iter().flatten());let mut u=std::array::from_fn(|k|basis[k]);let mut x=z.x;let mut last=0;
  for step in 0..2 {
   let(ticks,half,fixture)=clocks[step];assert_eq!(ticks-last,half as u64);last=ticks;let h=half as f64*TICK;let pair=joint::step(p,x,h).map_err(|e|format!("base_step:{id}:{step}:{e:?}"))?;let states=[x,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]];
   for(a,b)in states.into_iter().zip(fixture) {assert!(a.high.into_iter().chain(a.low).zip(b.high.into_iter().chain(b.low)).all(|(a,b)|a.to_bits()==b.to_bits()));}
   let s=joint_charge_basis_propagation::propagate(p,x,pair.increments,h,u).map_err(|e|format!("propagate:{id}:{step}:{e:?}"))?;
   for group in 0..2 {let nine=std::array::from_fn(|k|std::array::from_fn(|r|u[k][group*9+r]));let check=joint_history_propagation::propagate(p,x,pair.increments,h,nine).map_err(|e|format!("batch9:{e:?}"))?;for k in 0..400 {for r in 0..9 {assert_eq!(s[k][group*9+r].to_bits(),check[k][r].to_bits());}}}
   let zero=joint_charge_basis_propagation::propagate(p,x,pair.increments,h,[[0.;K];200]).map_err(|e|format!("zero:{e:?}"))?;assert!(zero.iter().flatten().all(|v|*v==0.));
   w.write_all(&ticks.to_le_bytes()).unwrap();w.write_all(&half.to_le_bytes()).unwrap();for state in states {put_state(&mut w,state);}put(&mut w,s.into_iter().flatten());u=std::array::from_fn(|k|s[200+k]);x=pair.candidates[1];
  }
  w.flush().unwrap();eprintln!("BASIS_BASE,{id},wall_s={:.3}",started.elapsed().as_secs_f64());
  for k in 0..K {for h in [0.000125,0.0000625] {for sign in [-1.,1.] {
   guard()?;let mut own_target=target;own_target[k]=add(own_target[k].0,own_target[k].1,sign*h);let(q,it,tr,res,corr,f)=condition(p,z.x,own_target).map_err(|e|format!("own_root:{id}:{k}:{h}:{sign}:{e:?}"))?;put(&mut w,[k as f64,h,sign]);put_root(&mut w,q,[it as f64,tr as f64,res,corr,f]);let mut own=q.x;
   for step in 0..2 {let dt=clocks[step].1 as f64*TICK;let pair=joint::step(p,own,dt).map_err(|e|format!("own_step:{id}:{k}:{h}:{sign}:{step}:{e:?}"))?;own=pair.candidates[1];put_state(&mut w,own);}
  }}w.flush().unwrap();eprintln!("BASIS_COLUMN,{id},{k},wall_s={:.3}",started.elapsed().as_secs_f64());}
 }
 assert_eq!(input.read(&mut [0]).unwrap(),0);w.flush().unwrap();Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
