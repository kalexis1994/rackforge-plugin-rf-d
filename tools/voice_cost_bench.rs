pub use rf_d_circuit::{junction_charge,StepError,vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton,block_decay_voice};
#[path="../crates/rf-d-circuit/src/dual_voice.rs"] mod voice;
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use voice::*;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use std::{fs,time::Instant,hint::black_box};
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn main(){
    let args:Vec<_>=std::env::args().collect();let bytes=fs::read(&args[1]).unwrap();assert_eq!(bytes.len(),24*2502*8);let get=|k|f64::from_le_bytes(bytes[8*k..8*k+8].try_into().unwrap());
    let mut pairs=Vec::new();for c in 0..24{let base=c*2502;let h=get(base);let mut p=scene();p.key=get(base+1);let states:[State;5]=std::array::from_fn(|i|State{high:std::array::from_fn(|k|get(base+2+500*i+k)),low:std::array::from_fn(|k|get(base+2+500*i+250+k))});pairs.push((h,p,states));}
    for (c,(h,p,s)) in pairs.iter().enumerate(){
        let a=parts(*p,s[0],s[1],*h).unwrap();let b=parts(*p,s[0],s[2],*h).unwrap();let j:[[f64;M];M]=std::array::from_fn(|k|std::array::from_fn(|l|B[k/N][l/N]*if l/N==0{a.mass_over_h[k%N][l%N]}else{b.mass_over_h[k%N][l%N]}+if k/N==l/N{if k/N==0{a.dc_jacobian[k%N][l%N]}else{b.dc_jacobian[k%N][l%N]}}else{0.}));
        let rhs:[f64;M]=std::array::from_fn(|k|-(if k/N==0{a.dc[k%N]}else{b.dc[k%N]}+B[k/N][0]*a.charge_over_h[k%N]+B[k/N][1]*b.charge_over_h[k%N]));
        black_box(solver::solve(j,rhs).unwrap());
        let start=Instant::now();for _ in 0..16{black_box(parts(*p,s[0],s[1],*h).unwrap());}let part=start.elapsed().as_secs_f64()/16.;
        let start=Instant::now();for _ in 0..16{black_box(solver::solve(black_box(j),black_box(rhs)).unwrap());}let solve=start.elapsed().as_secs_f64()/16.;
        println!("COST,{c},{h:.17e},{},{part:.17e},{solve:.17e}",p.key);
    }
}
