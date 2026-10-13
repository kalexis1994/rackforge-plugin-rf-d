//! Laboratory-only paired cost measurement; heap/timers are outside audio admission.
#[path="joint_lu_extent_kernel.rs"] mod original;
#[path="joint_schur_chain_kernel.rs"] mod reference;
#[path="joint_radau_inplace_kernel.rs"] mod reuse;
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
execute!(run_original,original);execute!(run_reference,reference);execute!(run_reuse,reuse);
fn stored(c:&Case)->Vec<u64>{let mut v=Vec::with_capacity(1834);for s in &c.states[1..]{v.extend(s.iter().map(|x|x.to_bits()));}v.extend([c.res.to_bits(),c.corr.to_bits()]);v}
fn batch(cs:&[Case],expected:&[(Vec<u64>,usize,usize)],run:fn(&Case)->(Vec<u64>,usize,usize))->u128{let t=Instant::now();for(c,e)in cs.iter().zip(expected){let q=std::hint::black_box(run(std::hint::black_box(c)));assert_eq!(&q,e,"candidate/increment/ratio/iteration/trial bits");}t.elapsed().as_nanos()}
fn compare(a:&(Vec<u64>,usize,usize),b:&(Vec<u64>,usize,usize))->f64{
 let mut worst=0_f64;for block in 0..4{for k in 0..229{let q=block*458;let ah=f64::from_bits(a.0[q+k]);let al=f64::from_bits(a.0[q+k+229]);let bh=f64::from_bits(b.0[q+k]);let bl=f64::from_bits(b.0[q+k+229]);let diff=(ah-bh)+(al-bl);let ratio=diff.abs()/if(98..133).contains(&k){2e-9}else{2e-6};worst=worst.max(ratio);}}
 assert!(worst<=1.,"full candidate/increment gate {worst}");assert!(f64::from_bits(b.0[1832])<=1.&&f64::from_bits(b.0[1833])<=1.,"original Newton gates");worst
}
fn save(w:&mut impl std::io::Write,c:&Case,q:&(Vec<u64>,usize,usize)){
 writeln!(w,"SCENE,{},{}",c.on as u32,c.phase).unwrap();writeln!(w,"JOINT_ROOT,0,{:.17e},{:.17e},{:.17e}",c.h,f64::from_bits(q.0[1832]),f64::from_bits(q.0[1833])).unwrap();write!(w,"JOINT_STATE").unwrap();for v in c.states[0]{write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();for block in 0..4{write!(w,"JOINT_STATE").unwrap();for &v in &q.0[block*458..(block+1)*458]{write!(w,",{:.17e}",f64::from_bits(v)).unwrap();}writeln!(w).unwrap();}
}
fn main(){
 let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),84);let mut expected=Vec::new();let mut file=std::fs::File::create(&args[2]).unwrap();
 for(i,c)in cs.iter().enumerate(){let raw=run_original(c);assert_eq!(raw.0,stored(c),"original stored bits");let a=run_reference(c);compare(&raw,&a);let b=run_reuse(c);let error=compare(&raw,&b);assert_eq!(a,b,"in-place candidate/increment/ratio/iteration/trial bits");save(&mut file,c,&b);println!("CASE,{i},{},{},{:.17e},{},{},{},{},{error:.17e}",c.on as u32,c.phase,c.h,a.1,a.2,b.1,b.2);expected.push(a);}
 for c in &cs{std::hint::black_box(run_reference(c));std::hint::black_box(run_reuse(c));}
 for round in 0..5{let reference=|cs:&[Case]|{let t=Instant::now();for(c,e)in cs.iter().zip(&expected){assert_eq!(&run_reference(c),e);}t.elapsed().as_nanos()};let reduced=|cs:&[Case]|{let t=Instant::now();for(c,e)in cs.iter().zip(&expected){assert_eq!(&run_reuse(c),e,"in-place timed root identity");}t.elapsed().as_nanos()};let(a,b)=if round%2==0{(reference(&cs),reduced(&cs))}else{let b=reduced(&cs);(reference(&cs),b)};println!("ROUND,{round},{a},{b}");}
 println!("PASSED,84,5,reconstructed_candidate_gates");
}
