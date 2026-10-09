"""Generate a lab-only constrained-charge caller against the frozen library."""
from prepare_vco1_portable import ROOT

def caller():
    old=(ROOT/'tools/joint_startup_runner.rs').read_text(encoding='utf8')
    header=old[:old.index('fn run()->Result<(),String>')]
    header=header.replace('joint_startup,','').replace('//! Lab caller: joint constrained DC, chain matrices and short release.','//! Lab-only 218-row phase/charge conditioning; production physics unchanged.')
    source=(ROOT/'crates/rf-d-circuit/src/output_conversion.rs').read_text(encoding='utf8')
    linear=source[source.index('fn solve_linear_internal<'):source.index('/// Scaled-pivot elimination for several')]
    linear=linear.replace('fn solve_linear_internal<const M: usize, const SKIP_ZERO: bool>','fn solve<const M: usize>').replace('max_abs(&j[i])','j[i].iter().fold(0_f64,|a,v|a.max(v.abs()))').replace('SKIP_ZERO && ','')
    return header+'use rf_d_circuit::{StepError,vco1_increment::two_sum};\n'+linear+ALGORITHM

ALGORITHM=r'''
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
fn run()->Result<(),String> {
 let(p,seed)=scene()?;println!("INITIAL_HISTORY");state(seed);
 let rows:Vec<Vec<f64>>=include_str!("../evidence/voice_joint_charge_seed_targets01.txt").lines().map(|line|line.split_whitespace().map(|x|x.parse().unwrap()).collect()).collect();
 if rows.len()!=2||rows.iter().any(|r|r.len()!=36) {return Err("target codec".into());}
 let mut bad=std::array::from_fn(|k|(rows[0][2*k],rows[0][2*k+1]));bad[0].0=f64::NAN;
 if !matches!(condition(p,seed,bad),Err(StepError::InvalidInput)) {return Err("NaN target accepted".into());}
 let mut badstate=seed;badstate.high[0]=f64::NAN;
 if condition(p,badstate,std::array::from_fn(|k|(rows[0][2*k],rows[0][2*k+1]))).is_ok() {return Err("NaN state accepted".into());}
 println!("INPUT_REJECTIONS,2");
 for id in 0..2 {
  let target=std::array::from_fn(|k|(rows[id][2*k],rows[id][2*k+1]));let mut first=None;
  for guess in 0..2 {
   let initial=if guess==0 {seed} else {seed.advanced(std::array::from_fn(|k|if k>=133 {0.001} else {0.}))};
   let(z,iterations,trials,res,corr,forcing)=condition(p,initial,target).map_err(|e|format!("charge:{id}:{guess}:{e:?}"))?;
   println!("CHARGE_ROOT,{id},{guess},{iterations},{trials},{res:.17e},{corr:.17e},{forcing:.17e}");state(z.x);
   print!("CHAIN_CURRENTS");for k in 0..K {print!(",{:.17e},{:.17e}",z.i.high[k],z.i.low[k]);}println!();
   if let Some(root)=first {let error=rf_d_circuit::joint_engine::difference(z.x,root).iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if (98..133).contains(&k) {1e-9} else {1e-6}));if error>1. {return Err("guess root difference".into());}println!("GUESS_REFINEMENT,{id},{error:.17e}");}else {first=Some(z.x);}
  }
  let root=first.unwrap();
  for maximum in [65536,32768] {
   let mut e=Engine::from_conditioned(p,root,Settings{maximum_half_ticks:maximum,attempt_limit:20}).map_err(|e|format!("init:{e:?}"))?;
   let q=e.checkpoint();let mut restore=Engine::restore(q).map_err(|e|format!("restore:{e:?}"))?;
   let a=e.advance_to(1048576).map_err(|e|format!("original replay:{e:?}"))?;let b=restore.advance_to(1048576).map_err(|e|format!("restored replay:{e:?}"))?;
   if e.checkpoint().state!=restore.checkpoint().state||e.checkpoint().elapsed_ticks!=restore.checkpoint().elapsed_ticks||e.checkpoint().next_full_ticks!=restore.checkpoint().next_full_ticks||a.half_ticks!=b.half_ticks||a.error_ratio.to_bits()!=b.error_ratio.to_bits() {return Err("restore replay mismatch".into());}
   e=Engine::restore(q).map_err(|e|format!("restore initial:{e:?}"))?;
   let mut steps=0;let mut bus=0_f64;let mut c1=0_f64;let mut lte=0_f64;
   while e.checkpoint().elapsed_ticks<1048576 {
    if steps>=512 {return Err("interval budget".into());}let old=e.checkpoint().state;let a=e.advance_to(1048576).map_err(|err|format!("release:{id}:{maximum}:{err:?}"))?;steps+=1;lte=lte.max(a.error_ratio);
    let h=f64::from(a.half_ticks)*rf_d_circuit::joint_engine::TICK_S;let mut previous=old;
    for endpoint in &a.endpoints {
     let cur=joint_currents::stages(&endpoint.pair,previous,h).map_err(|err|format!("current:{err:?}"))?;let d=&endpoint.pair.increments;
     let cap=1e-8/h*(joint::B[1][0]*(d[0].high[43]+d[0].low[43])+joint::B[1][1]*(d[1].high[43]+d[1].low[43]));
     c1=c1.max((cap+cur[1].iter().sum::<f64>()).abs());bus=bus.max(endpoint.observations.bus_kcl_a.abs());previous=endpoint.pair.candidates[1];
    }
    if steps==1||e.checkpoint().elapsed_ticks==1048576 {println!("RELEASE_SELECTED,{id},{maximum},{steps}");selected(old,&a);}
   }
   if bus>1e-12||c1>1e-12 {return Err("release balance".into());}
   println!("RELEASE_PROFILE,{id},{maximum},{steps},{:.17e},{bus:.17e},{c1:.17e},restore=exact",lte);state(e.checkpoint().state);
  }
 }
 Ok(())
}
fn main() {if let Err(e)=run() {eprintln!("FAILURE,{e}");std::process::exit(1);}}
'''

if __name__=='__main__':
    p=ROOT/'tools/joint_charge_seed_runner.rs';assert not p.exists()
    p.write_text(caller(),encoding='utf8',newline='\n')
