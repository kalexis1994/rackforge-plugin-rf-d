//! Experimental single-VCO voice. See MONO_VOICE_PROTOCOLO.md for domain.
//! Own DC + physical nominal contours/trigger/filter/VCAs + causal 1 ms FIR.
//! Not admitted for real-time use; nominal transposition, not H128/CV dynamics.
#[path="pitch_program_output.rs"] pub mod stream;
use stream::{Frame,Pipeline,startup::{self,voice,State,Parameters,Controls}};
pub use startup::Workspace;
use crate::StepError;
const TPS:u64=stream::reference_readout::TICKS_PER_SECOND;
const TICK:f64=stream::reference_readout::TICK_S;
const US:u64=524_288;
const GRID:u64=125*US;
pub const MAX_BLOCK:usize=128;
pub const RATE:u64=48_000;
pub const LATENCY:usize=48;

#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Message{NoteOn{note:u8,velocity:u8},NoteOff{note:u8},AllNotesOff}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Event{pub offset:usize,pub message:Message}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Notes{held:[bool;128]}
impl Default for Notes{fn default()->Self{Self{held:[false;128]}}}
impl Notes{
    pub fn lowest(self)->Option<u8>{self.held.iter().position(|v|*v).map(|n|n as u8)}
    pub fn hz(note:u8)->Result<f64,StepError>{
        if note>127{return Err(StepError::InvalidInput);}
        let f=440.*2_f64.powf((note as f64-69.)/12.);
        if !(voice::phase::NOMINAL_HZ/2. ..=2.*voice::phase::NOMINAL_HZ).contains(&f){return Err(StepError::InvalidInput);}
        Ok(f)
    }
    pub fn apply(&mut self,m:Message)->Result<(),StepError>{
        match m{
            Message::NoteOn{note,velocity}=>{
                if note>127||velocity>127{return Err(StepError::InvalidInput);}
                if velocity!=0{Self::hz(note)?;}self.held[note as usize]=velocity!=0;
            }
            Message::NoteOff{note}=>{if note>127{return Err(StepError::InvalidInput);}self.held[note as usize]=false;}
            Message::AllNotesOff=>self.held=[false;128],
        }Ok(())
    }
}
#[derive(Clone,Copy,Debug,Default)]
pub struct Stats{pub calls:u64,pub attempts:u64,pub iterations:u64,pub max_residual_a:f64,pub max_correction_v:f64,pub max_error:f64}
impl Stats{
    fn accept(&mut self,q:&startup::Accepted){self.calls+=1;self.attempts+=q.attempts as u64;self.max_error=self.max_error.max(q.error);
        for p in [&q.coarse,&q.fine[0],&q.fine[1]]{self.iterations+=p.iterations as u64;self.max_residual_a=self.max_residual_a.max(p.residual_a);self.max_correction_v=self.max_correction_v.max(p.correction_v);}
    }
}
/// Absolute sample boundary rounded upward by <8 ticks (half-step >= MIN_DT).
pub fn sample_ticks(sample:u64)->Result<u64,StepError>{
    if sample>1000*RATE{return Err(StepError::InvalidInput);}
    Ok((((sample as u128*TPS as u128)+(8*RATE-1)as u128)/(8*RATE)as u128*8)as u64)
}
#[derive(Clone)]
pub struct Voice{
    base:Parameters,state:State,notes:Notes,law:voice::phase::Law,
    pipeline:Pipeline,ready:Option<Frame>,sample:u64,ticks:u64,next_grid:u64,
    proposal:u64,maximum:u64,
}
impl Voice{
    pub fn cold_start(raw:rf_d_circuit::chain_charge::Parameters)->Result<Self,StepError>{Self::cold_start_refined(raw,false)}
    /// .25 us is a refinement reference, never an automatic quality switch.
    pub fn cold_start_refined(raw:rf_d_circuit::chain_charge::Parameters,refined:bool)->Result<Self,StepError>{
        let s=startup::cold_start(raw)?.state;let maximum=if refined{US/4}else{US/2};
        Ok(Self{base:Parameters::new(raw)?,state:s,notes:Notes::default(),law:voice::phase::Law::nominal(),pipeline:Pipeline::new(s)?,ready:None,sample:0,ticks:0,next_grid:GRID,proposal:maximum,maximum})
    }
    pub fn state(&self)->State{self.state}
    pub fn notes(&self)->Notes{self.notes}
    pub fn samples(&self)->u64{self.sample}
    pub fn ticks(&self)->u64{self.ticks}
    pub fn phase_law(&self)->voice::phase::Law{self.law}
    pub fn output(&self)->&Pipeline{&self.pipeline}
    fn preflight(&self,events:&[Event],n:usize)->Result<(),StepError>{
        if n==0||n>MAX_BLOCK||events.len()>256{return Err(StepError::InvalidInput);}
        sample_ticks(self.sample.checked_add(n as u64).ok_or(StepError::InvalidInput)?)?;
        let mut notes=self.notes;let mut previous=0;
        for(k,e)in events.iter().enumerate(){if e.offset>=n||(k>0&&e.offset<previous){return Err(StepError::InvalidInput);}notes.apply(e.message)?;previous=e.offset;}
        Ok(())
    }
    fn deliver(&mut self,f:Frame,start:u64,out:&mut[f64],count:&mut usize)->Result<(),StepError>{
        let index=f.source_index+LATENCY as u64;let end=start+out.len()as u64;
        if f.ready_input_index!=8*index||!f.voltage_v.is_finite(){return Err(StepError::InvalidInput);}
        if index==end{if self.ready.is_some(){return Err(StepError::InvalidInput);}self.ready=Some(f);return Ok(());}
        if index<start||index>=end||index!=start.max(LATENCY as u64)+*count as u64{return Err(StepError::InvalidInput);}
        out[(index-start)as usize]=f.voltage_v;*count+=1;Ok(())
    }
    fn until(&mut self,w:&mut Workspace,target:u64,start:u64,out:&mut[f64],count:&mut usize,stats:&mut Stats)->Result<(),StepError>{
        while self.ticks<target{
            let remain=target.min(self.next_grid)-self.ticks;
            let span=self.proposal.min(1_u64<<(63-remain.leading_zeros()));
            let mut p=self.base;p.time=self.ticks as f64*TICK;p.pitch=self.law;
            let c=Controls{key:if self.notes.lowest().is_some(){10.}else{0.},short:false,optional:false};
            let old=self.state;let q=voice::advance(w,p,&mut self.state,c,span as f64*TICK)?;
            let actual=(q.h/TICK).round()as u64;
            if actual==0||actual%2!=0||actual>span||q.h.to_bits()!=(actual as f64*TICK).to_bits(){return Err(StepError::InvalidInput);}
            let mut frame=[Frame::EMPTY;1];let n=self.pipeline.append(old,&q,self.ticks,actual,&mut frame)?;
            stats.accept(&q);self.ticks+=actual;self.proposal=if q.error<0.05{(2*actual).min(self.maximum)}else{actual};
            if self.ticks==self.next_grid{self.next_grid+=GRID;}
            if n==1{self.deliver(frame[0],start,out,count)?;}
        }Ok(())
    }
    /// Whole-block transaction: no state/audio publication after any rejection.
    /// Workspace is scratch. Timers/IO/allocations belong to the caller.
    pub fn render_block(&mut self,w:&mut Workspace,events:&[Event],out:&mut[f64])->Result<Stats,StepError>{
        self.preflight(events,out.len())?;
        let mut next=self.clone();let mut audio=[0.;MAX_BLOCK];let out_local=&mut audio[..out.len()];
        let start=self.sample;let mut count=0;let mut stats=Stats::default();
        if let Some(f)=next.ready.take(){next.deliver(f,start,out_local,&mut count)?;}
        for e in events{
            let tick=sample_ticks(start+e.offset as u64)?;next.until(w,tick,start,out_local,&mut count,&mut stats)?;
            next.notes.apply(e.message)?;
            if let Some(note)=next.notes.lowest(){next.law=next.law.retune(tick as f64*TICK,Notes::hz(note)?)?;}
        }
        next.sample=start+out.len()as u64;
        next.until(w,sample_ticks(next.sample)?,start,out_local,&mut count,&mut stats)?;
        if count as u64!=next.sample.saturating_sub(LATENCY as u64)-start.saturating_sub(LATENCY as u64){return Err(StepError::InvalidInput);}
        out.copy_from_slice(out_local);*self=next;Ok(stats)
    }
}

#[cfg(test)]mod mono_tests{
    use super::*;
    #[test]fn low_priority_legato_and_release(){let mut n=Notes::default();for note in[69,72,67,67]{n.apply(Message::NoteOn{note,velocity:100}).unwrap();}assert_eq!(n.lowest(),Some(67));n.apply(Message::NoteOff{note:67}).unwrap();assert_eq!(n.lowest(),Some(69));n.apply(Message::NoteOn{note:69,velocity:0}).unwrap();assert_eq!(n.lowest(),Some(72));n.apply(Message::AllNotesOff).unwrap();assert_eq!(n.lowest(),None);}
    #[test]fn note_domain_and_invalid_transaction(){let mut n=Notes::default();for note in 0..=127{let old=n;let q=n.apply(Message::NoteOn{note,velocity:1});assert_eq!(q.is_ok(),(56..=79).contains(&note));if q.is_err(){assert_eq!(old,n);}}let old=n;for m in[Message::NoteOn{note:255,velocity:1},Message::NoteOn{note:69,velocity:255},Message::NoteOff{note:255}]{assert!(n.apply(m).is_err());assert_eq!(old,n);}assert_eq!(Notes::hz(69).unwrap(),440.);}
    #[test]fn rational_sample_clock(){for s in[0,1,47,48,64,127,128,480,47_999_999,48_000_000]{let t=sample_ticks(s).unwrap();assert_eq!(t%8,0);let numerator=s as u128*TPS as u128;assert!(t as u128*RATE as u128>=numerator);assert!((t as u128*RATE as u128)-numerator<8*RATE as u128);}assert!(sample_ticks(48_000_001).is_err());}
    #[test]fn phase_retune_keeps_gate_and_legato_continuity(){let mut law=voice::phase::Law::nominal();for(i,note)in[69,72,69,67].into_iter().enumerate(){let time=sample_ticks(48*(i as u64+1)).unwrap()as f64*TICK;let old=law;law=law.retune(time,Notes::hz(note).unwrap()).unwrap();assert_eq!(old.phase(time).unwrap().to_bits(),law.phase(time).unwrap().to_bits());assert_eq!(law,law.retune(time,Notes::hz(note).unwrap()).unwrap());}}
}
