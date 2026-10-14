pub use rf_d_circuit::{junction_charge,StepError,vco1_stamp,vco_bjt,vco_jfet,lm741,vco1_newton,block_decay_voice};
#[path="../crates/rf-d-circuit/src/observed_voice.rs"] mod voice;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use voice::*;
fn same(a:State,b:State)->bool {
    a.high.iter().chain(a.low.iter()).zip(b.high.iter().chain(b.low.iter())).all(|(a,b)|a.to_bits()==b.to_bits())
}
fn main() {
    let args:Vec<_>=std::env::args().collect();let data=std::fs::read(&args[1]).unwrap();assert_eq!(data.len(),4000);
    let read=|k|f64::from_le_bytes(data[8*k..8*k+8].try_into().unwrap());
    let seed=State{high:std::array::from_fn(read),low:std::array::from_fn(|k|read(250+k))};
    let(a,b,c)=lab::lab_parameters();let p=Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap();
    let mut w=Workspace::new();
    for bad in [f64::NAN,41.] {
        let mut state=seed;state.high[0]=bad;let saved=state;
        assert!(advance(&mut w,p,&mut state,524288).is_err());assert!(same(state,saved));
    }
    let mut good=seed;advance(&mut w,p,&mut good,524288).unwrap();
    let mut fresh=seed;advance(&mut Workspace::new(),p,&mut fresh,524288).unwrap();
    assert!(same(good,fresh));println!("ROLLBACK,2,exact_valid_candidate_replay=true");
}
