use rf_d_circuit::{chain_charge::{self,State,N},StepError};
#[path="charge_control_oracle.rs"]mod base;
use std::io::{BufWriter,Write};
// Self-contained reconstruction of the published bench boundary.
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
fn parameters(cutoff:f64)->chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();let mut boundary=lab::controlled_boundary(0,true);boundary.panel.cutoff_fraction_from_neg10=cutoff;chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary,mixer:rf_d_circuit::mixer_on::OnMixer::new([false,true,true,true,true],[0.5;4]).unwrap()}}
fn main()->Result<(),Box<dyn std::error::Error>>{
 let mut bytes=Vec::new();std::io::Read::read_to_end(&mut std::io::stdin().lock(),&mut bytes)?;let rows=bytes.len()/(136*8);assert_eq!(bytes.len(),rows*136*8);let mut out=BufWriter::new(std::io::stdout().lock());
 for block in bytes.chunks_exact(136*8){let mut values=[0.;136];for(k,b)in block.chunks_exact(8).enumerate(){values[k]=f64::from_le_bytes(b.try_into().unwrap());}let s=State{high:std::array::from_fn(|k|values[k]),low:std::array::from_fn(|k|values[68+k])};let a=chain_charge::linearize_compensated(parameters(0.5),[0.;5],s,State::from_nodes([0.;N]),1e-6).map_err(|e|format!("STAMP:{e:?}"))?;for v in a.dc.into_iter().chain(a.dc_jacobian.into_iter().flatten()){out.write_all(&v.to_le_bytes())?;}
 }out.flush()?;Ok(())}
