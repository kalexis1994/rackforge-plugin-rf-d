//! Offline clocks and exact paired evidence; not audio-thread code.
pub use rf_d_circuit::*;
use std::{fs,time::Instant};
#[path="voice_pivot_profile_kernel.rs"] mod profiled;
#[path="voice_pivot_copy_kernel.rs"] mod plain;
#[path="voice_pivot_kernel.rs"] mod candidate;
struct Case{ohm:f64,h:f64,old:[f64;458],expected:[u64;1834],counts:[u64;2]}
fn scene()->rf_d_circuit::conditioned_voice::Parameters{conditioned_recipe::Recipe{final_decay:conditioned_recipe::FinalDecay::On,resolution:conditioned_recipe::Resolution::Half2Us}.parameters()}
fn cases(path:&str)->Vec<Case>{let b=fs::read(path).unwrap();assert_eq!(&b[..8],b"RFPIVT01");let n=u32::from_le_bytes(b[8..12].try_into().unwrap()) as usize;assert_eq!(b.len(),12+n*18368);(0..n).map(|i|{let r=&b[12+i*18368..12+(i+1)*18368];let u=|k:usize|u64::from_le_bytes(r[8*k..8*k+8].try_into().unwrap());Case{ohm:f64::from_bits(u(0)),h:f64::from_bits(u(1)),old:std::array::from_fn(|k|f64::from_bits(u(k+2))),expected:std::array::from_fn(|k|u(k+460)),counts:[u(2294),u(2295)]}}).collect()}
macro_rules! runner{($name:ident,$module:ident)=>{
fn $name(cs:&[Case])->(u128,Vec<(Vec<u64>,[u64;2])>){let mut w=$module::Workspace::new();let mut time=0;let mut rows=Vec::new();for c in cs{let mut p=$module::Parameters::from_nominal(scene());p.decay_ohm=c.ohm;let s=$module::State{high:std::array::from_fn(|k|c.old[k]),low:std::array::from_fn(|k|c.old[k+229])};let t=Instant::now();let a=w.step(p,s,c.h).expect("finite native pair");time+=t.elapsed().as_nanos();let mut v=Vec::new();for state in a.increments.iter().chain(a.candidates.iter()){v.extend(state.high.iter().chain(state.low.iter()).map(|v|v.to_bits()));}v.extend([a.residual_ratio.to_bits(),a.correction_ratio.to_bits()]);assert_eq!(v,c.expected,"historical 1834 f64");let counts=[a.iterations as u64,a.trials as u64];if c.counts[0]!=u64::MAX{assert_eq!(counts,c.counts,"historical nominal counters");}rows.push((v,counts));}(time,rows)}
}}
use rf_d_circuit::decay_voice as baseline;
runner!(run_baseline,baseline);runner!(run_plain,plain);runner!(run_profiled,profiled);runner!(run_candidate,candidate);
fn errors(){
 // Exercise the original rejection policy, including structural checks.
 let tests=[0,1,2,3,4,5];for kind in tests{let mut j=[[0.;458];458];let mut b=[0.;458];for k in 0..458{j[k][k]=1.;b[k]=1.;}
 match kind{0=>j.fill([0.;458]),1=>j[0][0]=f64::NAN,2=>b[0]=f64::INFINITY,3=>j[56][0]=1.,4=>{j[0][1]=1.;j[1][0]=1.;j[1][1]=1.+1e-14;},_=>{b[0]=f64::MAX;j[0][0]=0.1;}}
 let a=baseline::dynamic_schur::solve_observed(j,b);let c=candidate::dynamic_schur::solve_observed(j,b);assert_eq!(a.err(),c.err(),"same error class");assert!(baseline::dynamic_schur::solve_observed(j,b).is_err(),"negative fixture rejects");
 }println!("ERRORS_PASSED,6");
}
fn main(){let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),78);let(_,gold)=run_baseline(&cs);let(_,copy)=run_plain(&cs);assert_eq!(gold,copy);let(_,profile)=run_profiled(&cs);assert_eq!(gold,profile);profiled::profile();errors();
 for round in 0..5{let(a,x,b,y)=if round%2==0{let(a,x)=run_baseline(&cs);let(b,y)=run_candidate(&cs);(a,x,b,y)}else{let(b,y)=run_candidate(&cs);let(a,x)=run_baseline(&cs);(a,x,b,y)};assert_eq!(gold,x);assert_eq!(gold,y);println!("ROUND,{round},{a},{b}");}println!("PIVOT_BENCH_PASSED,78,1834,5");}
