//! Same chronological FIR, with two contiguous ring spans.
#[path="../crates/rf-d-circuit/src/j7_antialias.rs"]pub mod reference_filter;
use crate::StepError;
pub const INPUT_RATE:u64=384_000;
pub const OUTPUT_RATE:u64=48_000;
pub const LATENCY_INPUT_SAMPLES:u64=384;
pub const LATENCY_OUTPUT_SAMPLES:u64=48;
const LIMIT:u64=INPUT_RATE*1000+1;
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
                let first=769-oldest;
                for (&c,&v) in h[..first].iter().zip(&self.ring[oldest..]) {sum+=c*v;}
                for (&c,&v) in h[first..].iter().zip(&self.ring[..oldest]) {sum+=c*v;}
                out[written]=Frame{source_index:(i-384)/8,ready_input_index:i,voltage_v:sum};written+=1;
            }
        }
        Ok(written)
    }
}
