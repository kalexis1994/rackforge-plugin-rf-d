//! Compatible Ebers-Moll/depletion/low-injection charge for Q25/Q15.
//! Synthetic laboratory parameters; not an identified 2N3392.
use rf_d_circuit::{junction_charge::Parameters as Depletion,StepError};
pub const VT:f64=1.380649e-23*298.15/1.602176634e-19;
pub const BE:Depletion=Depletion{zero_bias_capacitance_f:7e-12,potential_v:0.75,grading:0.5,forward_fraction:0.4};
pub const BC:Depletion=Depletion{zero_bias_capacitance_f:5e-12,potential_v:0.7,grading:0.33,forward_fraction:0.4};
// Return Q increment and dQ/dV, keeping high/low histories distinct.
pub fn junction(law:Depletion,t:f64,old:(f64,f64),now:(f64,f64))->Result<(f64,f64),StepError>{
 let (a,al)=old;let(b,bl)=now;
 if a/VT>45.||b/VT>45.||![al,bl,t].iter().all(|v|v.is_finite())||t<0. {return Err(StepError::ExponentialDomain);}
 let ca=law.charge(a).map_err(|_|StepError::ExponentialDomain)?.capacitance_f+t*1e-14*(a/VT).exp()/VT;
 let cb=law.charge(b).map_err(|_|StepError::ExponentialDomain)?.capacitance_f+t*1e-14*(b/VT).exp()/VT;
 let dq=law.charge_increment(a,b).map_err(|_|StepError::ExponentialDomain)?+t*1e-14*(a/VT).exp()*((b-a)/VT).exp_m1()+cb*bl-ca*al;
 if !dq.is_finite()||!cb.is_finite(){return Err(StepError::ExponentialDomain);}Ok((dq,cb))
}
pub fn terminal(old:[(f64,f64);2],now:[(f64,f64);2])->Result<([f64;2],[[f64;2];2]),StepError>{
 let difference=|a:(f64,f64),b:(f64,f64)|{let h=a.0-b.0;let v=h-a.0;let e=(a.0-(h-v))+(-b.0-v);(h,e+a.1-b.1)};
 let bc_old=difference(old[0],old[1]);
 let bc_now=difference(now[0],now[1]);
 let(qbe,cbe)=junction(BE,1e-9,old[0],now[0])?;
 let(qbc,cbc)=junction(BC,3e-9,bc_old,bc_now)?;
 Ok(([qbe+qbc,-qbc],[[cbe+cbc,-cbc],[-cbc,cbc]]))
}
