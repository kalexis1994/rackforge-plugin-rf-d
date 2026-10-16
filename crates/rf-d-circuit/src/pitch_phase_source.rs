//! Experimental transposition of the admitted nominal circuit cycle.
//! PITCH_PROGRAM_PROTOCOLO.md: this is not a general physical VCO/CV model.
#[path="hybrid_phase_source.rs"]pub mod nominal;
#[path="vco_phase_profile.rs"]mod clock;
use crate::StepError;
pub const NOMINAL_HZ:f64=clock::FREQUENCY_HZ;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Law{anchor_s:f64,anchor_cycles:f64,hz:f64,legacy:bool}
impl Law{
    pub fn nominal()->Self{Self{anchor_s:0.,anchor_cycles:0.,hz:NOMINAL_HZ,legacy:true}}
    pub fn frequency_hz(self)->f64{self.hz}
    pub fn unwrapped(self,time_s:f64)->Result<f64,StepError>{
        if !time_s.is_finite()||time_s<self.anchor_s||time_s>1000.{return Err(StepError::InvalidInput);}
        Ok(if self.legacy{(time_s-clock::EPOCH_S)*NOMINAL_HZ}else{self.anchor_cycles+(time_s-self.anchor_s)*self.hz})
    }
    pub fn phase(self,time_s:f64)->Result<f64,StepError>{Ok(self.unwrapped(time_s)?.rem_euclid(1.))}
    /// A new immutable segment; callers keep the previous law for the left interval.
    pub fn retune(self,time_s:f64,hz:f64)->Result<Self,StepError>{
        if !hz.is_finite()||!(NOMINAL_HZ/2. ..=2.*NOMINAL_HZ).contains(&hz){return Err(StepError::InvalidInput);}
        let anchor=self.unwrapped(time_s)?;
        if hz.to_bits()==self.hz.to_bits(){return Ok(self);}
        Ok(Self{anchor_s:time_s,anchor_cycles:anchor,hz,legacy:false})
    }
}
pub fn observe(law:Law,time_s:f64,bus_v:f64)->Result<nominal::output::Port,StepError>{
    if !bus_v.is_finite()||bus_v.abs()>2.{return Err(StepError::InvalidInput);}
    let phase=law.phase(time_s)?;let a=&nominal::profile::KNOTS;let mut lo=0;let mut hi=a.len()-1;
    while hi-lo>1{let mid=(lo+hi)/2;if a[mid][0]<=phase{lo=mid;}else{hi=mid;}}
    let q=(phase-a[lo][0])/(a[hi][0]-a[lo][0]);
    let v=std::array::from_fn::<_,2,_>(|k|a[lo][k+1]+q*(a[hi][k+1]-a[lo][k+1]));
    nominal::output::evaluate(0.5,[v[0],v[1],0.,bus_v]).map_err(|_|StepError::InvalidInput)
}
#[cfg(test)]mod pitch_tests{
    use super::*;
    #[test]fn phase_continuity_and_pure_queries(){
        let a=Law::nominal();assert_eq!(a,a.retune(0.001,NOMINAL_HZ).unwrap());let b=a.retune(0.00625,1.5*NOMINAL_HZ).unwrap();assert_eq!(a.phase(0.00625).unwrap().to_bits(),b.phase(0.00625).unwrap().to_bits());let c=b.retune(0.0125,0.5*NOMINAL_HZ).unwrap();assert_eq!(b.phase(0.0125).unwrap().to_bits(),c.phase(0.0125).unwrap().to_bits());let saved=c;for t in[0.02,0.0125,0.018,0.015]{let x=observe(c,t,0.1).unwrap();assert_eq!(x,observe(c,t,0.1).unwrap());assert_eq!(c,saved);}
    }
    #[test]fn invalid_phase_inputs_leave_immutable_law(){
        let a=Law::nominal();for f in[f64::NAN,f64::INFINITY,0.,NOMINAL_HZ/2.-1.,2.*NOMINAL_HZ+1.]{assert!(a.retune(0.001,f).is_err());}for t in[f64::NAN,-1.,1000.1]{assert!(a.phase(t).is_err());assert!(a.retune(t,NOMINAL_HZ).is_err());}let b=a.retune(0.01,2.*NOMINAL_HZ).unwrap();assert!(b.phase(0.009).is_err());for bus in[f64::NAN,2.01,-2.01]{assert!(observe(a,0.,bus).is_err());}assert_eq!(a,Law::nominal());
    }
}
