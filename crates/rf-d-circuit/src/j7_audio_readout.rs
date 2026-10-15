//! Passive offline J7 voltage readout; see J7_READOUT_PROTOCOLO.md.
#[path="nominal_chain_startup.rs"]pub mod startup;
use startup::{State,Pair,Accepted};
use crate::StepError;
pub const RATE:u64=48_000;
pub const TICKS_PER_SECOND:u64=524_288_000_000;
pub const TICK_S:f64=125e-9/65536.;
const J7:usize=115;
fn voltage(s:State)->f64{s.high[J7]+s.low[J7]}
fn interpolate(old:State,p:&Pair,theta:f64)->f64{
    if theta==0.{return voltage(old);}
    if theta==1.{return voltage(p.stages[1]);}
    let a=4.5*theta*(1.-theta);let b=1.5*theta*theta-0.5*theta;
    old.high[J7]+(old.low[J7]+a*(p.delta[0].high[J7]+p.delta[0].low[J7])+b*(p.delta[1].high[J7]+p.delta[1].low[J7]))
}
/// Fixed storage, endpoint-inclusive from t=0. Values are volts, without gain.
/// No interpolated state is returned to the electrical solver.
#[derive(Clone)]
pub struct Buffer<const CAP:usize>{samples:[f64;CAP],len:usize,through:u64,last:State}
impl<const CAP:usize> Buffer<CAP>{
    pub fn new(initial:State)->Result<Self,StepError>{
        if CAP==0||!initial.valid(){return Err(StepError::InvalidInput);}
        let mut samples=[0.;CAP];samples[0]=voltage(initial);
        Ok(Self{samples,len:1,through:0,last:initial})
    }
    pub fn samples(&self)->&[f64]{&self.samples[..self.len]}
    pub fn through_ticks(&self)->u64{self.through}
    /// Caller supplies an admitted, contiguous Accepted step, with integer clock.
    /// Rejects and capacity errors publish neither samples nor new history.
    pub fn append(&mut self,old:State,q:&Accepted,start:u64,span:u64)->Result<(),StepError>{
        let end=start.checked_add(span).ok_or(StepError::InvalidInput)?;
        if start!=self.through||old!=self.last||span==0||span%2!=0
            ||q.h.to_bits()!=(span as f64*TICK_S).to_bits()
            ||!q.error.is_finite()||q.error>1.||q.error<0.
            ||q.fine.iter().any(|p|!p.residual_a.is_finite()||p.residual_a>1e-12||p.residual_a<0.
                ||!p.correction_v.is_finite()||p.correction_v>2e-9||p.correction_v<0.
                ||p.stages.iter().chain(p.delta.iter()).any(|s|!s.valid())){
            return Err(StepError::InvalidInput);
        }
        let last_index=(end as u128*RATE as u128)/TICKS_PER_SECOND as u128;
        if last_index>=CAP as u128{return Err(StepError::InvalidInput);}
        let count=last_index as usize+1;
        let value=|n:usize|{
            // All comparisons and offsets use a rational clock, without accumulation.
            let numerator=n as u128*TICKS_PER_SECOND as u128-start as u128*RATE as u128;
            let half=span as u128*RATE as u128/2;
            if numerator<=half{interpolate(old,&q.fine[0],numerator as f64/half as f64)}
            else{interpolate(q.fine[0].stages[1],&q.fine[1],(numerator-half)as f64/half as f64)}
        };
        for n in self.len..count{if !value(n).is_finite(){return Err(StepError::InvalidInput);}}
        for n in self.len..count{self.samples[n]=value(n);}
        self.len=count;self.through=end;self.last=q.fine[1].stages[1];Ok(())
    }
}
#[cfg(test)]mod tests{
    use super::*;
    #[test]fn quadratic_readout_and_endpoint_bits(){
        let old=State::new([0.;118],false);
        let delta=|theta:f64|{let mut s=old;s.high[J7]=2.*theta+3.*theta*theta;s};
        let p=Pair{delta:[delta(1./3.),delta(1.)],stages:[delta(1./3.),delta(1.)],residual_a:0.,correction_v:0.,iterations:1};
        for k in 0..=100{let t=k as f64/100.;assert!((interpolate(old,&p,t)-(2.*t+3.*t*t)).abs()<3e-15);}
        assert_eq!(interpolate(old,&p,0.).to_bits(),voltage(old).to_bits());
        assert_eq!(interpolate(old,&p,1.).to_bits(),voltage(p.stages[1]).to_bits());
    }
    #[test]fn bounded_capacity_and_atomic_retry(){
        let old=State::new([0.;118],false);let mut end=old;end.high[J7]=1.;
        let pair=||Pair{delta:[old,end],stages:[old,end],residual_a:0.,correction_v:0.,iterations:1};
        let q=Accepted{coarse:pair(),fine:[pair(),pair()],h:524288000_u64 as f64*TICK_S,error:0.,attempts:1};
        assert!(Buffer::<0>::new(old).is_err());let mut bad=old;bad.high[0]=f64::NAN;assert!(Buffer::<49>::new(bad).is_err());
        let mut a=Buffer::<49>::new(old).unwrap();let mut small=Buffer::<48>::new(old).unwrap();
        assert!(small.append(old,&q,0,524288000).is_err());assert_eq!(small.samples(),&[0.]);assert_eq!(small.through_ticks(),0);
        assert!(a.append(old,&q,1,524288000).is_err());assert!(a.append(old,&q,0,524288001).is_err());
        assert_eq!(a.samples(),&[0.]);a.append(old,&q,0,524288000).unwrap();assert_eq!(a.samples().len(),49);
        assert_eq!(a.samples()[48].to_bits(),1_f64.to_bits());let saved=a.clone();
        assert!(a.append(old,&q,0,524288000).is_err());assert_eq!(a.samples(),saved.samples());assert_eq!(a.through_ticks(),saved.through_ticks());
    }
}
