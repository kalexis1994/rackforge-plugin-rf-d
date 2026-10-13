//! Laboratory-only paired cost measurement; heap/timers are outside audio admission.
#[path="../references-local/lu-extent-inputs01/reference_profile.rs"] mod reference;
#[path="../references-local/lu-extent-inputs01/reuse_profile.rs"] mod reuse;
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer,vco1_stamp::Controls};
use std::time::Instant;
struct Case{on:bool,phase:usize,h:f64,res:f64,corr:f64,states:[[f64;458];5]}
fn cases(path:&str)->Vec<Case>{
 let b=std::fs::read(path).unwrap();let u=|k|u32::from_le_bytes(b[k..k+4].try_into().unwrap());let f=|k|f64::from_le_bytes(b[k..k+8].try_into().unwrap());let n=u64::from_le_bytes(b[..8].try_into().unwrap()) as usize;assert_eq!(b.len(),8+n*18352);
 (0..n).map(|i|{let p=8+i*18352;Case{on:u(p)!=0,phase:u(p+4) as usize,h:f(p+8),res:f(p+16),corr:f(p+24),states:std::array::from_fn(|k|std::array::from_fn(|a|f(p+32+8*(k*458+a))))}}).collect()
}
macro_rules! execute{($name:ident,$m:ident)=>{fn $name(c:&Case)->(Vec<u64>,usize,usize){
 let(mut a,b,d)=lab::lab_parameters();a.r61_ohm=200.;let mut chain=Chain{circuit:a,conversion:b,headphone:d,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};chain.boundary.panel.cutoff_fraction_from_neg10=1.;let mut p=$m::Parameters::new(Controls::default(),chain,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap();p.final_decay=c.on;p.keyboard=[0.,10.,0.][c.phase];p.short=c.phase==1;
 let old=$m::State{high:std::array::from_fn(|k|c.states[0][k]),low:std::array::from_fn(|k|c.states[0][k+229])};let q=$m::step(p,old,c.h).unwrap();let mut out=Vec::with_capacity(1834);for s in q.increments.into_iter().chain(q.candidates){out.extend(s.high.into_iter().chain(s.low).map(f64::to_bits));}out.extend([q.residual_ratio.to_bits(),q.correction_ratio.to_bits()]);(out,q.iterations,q.trials)
}}}
execute!(run_reference,reference);execute!(run_reuse,reuse);
fn stored(c:&Case)->Vec<u64>{let mut v=Vec::with_capacity(1834);for s in &c.states[1..]{v.extend(s.iter().map(|x|x.to_bits()));}v.extend([c.res.to_bits(),c.corr.to_bits()]);v}
fn batch(cs:&[Case],expected:&[(Vec<u64>,usize,usize)],run:fn(&Case)->(Vec<u64>,usize,usize))->u128{let t=Instant::now();for(c,e)in cs.iter().zip(expected){let q=std::hint::black_box(run(std::hint::black_box(c)));assert_eq!(&q,e,"candidate/increment/ratio/iteration/trial bits");}t.elapsed().as_nanos()}
fn main(){
 let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),84);let mut expected=Vec::new();
 for(i,c)in cs.iter().enumerate(){let a=run_reference(c);let b=run_reuse(c);assert_eq!(a,b,"warmup reference/reuse");assert_eq!(a.0,stored(c),"stored selected pair");println!("CASE,{i},{},{},{:.17e},{},{}",c.on as u32,c.phase,c.h,a.1,a.2);expected.push(a);}
 for round in 0..5{reference::reset_profile();reuse::reset_profile();let(a,b)=if round%2==0{(batch(&cs,&expected,run_reference),batch(&cs,&expected,run_reuse))}else{let b=batch(&cs,&expected,run_reuse);(batch(&cs,&expected,run_reference),b)};let r=reference::profile();let q=reuse::profile();println!("ROUND,{round},{a},{b},{},{},{},{},{},{},{},{}",r[0],r[1],r[2],r[3],q[0],q[1],q[2],q[3]);}
 println!("PASSED,84,5,stored_and_candidate_bits");
}
