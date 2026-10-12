//! Matrix export only, at archived DC candidates. No root or trajectory solve.
use rf_d_circuit::{chain_charge::{self,Parameters},mixer_on::OnMixer};
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use std::{fs::File,io::{Read,Write,BufWriter}};
fn main() {
 let args:Vec<String>=std::env::args().collect();let mut data=Vec::new();File::open(&args[1]).unwrap().read_to_end(&mut data).unwrap();assert_eq!(&data[..8],b"RFCUTI01");assert_eq!(data.len(),8+3*69*8);
 let mut out=BufWriter::new(File::create(&args[2]).unwrap());out.write_all(b"RFCUTO01").unwrap();
 for id in 0..3 {
  let values:[f64;69]=std::array::from_fn(|k|{let i=8+8*(69*id+k);f64::from_le_bytes(data[i..i+8].try_into().unwrap())});
  let(a,b,c)=lab::lab_parameters();let mut boundary=lab::controlled_boundary(0,true);boundary.panel.cutoff_fraction_from_neg10=values[0];let p=Parameters{circuit:a,conversion:b,headphone:c,boundary,mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
  let old=chain_charge::State::from_nodes(std::array::from_fn(|k|values[k+1]));let s=chain_charge::linearize_compensated(p,[0.,0.2,-0.3,0.1,0.4],old,chain_charge::State::from_nodes([0.;68]),125e-9).unwrap();
  for v in std::iter::once(values[0]).chain(old.high).chain(s.dc).chain(s.dc_jacobian.into_iter().flatten()).chain(s.mass_over_h.into_iter().flatten().map(|v|v*125e-9)) {assert!(v.is_finite());out.write_all(&v.to_le_bytes()).unwrap();}
 }out.flush().unwrap();
}
