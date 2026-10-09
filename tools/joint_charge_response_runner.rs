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
fn record(label:&str,id:usize,k:usize,h:f64,z:Aug,iterations:usize,trials:usize,res:f64,corr:f64,forcing:f64) {
 println!("{label},{id},{k},{h:.17e},{iterations},{trials},{res:.17e},{corr:.17e},{forcing:.17e}");state(z.x);
 print!("CHAIN_CURRENTS");for k in 0..K {print!(",{:.17e},{:.17e}",z.i.high[k],z.i.low[k]);}println!();
}
fn run()->Result<(),String> {
 let(p,seed)=scene()?;
 let rows:Vec<Vec<f64>>=include_str!("../evidence/voice_joint_charge_seed_targets01.txt").lines().map(|line|line.split_whitespace().map(|x|x.parse().unwrap()).collect()).collect();
 if rows.len()!=2||rows.iter().any(|r|r.len()!=36) {return Err("target codec".into());}
 for id in 0..2 {
  let target=std::array::from_fn(|k|(rows[id][2*k],rows[id][2*k+1]));
  let(z,it,tr,res,corr,f)=condition(p,seed,target).map_err(|e|format!("base:{id}:{e:?}"))?;
  record("RESPONSE_BASE",id,0,0.,z,it,tr,res,corr,f);
  let(_,matrix,_)=system(p,z,target).map_err(|e|format!("matrix:{e:?}"))?;
  for k in 0..K {
   let mut rhs=[0.;M];rhs[200+k]=1.;
   let d=solve(matrix,rhs).map_err(|e|format!("response:{id}:{k}:{e:?}"))?;
   print!("RESPONSE_COLUMN,{id},{k}");for value in d {print!(",{value:.17e}");}println!();
  }
  for k in 0..K {for h in [0.001,0.0005] {for sign in [-1.,1.] {
   let mut t=target;t[k]=add(t[k].0,t[k].1,sign*h);
   let(q,it,tr,res,corr,f)=condition(p,z.x,t).map_err(|e|format!("perturb:{id}:{k}:{h}:{sign}:{e:?}"))?;
   record("RESPONSE_PERTURB",id,k,sign*h,q,it,tr,res,corr,f);
  }}}
 }
 Ok(())
}
fn main() {if let Err(e)=run() {eprintln!("FAILURE,{e}");std::process::exit(1);}}
