//! Derivative of the saved linear crossing observer, not a continuous root.
use rf_d_circuit::{joint_voice as j,joint_engine};
use crate::joint_history_propagation::{R,Sensitivity};
pub struct Event {pub alpha:f64,pub state:j::State,pub dalpha:[f64;R],pub dt:[f64;R],pub response:[[f64;R];j::N]}
pub fn crossing(a:j::State,b:j::State,h:f64,sa:Sensitivity,sb:Sensitivity)->Event {
 let ra=a.high[43]+a.low[43];let rb=b.high[43]+b.low[43];assert!(ra< -2. && rb>= -2. && rb>ra && h>0.);
 let alpha=(-2.-ra)/(rb-ra);assert!((0. ..=1.).contains(&alpha));let difference=joint_engine::difference(b,a);
 let state=a.advanced(difference.map(|v|alpha*v));
 let dalpha=std::array::from_fn(|r|-((1.-alpha)*sa[j::N+43][r]+alpha*sb[j::N+43][r])/(rb-ra));
 let dt=dalpha.map(|v|h*v);
 let response=std::array::from_fn(|k|std::array::from_fn(|r|(1.-alpha)*sa[j::N+k][r]+alpha*sb[j::N+k][r]+difference[k]*dalpha[r]));
 Event{alpha,state,dalpha,dt,response}
}
