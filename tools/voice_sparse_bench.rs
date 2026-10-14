pub use rf_d_circuit::{junction_charge,StepError,vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton,block_decay_voice};
#[path="../crates/rf-d-circuit/src/dual_voice.rs"] mod baseline;
#[path="../crates/rf-d-circuit/src/sparse_ordered_voice.rs"] mod candidate;
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use baseline::{N,M,B};
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use std::{fs,time::Instant,hint::black_box};
fn chain()->Chain{let(a,b,c)=lab::lab_parameters();Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn cs(s:baseline::State)->candidate::State{candidate::State{high:s.high,low:s.low}}
fn values(a:&baseline::Parts,b:&candidate::Parts)->bool{a.dc.iter().chain(a.charge_over_h.iter()).chain(a.dc_jacobian.iter().flatten()).chain(a.mass_over_h.iter().flatten()).chain(a.candidate.high.iter()).chain(a.candidate.low.iter()).zip(b.dc.iter().chain(b.charge_over_h.iter()).chain(b.dc_jacobian.iter().flatten()).chain(b.mass_over_h.iter().flatten()).chain(b.candidate.high.iter()).chain(b.candidate.low.iter())).all(|(a,b)|a.to_bits()==b.to_bits())}
fn main(){
    let args:Vec<_>=std::env::args().collect();let bytes=fs::read(&args[1]).unwrap();assert_eq!(bytes.len(),24*2502*8);let get=|k|f64::from_le_bytes(bytes[8*k..8*k+8].try_into().unwrap());
    let mut bw=baseline::Workspace::new();let mut cw=candidate::Workspace::new();let mut linear=candidate::solver::Workspace::new();
    for c in 0..24{
        let base=c*2502;let h=get(base);let mut p=baseline::Parameters::new(chain()).unwrap();p.key=get(base+1);let mut cp=candidate::Parameters::new(chain()).unwrap();cp.key=p.key;
        let s:[baseline::State;5]=std::array::from_fn(|i|baseline::State{high:std::array::from_fn(|k|get(base+2+500*i+k)),low:std::array::from_fn(|k|get(base+2+500*i+250+k))});
        let a=baseline::parts(p,s[0],s[1],h).unwrap();let b=baseline::parts(p,s[0],s[2],h).unwrap();
        assert!(values(&a,&candidate::parts(cp,cs(s[0]),cs(s[1]),h).unwrap()));assert!(values(&b,&candidate::parts(cp,cs(s[0]),cs(s[2]),h).unwrap()));
        let j:[[f64;M];M]=std::array::from_fn(|k|std::array::from_fn(|l|B[k/N][l/N]*if l/N==0{a.mass_over_h[k%N][l%N]}else{b.mass_over_h[k%N][l%N]}+if k/N==l/N{if k/N==0{a.dc_jacobian[k%N][l%N]}else{b.dc_jacobian[k%N][l%N]}}else{0.}));
        let rhs:[f64;M]=std::array::from_fn(|k|-(if k/N==0{a.dc[k%N]}else{b.dc[k%N]}+B[k/N][0]*a.charge_over_h[k%N]+B[k/N][1]*b.charge_over_h[k%N]));
        let gold=baseline::solver::solve(j,rhs).unwrap();let got=linear.solve(&j,rhs).unwrap();let error=(0..M).fold(0_f64,|m,k|m.max((gold[k]-got[k]).abs()/if(98..133).contains(&(k%N)){2e-12}else{2e-9}));assert!(error<=1.);
        let original=bw.step(p,s[0],h).unwrap();let changed=cw.step(cp,cs(s[0]),h).unwrap();let mut stage_error=0_f64;
        for i in 0..2{for k in 0..N{let e=((original.stages[i].high[k]-changed.stages[i].high[k])+(original.stages[i].low[k]-changed.stages[i].low[k])).abs()/if(98..133).contains(&k){2e-12}else{2e-9};stage_error=stage_error.max(e);}}assert!(stage_error<=1.);
        println!("CHECK,{c},{error:.17e},{stage_error:.17e}");
        for round in 0..5{
            let base=|_|{let start=Instant::now();for _ in 0..16{black_box(baseline::solver::solve(black_box(j),black_box(rhs)).unwrap());}start.elapsed().as_secs_f64()/16.};
            let mut fast=|_|{let start=Instant::now();for _ in 0..16{black_box(linear.solve(black_box(&j),black_box(rhs)).unwrap());}start.elapsed().as_secs_f64()/16.};
            let(a,b)=if round%2==0{(base(0),fast(0))}else{let b=fast(0);let a=base(0);(a,b)};println!("ROUND,{c},{round},{a:.17e},{b:.17e}");
        }
    }
}
