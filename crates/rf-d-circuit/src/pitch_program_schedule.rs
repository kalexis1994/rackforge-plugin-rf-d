//! Immutable, fixed-size Hz/KEY score; no MIDI-to-CV calibration is implied.
use super::stream::startup::voice::phase::{Law,NOMINAL_HZ};
use crate::StepError;
const US:u64=524_288;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Event{pub ticks:u64,pub hz:f64,pub key_on:bool}
impl Event{pub const INITIAL:Self=Self{ticks:0,hz:NOMINAL_HZ,key_on:false};}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Segment{pub ticks:u64,pub law:Law,pub key_on:bool}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Program{segments:[Segment;8],len:usize,end:u64}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Profile{TwoUs,OneUs,HalfUs}
impl Profile{pub fn ticks(self)->u64{match self{Self::TwoUs=>2*US,Self::OneUs=>US,Self::HalfUs=>US/2}}}
impl Program{
    pub fn new(events:&[Event],end:u64)->Result<Self,StepError>{
        if events.is_empty()||events.len()>8||end==0||end>301000*US||end%(125*US)!=0||events[0]!=Event::INITIAL{return Err(StepError::InvalidInput);}
        let mut law=Law::nominal();let mut segments=[Segment{ticks:0,law,key_on:false};8];
        for(k,e)in events.iter().enumerate(){
            if e.ticks>=end||e.ticks%US!=0||(k>0&&e.ticks<=events[k-1].ticks){return Err(StepError::InvalidInput);}
            law=law.retune(e.ticks as f64*(125e-9/65536.),e.hz)?;segments[k]=Segment{ticks:e.ticks,law,key_on:e.key_on};
        }Ok(Self{segments,len:events.len(),end})
    }
    pub fn end_ticks(self)->u64{self.end}
    /// Caller uses 0 <= ticks < end; the right segment owns an event boundary.
    pub fn at(self,ticks:u64)->(Segment,u64){
        assert!(ticks<self.end);let mut k=0;while k+1<self.len&&self.segments[k+1].ticks<=ticks{k+=1;}
        (self.segments[k],if k+1<self.len{self.segments[k+1].ticks}else{self.end})
    }
}
#[cfg(test)]mod pitch_tests{
    use super::*;
    #[test]fn invalid_score_and_profile_domain(){
        let end=10000*US;assert!(Program::new(&[],end).is_err());assert!(Program::new(&[Event::INITIAL;9],end).is_err());for bad in[0,1,301125*US]{assert!(Program::new(&[Event::INITIAL],bad).is_err());}
        for e in[Event{ticks:1,..Event::INITIAL},Event{key_on:true,..Event::INITIAL},Event{hz:NOMINAL_HZ*2.,..Event::INITIAL}]{assert!(Program::new(&[e],end).is_err());}
        for e in[Event::INITIAL,Event{ticks:end,..Event::INITIAL},Event{ticks:US+1,..Event::INITIAL},Event{ticks:US,hz:f64::NAN,key_on:false}]{assert!(Program::new(&[Event::INITIAL,e],end).is_err());}
        assert_eq!([Profile::TwoUs.ticks(),Profile::OneUs.ticks(),Profile::HalfUs.ticks()],[2*US,US,US/2]);
    }
    #[test]fn right_event_selection_preserves_gate_only_phase(){
        let p=Program::new(&[Event::INITIAL,Event{ticks:1000*US,key_on:true,..Event::INITIAL},Event{ticks:6250*US,hz:1.5*NOMINAL_HZ,key_on:true}],10000*US).unwrap();assert!(!p.at(999*US).0.key_on);assert!(p.at(1000*US).0.key_on);assert_eq!(p.at(1000*US).0.law,Law::nominal());assert_eq!(p.at(6250*US).0.law.frequency_hz(),1.5*NOMINAL_HZ);assert_eq!(p.at(6249*US).1,6250*US);assert_eq!(p.at(6250*US).1,10000*US);
    }
}
