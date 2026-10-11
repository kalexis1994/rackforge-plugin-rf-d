
mod joint_history_tangent;
mod joint_history_propagation;
mod joint_history_event;
mod joint_charge_basis_propagation;
mod joint_conditioned_return_event;
use joint_charge_basis_propagation::Sensitivity;
use joint_conditioned_return_event::Event;
use std::{fs::File,io::{Read,Write,BufWriter},path::Path,time::Instant};
const TICK:f64=125e-9/65536.;
const OBS:[usize;7]=[43,46,54,44,12,39,194];
const FIX:[usize;6]=[0,1,20188,20189,42542,42543];
fn get<const N:usize>(r:&mut impl Read)->[u8;N] {let mut b=[0;N];r.read_exact(&mut b).unwrap();b}
fn read_f(r:&mut impl Read)->f64 {let v=f64::from_le_bytes(get(r));assert!(v.is_finite());v}
fn read_state(r:&mut impl Read)->joint::State {joint::State{high:std::array::from_fn(|_|read_f(r)),low:std::array::from_fn(|_|read_f(r))}}
fn put(w:&mut impl Write,v:impl IntoIterator<Item=f64>) {for v in v {assert!(v.is_finite());w.write_all(&v.to_le_bytes()).unwrap();}}
fn put_state(w:&mut impl Write,s:joint::State) {put(w,s.high);put(w,s.low);}
fn put_root(w:&mut impl Write,z:Aug,m:[f64;5]) {put_state(w,z.x);put(w,(0..K).flat_map(|k|[z.i.high[k],z.i.low[k]]));put(w,m);}
fn state_bits(a:joint::State,b:joint::State)->bool {a.high.into_iter().chain(a.low).zip(b.high.into_iter().chain(b.low)).all(|(a,b)|a.to_bits()==b.to_bits())}
fn put_event(w:&mut impl Write,e:&Event) {put(w,[e.alpha]);put_state(w,e.state);put(w,e.dalpha);put(w,e.dt);put(w,e.response.into_iter().flatten());}
fn failed(label:&str,x:joint::State,h:f64,e:StepError)->String {eprint!("FAILED_STEP,{label},{h:.17e}");for v in x.high.into_iter().chain(x.low) {eprint!(",{v:.17e}");}eprintln!();format!("{label}:{e:?}")}
fn check_event(a:joint::State,b:joint::State,h:f64,sa:Sensitivity,sb:Sensitivity)->Event {
 let e=joint_conditioned_return_event::crossing(a,b,h,sa,sb);
 for group in 0..2 {let na=std::array::from_fn(|k|std::array::from_fn(|r|sa[k][9*group+r]));let nb=std::array::from_fn(|k|std::array::from_fn(|r|sb[k][9*group+r]));let q=joint_history_event::crossing(a,b,h,na,nb);assert_eq!(e.alpha.to_bits(),q.alpha.to_bits());assert!(state_bits(e.state,q.state));for r in 0..9 {assert_eq!(e.dalpha[9*group+r].to_bits(),q.dalpha[r].to_bits());assert_eq!(e.dt[9*group+r].to_bits(),q.dt[r].to_bits());for k in 0..200 {assert_eq!(e.response[k][9*group+r].to_bits(),q.response[k][r].to_bits());}}}
 let z=joint_conditioned_return_event::crossing(a,b,h,[[0.;K];400],[[0.;K];400]);assert!(z.dalpha.into_iter().chain(z.dt).chain(z.response.into_iter().flatten()).all(|v|v==0.));e
}
fn run()->Result<(),String> {
 let args:Vec<String>=std::env::args().collect();let output=Path::new(&args[2]);let start=Instant::now();let guard=||->Result<(),String>{if start.elapsed().as_secs_f64()>4400.||output.parent().unwrap().join("stop.flag").exists(){Err("ADMINISTRATIVE_BUDGET".into())}else{Ok(())}};
 let(p,seed)=scene()?;let mut r=File::open(&args[1]).map_err(|e|e.to_string())?;assert_eq!(get::<8>(&mut r),*b"RFJCRIN1");let n=u32::from_le_bytes(get(&mut r)) as usize;assert_eq!(n,42544);
 let mut expected=Aug{x:read_state(&mut r),i:joint::State::from_nodes([0.;200])};for k in 0..K {expected.i.high[k]=read_f(&mut r);expected.i.low[k]=read_f(&mut r);}
 let expected_basis:[[f64;K];M]=std::array::from_fn(|_|std::array::from_fn(|_|read_f(&mut r)));let fixtures:[[joint::State;5];6]=std::array::from_fn(|_|std::array::from_fn(|_|read_state(&mut r)));let prefix:[Sensitivity;2]=std::array::from_fn(|_|std::array::from_fn(|_|std::array::from_fn(|_|read_f(&mut r))));
 let count=u32::from_le_bytes(get(&mut r));assert_eq!(count,20);let points:Vec<usize>=(0..count).map(|_|u32::from_le_bytes(get(&mut r)) as usize).collect();let clocks:Vec<(u64,u32,[f64;7])>=(0..n).map(|_|(u64::from_le_bytes(get(&mut r)),u32::from_le_bytes(get(&mut r)),std::array::from_fn(|_|read_f(&mut r)))).collect();assert_eq!(r.read(&mut [0]).unwrap(),0);
 let row:Vec<f64>=include_str!("../evidence/voice_joint_charge_response_targets01.txt").lines().next().unwrap().split_whitespace().map(|v|v.parse().unwrap()).collect();let target=std::array::from_fn(|k|(row[2*k],row[2*k+1]));let(z,it,tr,res,corr,f)=condition(p,seed,target).map_err(|e|format!("base_root:{e:?}"))?;assert!(state_bits(z.x,expected.x));for k in 0..K {assert_eq!(z.i.high[k].to_bits(),expected.i.high[k].to_bits());assert_eq!(z.i.low[k].to_bits(),expected.i.low[k].to_bits());}
 let(_,matrix,_)=system(p,z,target).map_err(|e|format!("base_matrix:{e:?}"))?;let mut basis=[[0.;K];M];for k in 0..K {let mut rhs=[0.;M];rhs[200+k]=1.;let b=solve(matrix,rhs).map_err(|e|format!("basis:{k}:{e:?}"))?;for row in 0..M {basis[row][k]=b[row];assert_eq!(b[row].to_bits(),expected_basis[row][k].to_bits());}}
 let mut w=BufWriter::new(File::create_new(output).map_err(|e|e.to_string())?);w.write_all(b"RFJCRO01").unwrap();w.write_all(&(n as u32).to_le_bytes()).unwrap();put_root(&mut w,z,[it as f64,tr as f64,res,corr,f]);put(&mut w,basis.into_iter().flatten());
 let mut u=std::array::from_fn(|k|basis[k]);let mut x=z.x;let mut gain=[1_f64;K];let mut ends=[x;4];let mut sensitivities=[[[0.;K];400];4];let mut last=0;
 for k in 0..200 {for c in 0..K {let scale=if (98..133).contains(&k){1e-8}else{1e-5};gain[c]=gain[c].max(1e-5*u[k][c].abs()/scale);}}
 for step in 0..n {
  guard()?;let(ticks,half,obs)=clocks[step];assert_eq!(ticks-last,half as u64);last=ticks;let h=half as f64*TICK;let pair=joint::step(p,x,h).map_err(|e|failed(&format!("BASE,{step}"),x,h,e))?;let states=[x,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]];
  if let Some(index)=FIX.iter().position(|s|*s==step) {for(a,b)in states.into_iter().zip(fixtures[index]) {assert!(state_bits(a,b));}if index>=2 {ends[index-2]=pair.candidates[1];}}
  let observed=OBS.map(|k|pair.candidates[1].high[k]+pair.candidates[1].low[k]);for k in 0..7 {assert_eq!(observed[k].to_bits(),obs[k].to_bits());}
  let s=joint_charge_basis_propagation::propagate(p,x,pair.increments,h,u).map_err(|e|failed(&format!("PROPAGATE,{step}"),x,h,e))?;
  if step<2 {for k in 0..400 {for c in 0..K {assert_eq!(s[k][c].to_bits(),prefix[step][k][c].to_bits());}}}
  for k in 0..400 {for c in 0..K {let scale=if (98..133).contains(&(k%200)){1e-8}else{1e-5};gain[c]=gain[c].max(1e-5*s[k][c].abs()/scale);}}
  w.write_all(&(step as u32).to_le_bytes()).unwrap();w.write_all(&ticks.to_le_bytes()).unwrap();w.write_all(&half.to_le_bytes()).unwrap();put(&mut w,observed);let sample=points.contains(&step);w.write_all(&[sample as u8]).unwrap();
  if sample {for q in states {put_state(&mut w,q);}put(&mut w,u.into_iter().flatten());put(&mut w,s.into_iter().flatten());let zero=joint_charge_basis_propagation::propagate(p,x,pair.increments,h,[[0.;K];200]).map_err(|e|failed("ZERO",x,h,e))?;assert!(zero.iter().flatten().all(|v|*v==0.));}
  if let Some(index)=FIX.iter().position(|s|*s==step) {if index>=2 {sensitivities[index-2]=s;}}
  u=std::array::from_fn(|k|s[200+k]);x=pair.candidates[1];if step%2048==0||step+1==n {w.flush().unwrap();eprintln!("CONDITIONED_BASE,{step},wall_s={:.3}",start.elapsed().as_secs_f64());}
 }
 let epsilon=gain.map(|g|1e-5/g);put(&mut w,gain);put(&mut w,epsilon);let h1=clocks[20189].1 as f64*TICK;let h2=clocks[n-1].1 as f64*TICK;let first=check_event(ends[0],ends[1],h1,sensitivities[0],sensitivities[1]);let second=check_event(ends[2],ends[3],h2,sensitivities[2],sensitivities[3]);put_event(&mut w,&first);put_event(&mut w,&second);
 let fixed=(clocks[n-2].0-clocks[20188].0) as f64*TICK;put(&mut w,[fixed+h2*second.alpha-h1*first.alpha]);put(&mut w,rf_d_circuit::joint_engine::difference(second.state,first.state));put(&mut w,(0..K).map(|c|second.dt[c]-first.dt[c]));put(&mut w,(0..200).flat_map(|k|(0..K).map(move |c|second.response[k][c]-first.response[k][c])));w.flush().unwrap();
 for scale in [1.,0.5] {for sign in [1.,-1.] {
  guard()?;let size=scale*epsilon[5];let mut own_target=target;own_target[5]=add(target[5].0,target[5].1,sign*size);let(q,it,tr,res,corr,f)=condition(p,z.x,own_target).map_err(|e|failed(&format!("OWN_ROOT,{scale},{sign}"),z.x,0.,e))?;put(&mut w,[scale,sign,size]);put_root(&mut w,q,[it as f64,tr as f64,res,corr,f]);let mut own=q.x;let mut own_ends=[own;4];
  for step in 0..n {guard()?;let h=clocks[step].1 as f64*TICK;let pair=joint::step(p,own,h).map_err(|e|failed(&format!("OWN,{scale},{sign},{step}"),own,h,e))?;own=pair.candidates[1];if let Some(index)=FIX.iter().position(|s|*s==step) {if index>=2 {own_ends[index-2]=own;}}if step%4096==0||step+1==n {eprintln!("CONDITIONED_OWN,{scale},{sign},{step},wall_s={:.3}",start.elapsed().as_secs_f64());}}
  let zero:Sensitivity=[[0.;K];400];let a=joint_conditioned_return_event::crossing(own_ends[0],own_ends[1],h1,zero,zero);let b=joint_conditioned_return_event::crossing(own_ends[2],own_ends[3],h2,zero,zero);for q in own_ends {put_state(&mut w,q);}put(&mut w,[a.alpha]);put_state(&mut w,a.state);put(&mut w,[b.alpha]);put_state(&mut w,b.state);put(&mut w,[fixed+h2*b.alpha-h1*a.alpha]);w.flush().unwrap();
 }}Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
