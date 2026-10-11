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
