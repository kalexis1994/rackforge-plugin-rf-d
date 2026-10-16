//! Derived pitch variant; PITCH_PROGRAM_PROTOCOLO.md.
//! Fixed-history nominal output; STREAM_OUTPUT_PROTOCOLO.md.
#[path="pitch_program_readout.rs"]pub mod reference_readout;
#[path="j7_antialias.rs"]pub mod reference_filter;
pub use reference_readout::startup;
use startup::{State,Pair,Accepted};
use crate::StepError;
pub const INPUT_RATE:u64=384_000;
pub const OUTPUT_RATE:u64=48_000;
pub const LATENCY_INPUT_SAMPLES:u64=384;
pub const LATENCY_OUTPUT_SAMPLES:u64=48;
const LIMIT:u64=INPUT_RATE*1000+1;
const TPS:u64=reference_readout::TICKS_PER_SECOND;
const TICK:f64=reference_readout::TICK_S;
const MAX_SPAN:u64=1_048_576; // 2 us on the admitted electrical clock.
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Frame{pub source_index:u64,pub ready_input_index:u64,pub voltage_v:f64}
impl Frame{pub const EMPTY:Self=Self{source_index:0,ready_input_index:0,voltage_v:0.};}
#[derive(Clone,PartialEq)]
pub struct Decimator{ring:[f64;769],initial_v:f64,consumed:u64}
fn frames(count:u64)->u64{if count<=384{0}else{(count-385)/8+1}}
impl Decimator{
    pub fn new(initial_v:f64)->Result<Self,StepError>{
        if !initial_v.is_finite()||initial_v.abs()>=40.{return Err(StepError::InvalidInput);}
        Ok(Self{ring:[initial_v;769],initial_v,consumed:0})
    }
    pub fn consumed(&self)->u64{self.consumed}
    pub fn produced(&self)->u64{frames(self.consumed)}
    /// Whole-block preflight. No input or output is consumed on rejection.
    pub fn push(&mut self,input:&[f64],out:&mut[Frame])->Result<usize,StepError>{
        let end=self.consumed.checked_add(input.len()as u64).ok_or(StepError::InvalidInput)?;
        if end>LIMIT||(out.len()as u64)<frames(end)-frames(self.consumed)
            ||input.iter().any(|v|!v.is_finite()||v.abs()>=40.)
            ||(self.consumed==0&&!input.is_empty()&&input[0].to_bits()!=self.initial_v.to_bits()){
            return Err(StepError::InvalidInput);
        }
        let h=&reference_filter::coefficients::H384000;let mut written=0;
        for &v in input{
            let i=self.consumed;self.ring[(i%769)as usize]=v;self.consumed+=1;
            if i>=384&&(i-384)%8==0{
                let oldest=(self.consumed%769)as usize;let mut sum=0.;
                // Same oldest-to-newest coefficient order as the admitted batch FIR.
                for j in 0..769{sum+=h[j]*self.ring[(oldest+j)%769];}
                out[written]=Frame{source_index:(i-384)/8,ready_input_index:i,voltage_v:sum};written+=1;
            }
        }
        Ok(written)
    }
}
fn voltage(s:State)->f64{s.high[115]+s.low[115]}
fn interpolate(old:State,p:&Pair,theta:f64)->f64{
    if theta==0.{return voltage(old);}
    if theta==1.{return voltage(p.stages[1]);}
    let a=4.5*theta*(1.-theta);let b=1.5*theta*theta-0.5*theta;
    old.high[115]+(old.low[115]+a*(p.delta[0].high[115]+p.delta[0].low[115])+b*(p.delta[1].high[115]+p.delta[1].low[115]))
}
#[derive(Clone,PartialEq)]
pub struct Pipeline{last:State,through:u64,next_input:u64,decimator:Decimator}
impl Pipeline{
    pub fn new(initial:State)->Result<Self,StepError>{
        if !initial.valid()||initial.optional{return Err(StepError::InvalidInput);}
        let v=voltage(initial);let mut decimator=Decimator::new(v)?;decimator.push(&[v],&mut[])?;
        Ok(Self{last:initial,through:0,next_input:1,decimator})
    }
    pub fn through_ticks(&self)->u64{self.through}
    pub fn consumed(&self)->u64{self.decimator.consumed()}
    pub fn produced(&self)->u64{self.decimator.produced()}
    /// At most one new input sample for an admitted full step <=2 us.
    pub fn append(&mut self,old:State,q:&Accepted,start:u64,span:u64,out:&mut[Frame])->Result<usize,StepError>{
        let end=start.checked_add(span).ok_or(StepError::InvalidInput)?;
        if start!=self.through||old!=self.last||span==0||span%2!=0||span>MAX_SPAN||end>1000*TPS
            ||q.h.to_bits()!=(span as f64*TICK).to_bits()||!q.error.is_finite()||q.error<0.||q.error>1.
            ||q.fine.iter().any(|p|!p.residual_a.is_finite()||p.residual_a<0.||p.residual_a>1e-12
                ||!p.correction_v.is_finite()||p.correction_v<0.||p.correction_v>2e-9
                ||p.stages.iter().chain(p.delta.iter()).any(|s|!s.valid())){
            return Err(StepError::InvalidInput);
        }
        let last=(end as u128*INPUT_RATE as u128/TPS as u128)as u64;
        if last+1<self.next_input||last>self.next_input{return Err(StepError::InvalidInput);}
        let mut written=0;
        if last==self.next_input{
            let numerator=self.next_input as u128*TPS as u128-start as u128*INPUT_RATE as u128;
            let half=span as u128*INPUT_RATE as u128/2;
            let v=if numerator<=half{interpolate(old,&q.fine[0],numerator as f64/half as f64)}
                else{interpolate(q.fine[0].stages[1],&q.fine[1],(numerator-half)as f64/half as f64)};
            written=self.decimator.push(&[v],out)?;self.next_input+=1;
        }
        self.last=q.fine[1].stages[1];self.through=end;Ok(written)
    }
}
