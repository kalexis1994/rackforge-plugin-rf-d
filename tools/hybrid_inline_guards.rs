pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/inline_hybrid_voice.rs"] mod voice;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use voice::*;
fn params()->Parameters{let(a,b,c)=lab::lab_parameters();let mut p=Parameters::new(Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap();p.time=0.04;p}
fn check<const FULL:bool>(seed:State)->usize{
    let p=params();let c=Controls{key:10.,short:false,optional:false};let d=State::new([0.;N],false);let good=parts::<FULL>(p,seed,d,c,1e-6,0.04).unwrap();
    for mode in 0..13{
        let(mut pp,mut old,mut delta,mut cc,mut h,mut t)=(p,seed,d,c,1e-6,0.04);
        match mode{
            0=>old.high[0]=f64::NAN,1=>delta.high[0]=f64::NAN,2=>old.low[0]=1.,3=>delta.low[0]=1.,
            4=>{old.high[0]=39.;old.low[0]=0.;delta.high[0]=2.;},5=>h=f64::NAN,6=>h=0.,7=>h=1e-2,
            8=>cc.key=f64::NAN,9=>cc.key=11.,10=>t=f64::NAN,11=>pp.time=f64::NAN,_=>delta.optional=true,
        }
        assert!(parts::<FULL>(pp,old,delta,cc,h,t).is_err(),"mode {mode}");
        let retry=parts::<FULL>(p,seed,d,c,1e-6,0.04).unwrap();assert_eq!(good.dc,retry.dc);assert_eq!(good.dq,retry.dq);assert_eq!(good.j,retry.j);assert_eq!(good.mass,retry.mass);assert_eq!(good.now,retry.now);
    }13
}
fn main(){let a:Vec<_>=std::env::args().collect();let b=std::fs::read(&a[1]).unwrap();assert_eq!(b.len(),16*N);let v:[f64;236]=std::array::from_fn(|k|f64::from_le_bytes(b[8*k..8*k+8].try_into().unwrap()));let seed=State{high:std::array::from_fn(|k|v[k]),low:std::array::from_fn(|k|v[N+k]),optional:false};let n=check::<true>(seed)+check::<false>(seed);println!("GUARDS,{n},exact_retry=true");}
