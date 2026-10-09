//! Physical VCO terminal observations on joint Radau stages; inherited laws.
//! SVC-9 p.5; C1 balance includes Qa/Q10 collector and Q7 gate.
use crate::{joint_voice::{self as joint,State,Pair},joint_vco_fine as fine,StepError};
fn vco(s:State)->fine::State {fine::State{high:std::array::from_fn(|k|joint::vco_index(k).map_or(0.,|i|s.high[i])),low:std::array::from_fn(|k|joint::vco_index(k).map_or(0.,|i|s.low[i]))}}
pub fn stages(pair:&Pair,old:State,h:f64)->Result<[[f64;3];2],StepError> {
 let old=vco(old);let a=vco(pair.candidates[0]);let b=vco(pair.candidates[1]);
 let f=[fine::observed_currents(a,a,h),fine::observed_currents(b,b,h)].map(|r|r.map_err(|_|StepError::InvalidInput));
 let e=[fine::observed_currents(a,old,h),fine::observed_currents(b,old,h)].map(|r|r.map_err(|_|StepError::InvalidInput));
 let f=[f[0]?,f[1]?];let e=[e[0]?,e[1]?];
 let result:[[f64;3];2]=std::array::from_fn(|i|std::array::from_fn(|k|f[i][k]+joint::B[i][0]*(e[0][k]-f[0][k])+joint::B[i][1]*(e[1][k]-f[1][k])));
 if result.iter().flatten().any(|v|!v.is_finite()) {return Err(StepError::ExponentialDomain);}Ok(result)
}
