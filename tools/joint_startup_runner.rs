//! Lab caller: joint constrained DC, chain matrices and short release.
use rf_d_circuit::{joint_voice as joint,joint_startup,joint_engine::{Engine,Settings},joint_currents,chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,vco1_startup,vco1_stamp::Controls};
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
fn run()->Result<(),String> {
 let(p,seed)=scene()?;println!("INITIAL_HISTORY");state(seed);
 let mut root=None;
 for id in 0..2 {
  let initial=if id==0 {seed} else {seed.advanced(std::array::from_fn(|k|if k>=133 {0.001} else {0.}))};
  let s=joint_startup::condition(p,initial,joint_startup::Budget::default()).map_err(|e|format!("dc:{id}:{e:?}"))?;
  println!("STARTUP_ROOT,{id},{},{},{:.17e},{:.17e},{:.17e}",s.iterations,s.trials,s.residual_ratio,s.correction_ratio,s.constraint_current_a);state(s.state);
  if let Some(first)=root {let error=rf_d_circuit::joint_engine::difference(s.state,first).iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if (98..133).contains(&k) {1e-9} else {1e-6}));if error>1. {return Err("seed root difference".into());}println!("ROOT_REFINEMENT,{error:.17e}");} else {root=Some(s.state);}
 }
 let root=root.unwrap();
 for budget in [joint_startup::Budget{iterations:0,halvings:24},joint_startup::Budget{iterations:64,halvings:25}] {if !matches!(joint_startup::condition(p,seed,budget),Err(rf_d_circuit::StepError::InvalidInput)) {return Err("invalid budget".into());}}
 let mut bad=seed;bad.high[0]=f64::NAN;if joint_startup::condition(p,bad,joint_startup::Budget::default()).is_ok() {return Err("invalid seed".into());}println!("INPUT_REJECTIONS,invalid_budgets=2,invalid_seed=1");
 let chain=chain_charge::State{high:std::array::from_fn(|k|root.high[joint::chain_index(k)]),low:std::array::from_fn(|k|root.low[joint::chain_index(k)])};
 let h=1e-6;let q=chain_charge::linearize(p.chain(),p.sources,chain,[0.;68],h).map_err(|e|format!("matrix:{e:?}"))?;
 for(name,m) in [("CHAIN_G",q.dc_jacobian),("CHAIN_C",q.mass_over_h.map(|r|r.map(|v|v*h)))] {print!("{name}");for v in m.into_iter().flatten() {print!(",{v:.17e}");}println!();}
 for maximum in [65536,32768] {
  let mut e=Engine::from_conditioned(p,root,Settings{maximum_half_ticks:maximum,attempt_limit:20}).map_err(|e|format!("init:{e:?}"))?;let mut steps=0;let mut bus=0_f64;let mut c1=0_f64;let mut lte=0_f64;
  while e.checkpoint().elapsed_ticks<1048576 {
   if steps>=256 {return Err("interval budget".into());}let old=e.checkpoint().state;let a=e.advance_to(1048576).map_err(|err|format!("release:{maximum}:{err:?}"))?;steps+=1;lte=lte.max(a.error_ratio);
   let h=f64::from(a.half_ticks)*rf_d_circuit::joint_engine::TICK_S;let mut previous=old;
   for endpoint in &a.endpoints {
    let cur=joint_currents::stages(&endpoint.pair,previous,h).map_err(|err|format!("current:{err:?}"))?;let d=&endpoint.pair.increments;
    let cap=1e-8/h*(joint::B[1][0]*(d[0].high[43]+d[0].low[43])+joint::B[1][1]*(d[1].high[43]+d[1].low[43]));
    c1=c1.max((cap+cur[1].iter().sum::<f64>()).abs());bus=bus.max(endpoint.observations.bus_kcl_a.abs());previous=endpoint.pair.candidates[1];
   }
   if steps==1||e.checkpoint().elapsed_ticks==1048576 {println!("RELEASE_SELECTED,{maximum},{steps}");selected(old,&a);}
  }
  if bus>1e-12||c1>1e-12 {return Err("release balance".into());}
  println!("RELEASE_PROFILE,{maximum},{steps},{:.17e},{bus:.17e},{c1:.17e}",lte);state(e.checkpoint().state);
 }
 Ok(())
}
fn main() {if let Err(e)=run() {eprintln!("FAILURE,{e}");std::process::exit(1);}}
