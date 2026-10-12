//! Lab-only 218-row phase/charge conditioning; production physics unchanged.
use rf_d_circuit::{joint_voice as joint,joint_engine::{Engine,Settings},joint_currents,chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,vco1_startup,vco1_stamp::Controls};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
fn scene()->Result<(joint::Parameters,joint::State),String> {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let p=Chain {circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
 let controls=Controls::default();let v=vco1_startup::startup(controls).map_err(|e|format!("startup:{e:?}"))?.nodes;
 let row:Vec<f64>=include_str!("../evidence/voice_chain_charge_vectors06.txt").lines().next().unwrap().split_whitespace().map(|x|x.parse().unwrap()).collect();
 let c=chain_charge::State::from_nodes(row[8..76].try_into().unwrap());
 Ok((joint::Parameters::new(controls,p,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap(),joint::State::lift(v,[0.;134],c)))
}
fn state(s:joint::State) {print!("JOINT_STATE");for v in s.high.into_iter().chain(s.low) {print!(",{v:.17e}");}println!();}
fn selected(old:joint::State,a:&rf_d_circuit::joint_engine::Accepted) {
 let h=f64::from(a.half_ticks)*rf_d_circuit::joint_engine::TICK_S;
 for(dt,s,pair) in [(2.*h,old,&a.coarse),(h,old,&a.endpoints[0].pair),(h,a.endpoints[0].pair.candidates[1],&a.endpoints[1].pair)] {
  println!("JOINT_ROOT,0,{dt:.17e},{:.17e},{:.17e}",pair.residual_ratio,pair.correction_ratio);
  for x in [s,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]] {state(x);}
 }
}
use rf_d_circuit::{StepError,vco1_increment::two_sum};
fn solve<const M: usize>(
    mut j: [[f64; M]; M],
    mut rhs: [f64; M],
) -> Result<[f64; M], StepError> {
    let mut scale = [0.0; M];
    for i in 0..M {
        scale[i] = j[i].iter().fold(0_f64,|a,v|a.max(v.abs()));
        if scale[i] == 0.0 {
            return Err(StepError::SingularJacobian);
        }
    }
    for col in 0..M {
        let mut pivot = col;
        let mut best = 0.0;
        for row in col..M {
            if j[row][col] == 0.0 {
                continue;
            }
            let score = j[row][col].abs() / scale[row];
            if score > best {
                best = score;
                pivot = row;
            }
        }
        if best < 1e-12 {
            return Err(StepError::SingularJacobian);
        }
        j.swap(col, pivot);
        rhs.swap(col, pivot);
        scale.swap(col, pivot);
        let diagonal = j[col][col];
        for row in (col + 1)..M {
            if j[row][col] == 0.0 {
                continue;
            }
            let factor = j[row][col] / diagonal;
            j[row][col] = 0.0;
            #[allow(clippy::needless_range_loop)]
            for k in (col + 1)..M {
                j[row][k] -= factor * j[col][k];
            }
            rhs[row] -= factor * rhs[col];
        }
    }
    let mut out = [0.0; M];
    for row in (0..M).rev() {
        let mut value = rhs[row];
        for k in (row + 1)..M {
            value -= j[row][k] * out[k];
        }
        out[row] = value / j[row][row];
    }
    if out.iter().any(|v| !v.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(out)
}


const K:usize=18;
const M:usize=218;
#[derive(Clone,Copy)]
struct Aug {x:joint::State,i:joint::State}
fn branches()->[(usize,Option<usize>,f64);K] {
 let mut c=[(0,None,0.);K];
 for(k,(a,b,f))in chain_charge::CAPACITORS.into_iter().enumerate() {c[k]=(joint::chain_index(a),if b<68 {Some(joint::chain_index(b))} else {None},f);}
 c[17]=(joint::chain_index(67),Some(joint::chain_index(7)),10e-6);c
}
fn add(h:f64,l:f64,d:f64)->(f64,f64) {let(s,e)=two_sum(h,d);let(t,f)=two_sum(l,e);let(u,v)=two_sum(s,t);two_sum(u,v+f)}
fn voltage(x:joint::State,a:usize,b:Option<usize>)->(f64,f64) {
 let mut v=(x.high[a],x.low[a]);if let Some(b)=b {v=add(v.0,v.1,-x.high[b]);v=add(v.0,v.1,-x.low[b]);}v
}
fn system(p:joint::Parameters,z:Aug,target:[(f64,f64);K])->Result<([f64;M],[[f64;M];M],f64),StepError> {
 if target.iter().any(|(h,l)|!h.is_finite()||!l.is_finite()||two_sum(*h,*l)!=(*h,*l))||(0..K).any(|k|!z.i.high[k].is_finite()||!z.i.low[k].is_finite()||z.i.high[k].abs()>1.) {return Err(StepError::InvalidInput);}
 let q=joint::parts(p,z.x,joint::State::from_nodes([0.;200]),125e-9)?;
 let mut r=[0.;M];r[..200].copy_from_slice(&q.dc);let mut j=[[0.;M];M];for a in 0..200 {j[a][..200].copy_from_slice(&q.dc_jacobian[a]);}
 let forcing=-r[43];r[43]=z.x.high[43]+z.x.low[43];j[43]=[0.;M];j[43][43]=1.;
 for(k,(a,b,_))in branches().into_iter().enumerate() {
  let i=z.i.high[k]+z.i.low[k];r[a]+=i;j[a][200+k]=1.;j[200+k][a]=1.;
  if let Some(b)=b {r[b]-=i;j[b][200+k]=-1.;j[200+k][b]=-1.;}
  let v=voltage(z.x,a,b);let v=add(v.0,v.1,-target[k].0);let v=add(v.0,v.1,-target[k].1);r[200+k]=v.0+v.1;
 }
 Ok((r,j,forcing))
}
fn merit(p:joint::Parameters,r:&[f64;M])->f64 {r.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if k>=200||k==43||joint::constraint_row(p,k) {1e-11} else {1e-13}))}
fn correction(d:&[f64;M])->f64 {d.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if k>=200||(98..133).contains(&k) {2e-12} else {2e-9}))}
fn advance(z:Aug,d:[f64;M],alpha:f64)->Aug {Aug{x:z.x.advanced(std::array::from_fn(|k|alpha*d[k])),i:z.i.advanced(std::array::from_fn(|k|if k<K {alpha*d[200+k]} else {0.}))}}
fn condition(p:joint::Parameters,initial:joint::State,target:[(f64,f64);K])->Result<(Aug,usize,usize,f64,f64,f64),StepError> {
 let mut z=Aug{x:initial,i:joint::State::from_nodes([0.;200])};let mut trials=0;
 for iteration in 1..=64 {
  let(r,j,forcing)=system(p,z,target)?;let norm=merit(p,&r);let d=solve(j,r.map(|v|-v))?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {return Ok((z,iteration,trials,norm,ratio,forcing));}
  let mut accepted=false;
  for power in 0..24 {let alpha=2_f64.powi(-power);let trial=advance(z,d,alpha);trials+=1;
   if let Ok((rr,jj,_))=system(p,trial,target) {if let Ok(dd)=solve(jj,rr.map(|v|-v)) {
    if (merit(p,&rr)<=1.&&correction(&dd)<=1.)||merit(p,&rr)<norm*(1.-1e-4*alpha) {z=trial;accepted=true;break;}
   }}
  }if !accepted {return Err(StepError::NoDecrease);}
 }Err(StepError::IterationBudget)
}

mod joint_history_tangent;
mod joint_charge_basis_propagation;
mod joint_conditioned_return_event;
use std::{fs::File,io::{Read,Write,BufWriter},path::{Path,PathBuf},sync::Arc,time::Instant};
const TICK:f64=125e-9/65536.;
const OBS:[usize;7]=[43,46,54,44,12,39,194];
fn get<const N:usize>(r:&mut impl Read)->[u8;N] {let mut b=[0;N];r.read_exact(&mut b).unwrap();b}
fn read_f(r:&mut impl Read)->f64 {let v=f64::from_le_bytes(get(r));assert!(v.is_finite());v}
fn read_state(r:&mut impl Read)->joint::State {joint::State{high:std::array::from_fn(|_|read_f(r)),low:std::array::from_fn(|_|read_f(r))}}
fn put(w:&mut impl Write,v:impl IntoIterator<Item=f64>) {for v in v {assert!(v.is_finite());w.write_all(&v.to_le_bytes()).unwrap();}}
fn put_state(w:&mut impl Write,s:joint::State) {put(w,s.high);put(w,s.low);}
fn put_root(w:&mut impl Write,z:Aug,m:[f64;5]) {put_state(w,z.x);put(w,(0..K).flat_map(|k|[z.i.high[k],z.i.low[k]]));put(w,m);}
fn state_bits(a:joint::State,b:joint::State)->bool {a.high.into_iter().chain(a.low).zip(b.high.into_iter().chain(b.low)).all(|(a,b)|a.to_bits()==b.to_bits())}
fn failed(label:&str,x:joint::State,h:f64,e:StepError)->String {eprint!("FAILED_STEP,{label},{h:.17e}");for v in x.high.into_iter().chain(x.low) {eprint!(",{v:.17e}");}eprintln!();format!("{label}:{e:?}")}
type Clock=(u64,u32,[f64;7]);
struct Task {id:usize,a:f64,z:Aug,metrics:[f64;5],prefix:Vec<[joint::State;5]>}
fn guard(start:Instant,out:&Path)->Result<(),String> {if start.elapsed().as_secs_f64()>3400.||out.join("stop.flag").exists(){Err("ADMINISTRATIVE_BUDGET".into())}else{Ok(())}}
fn worker(p:joint::Parameters,t:Task,clocks:&[Clock],points:&[usize],out:&Path,start:Instant)->Result<(),String> {
 let mut w=BufWriter::new(File::create_new(out.join(format!("own-{}.bin",t.id))).map_err(|e|e.to_string())?);w.write_all(b"RFJDIRO1").unwrap();w.write_all(&(t.id as u32).to_le_bytes()).unwrap();w.write_all(&(clocks.len() as u32).to_le_bytes()).unwrap();put(&mut w,[t.a]);put_root(&mut w,t.z,t.metrics);
 let mut x=t.z.x;let mut last=0;let mut events=Vec::new();
 for step in 0..clocks.len() {
  guard(start,out)?;let(ticks,half,_)=clocks[step];assert_eq!(ticks-last,half as u64);last=ticks;let h=half as f64*TICK;let pair=joint::step(p,x,h).map_err(|e|failed(&format!("OWN,{},{step}",t.id),x,h,e))?;let states=[x,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]];
  if step<64 {for(a,b)in states.into_iter().zip(t.prefix[step]) {assert!(state_bits(a,b));}}
  let observed=OBS.map(|k|pair.candidates[1].high[k]+pair.candidates[1].low[k]);w.write_all(&(step as u32).to_le_bytes()).unwrap();w.write_all(&ticks.to_le_bytes()).unwrap();w.write_all(&half.to_le_bytes()).unwrap();put(&mut w,observed);let sample=step<64||points.contains(&step);w.write_all(&[sample as u8]).unwrap();if sample {for state in states {put_state(&mut w,state);}}
  let ra=x.high[43]+x.low[43];let rb=observed[0];if ra< -2.&&rb>= -2. {assert!(events.len()<2);let zero=[[0.;K];400];let e=joint_conditioned_return_event::crossing(x,pair.candidates[1],h,zero,zero);events.push((step,ticks,half,x,pair.candidates[1],e));}
  x=pair.candidates[1];if step%4096==0||step+1==clocks.len() {w.flush().unwrap();eprintln!("DIRECTION_OWN,{},{step},wall_s={:.3}",t.id,start.elapsed().as_secs_f64());}
 }
 assert_eq!(events.len(),2);w.write_all(&2_u32.to_le_bytes()).unwrap();let mut times=[0.;2];let mut zs=[x;2];
 for(i,(index,ticks,half,a,b,e))in events.into_iter().enumerate() {w.write_all(&(index as u32).to_le_bytes()).unwrap();w.write_all(&ticks.to_le_bytes()).unwrap();w.write_all(&half.to_le_bytes()).unwrap();put_state(&mut w,a);put_state(&mut w,b);put(&mut w,[e.alpha]);put_state(&mut w,e.state);times[i]=(ticks-half as u64) as f64*TICK+half as f64*TICK*e.alpha;put(&mut w,[times[i]]);zs[i]=e.state;}
 put(&mut w,[times[1]-times[0]]);put(&mut w,rf_d_circuit::joint_engine::difference(zs[1],zs[0]));w.flush().unwrap();Ok(())
}
fn run()->Result<(),String> {
 let args:Vec<String>=std::env::args().collect();let out=PathBuf::from(&args[2]);let start=Instant::now();let(p,seed)=scene()?;let mut r=File::open(&args[1]).map_err(|e|e.to_string())?;assert_eq!(get::<8>(&mut r),*b"RFJDIRI1");let n=u32::from_le_bytes(get(&mut r)) as usize;assert_eq!(n,42544);let mut expected=Aug{x:read_state(&mut r),i:joint::State::from_nodes([0.;200])};for k in 0..K {expected.i.high[k]=read_f(&mut r);expected.i.low[k]=read_f(&mut r);}
 let direction:[f64;K]=std::array::from_fn(|_|read_f(&mut r));let epsilon=read_f(&mut r);assert!(epsilon>0.&&direction[16]==0.);let count=u32::from_le_bytes(get(&mut r));assert_eq!(count,20);let points:Vec<usize>=(0..count).map(|_|u32::from_le_bytes(get(&mut r)) as usize).collect();let clocks:Vec<Clock>=(0..n).map(|_|(u64::from_le_bytes(get(&mut r)),u32::from_le_bytes(get(&mut r)),std::array::from_fn(|_|read_f(&mut r)))).collect();assert_eq!(r.read(&mut [0]).unwrap(),0);
 let row:Vec<f64>=include_str!("../evidence/voice_joint_charge_response_targets01.txt").lines().next().unwrap().split_whitespace().map(|v|v.parse().unwrap()).collect();let target=std::array::from_fn(|k|(row[2*k],row[2*k+1]));let(z,it,tr,res,corr,f)=condition(p,seed,target).map_err(|e|failed("BASE_ROOT",seed,0.,e))?;assert!(state_bits(z.x,expected.x));for k in 0..K {assert_eq!(z.i.high[k].to_bits(),expected.i.high[k].to_bits());assert_eq!(z.i.low[k].to_bits(),expected.i.low[k].to_bits());}
 let mut bw=BufWriter::new(File::create_new(out.join("base.bin")).map_err(|e|e.to_string())?);bw.write_all(b"RFJDBAS1").unwrap();put_root(&mut bw,z,[it as f64,tr as f64,res,corr,f]);bw.flush().unwrap();
 let mut serial=BufWriter::new(File::create_new(out.join("serial-prefix.bin")).map_err(|e|e.to_string())?);serial.write_all(b"RFJDSP01").unwrap();serial.write_all(&5_u32.to_le_bytes()).unwrap();let mut queues:Vec<Vec<Task>>=(0..4).map(|_|Vec::new()).collect();
 for(id,a)in [epsilon,-epsilon,epsilon/2.,-epsilon/2.,1.].into_iter().enumerate() {
  guard(start,&out)?;let mut own_target=target;for k in 0..K {own_target[k]=add(target[k].0,target[k].1,a*direction[k]);}let(q,it,tr,res,corr,f)=condition(p,z.x,own_target).map_err(|e|failed(&format!("ROOT,{id}"),z.x,0.,e))?;let mut x=q.x;let mut prefix=Vec::new();serial.write_all(&(id as u32).to_le_bytes()).unwrap();
  for step in 0..64 {let h=clocks[step].1 as f64*TICK;let pair=joint::step(p,x,h).map_err(|e|failed(&format!("SERIAL,{id},{step}"),x,h,e))?;let states=[x,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]];for state in states {put_state(&mut serial,state);}prefix.push(states);x=pair.candidates[1];}
  queues[id%4].push(Task{id,a,z:q,metrics:[it as f64,tr as f64,res,corr,f],prefix});
 }
 serial.flush().unwrap();let clocks=Arc::new(clocks);let points=Arc::new(points);let mut handles=Vec::new();
 for(i,tasks)in queues.into_iter().enumerate() {let clock=clocks.clone();let point=points.clone();let path=out.clone();handles.push(std::thread::Builder::new().name(format!("direction-{i}")).stack_size(33554432).spawn(move||->Result<(),String>{for task in tasks {worker(p,task,&clock,&point,&path,start)?;}Ok(())}).map_err(|e|e.to_string())?);}
 let mut error=None;for h in handles {match h.join() {Ok(Ok(()))=>(),Ok(Err(e))=>{if error.is_none(){error=Some(e);}},Err(_)=>{if error.is_none(){error=Some("WORKER_PANIC".into());}}}}if let Some(e)=error {return Err(e);}Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
