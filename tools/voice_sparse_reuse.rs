pub use rf_d_circuit::StepError;
#[path="../crates/rf-d-circuit/src/dual_voice_solver.rs"] mod baseline;
#[path="../crates/rf-d-circuit/src/sparse_ordered_voice_solver.rs"] mod candidate;
use std::fs;
fn main(){
    let args:Vec<_>=std::env::args().collect();let b=fs::read(&args[1]).unwrap();assert_eq!(b.len(),(250000+1000)*8);let f=|k|f64::from_le_bytes(b[8*k..8*k+8].try_into().unwrap());
    let j:[[f64;500];500]=std::array::from_fn(|i|std::array::from_fn(|k|f(i*500+k)));let rhs:[f64;500]=std::array::from_fn(|k|f(250000+k));
    let mut w=candidate::Workspace::new();let gold=w.solve(&j,rhs).unwrap();
    for kind in 0..5{
        let mut bad=j;let mut r=rhs;
        match kind{0=>bad[99][1]=f64::NAN,1=>r[5]=f64::INFINITY,2=>bad[0][200]=1e-5,3=>bad[0]=[0.;500],_=>bad=[[1.;500];500]}
        let expected=baseline::solve(bad,r).err();let got=w.solve(&bad,r).err();assert!(got.is_some());assert_eq!(expected,got);
        let restored=w.solve(&j,rhs).unwrap();assert!(gold.iter().zip(restored).all(|(a,b)|a.to_bits()==b.to_bits()));
        println!("REUSE,{kind},{got:?},exact_valid_direction=true");
    }
}
