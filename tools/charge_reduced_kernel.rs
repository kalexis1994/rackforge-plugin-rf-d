//! Fixed-control small-signal charge kernel. No full-voice or large-signal claim.
#[path="charge_reduced_data.rs"]mod data;
pub const N:usize=18;
#[derive(Clone,Copy,Debug,PartialEq)]pub struct State{pub q:[f64;N],pub input_v:f64}
impl State{pub const ZERO:Self=Self{q:[0.;N],input_v:0.};}
#[derive(Clone,Copy,Debug)]pub struct Output{pub bus_v:f64,pub base_v:f64,pub j7_v:f64,pub panel_a:f64}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum Error{InvalidInput}
pub fn nodes(case:usize,s:State)->Result<[f64;68],Error>{
 if case>=2||!s.input_v.is_finite()||s.q.iter().any(|v|!v.is_finite()){return Err(Error::InvalidInput);}
 Ok(std::array::from_fn(|i|{let mut v=data::XU[case][i]*s.input_v;for k in 0..N{v+=data::XQ[case][i][k]*s.q[k];}v}))
}
pub fn step(case:usize,s:&mut State,input_v:f64)->Result<Output,Error>{
 if case>=2||!input_v.is_finite()||input_v.abs()>1.3e-3||!s.input_v.is_finite()||s.q.iter().any(|v|!v.is_finite()){return Err(Error::InvalidInput);}
 let mut q=[0.;N];for i in 0..N{let mut v=0.;for k in 0..N{v+=data::F[case][i][k]*s.q[k];}q[i]=v+data::U0[case][i]*s.input_v+data::U1[case][i]*input_v;}
 if q.iter().any(|v|!v.is_finite()){return Err(Error::InvalidInput);}
 let value=|i:usize|{let mut v=data::XU[case][i]*input_v;for k in 0..N{v+=data::XQ[case][i][k]*q[k];}v};
 let bus=value(66);let out=Output{bus_v:bus,base_v:value(6),j7_v:value(61),panel_a:(bus-0.5*input_v)/39250.};
 if [out.bus_v,out.base_v,out.j7_v,out.panel_a].iter().any(|v|!v.is_finite()){return Err(Error::InvalidInput);}
 *s=State{q,input_v};Ok(out)
}
