//! Passive 384 kHz nominal readout; see LONG_NOTE_AA_PROTOCOLO.md.
#[path="nominal_chain_startup.rs"]pub mod startup;
use startup::{State,Pair,Accepted};
use crate::StepError;
pub const RATE:u64=384_000;
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
