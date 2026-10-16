//! Offline nominal lifecycle and a separate WAV sink; NOMINAL_RENDER_PROTOCOLO.md.
#[path="nominal_offline_producer.rs"]pub mod producer;
use producer::{Producer,Stop,US,stream::{Frame,startup::{voice,Workspace}}};
use crate::StepError;
use std::io::{self,Write};
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Phase{Running,Complete,Cancelled,Fault(StepError)}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Progress{pub solved_ticks:u64,pub consumed_ticks:u64,pub target_ticks:u64,pub invocations:u64,pub accepted_steps:u64,pub observed_frames:u64,pub body_frames:u64,pub pump_calls:u64}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Batch{pub written:usize,pub invocations:usize,pub phase:Phase}
#[derive(Clone)]
pub struct RenderSession{producer:Producer,body:u64,observed:u64,pump_calls:u64,anchor:Option<Frame>,phase:Phase}
impl RenderSession{
    /// DC setup precedes cooperative pumping; body_ms is a fixed-scene prefix.
    pub fn cold_start(raw:rf_d_circuit::chain_charge::Parameters,body_ms:u64)->Result<Self,StepError>{
        if !(1..=300).contains(&body_ms){return Err(StepError::InvalidInput);}
        let producer=Producer::cold_start(raw,(body_ms+1)*1000*US)?;
        Ok(Self{producer,body:body_ms*48,observed:0,pump_calls:0,anchor:None,phase:Phase::Running})
    }
    pub fn producer(&self)->&Producer{&self.producer}
    pub fn phase(&self)->Phase{self.phase}
    pub fn anchor(&self)->Option<Frame>{self.anchor}
    pub fn progress(&self)->Progress{Progress{solved_ticks:self.producer.solved_ticks(),consumed_ticks:self.producer.output().through_ticks(),target_ticks:self.producer.end_ticks(),invocations:self.producer.invocations(),accepted_steps:self.producer.accepted_steps(),observed_frames:self.observed,body_frames:self.observed.min(self.body),pump_calls:self.pump_calls}}
    fn collect(&mut self,frames:&[Frame])->Result<usize,StepError>{
        for(k,f)in frames.iter().enumerate(){let index=self.observed+k as u64;
            if index>self.body||f.source_index!=index||f.ready_input_index!=8*index+384||!f.voltage_v.is_finite()||f.voltage_v.abs()>=1.{return Err(StepError::InvalidInput);}
        }
        let written=frames.len().min(self.body.saturating_sub(self.observed)as usize);
        if frames.len()>written{self.anchor=frames.last().copied();}
        self.observed+=frames.len()as u64;Ok(written)
    }
    /// No IO, logging or allocation here. Cancellation is terminal between calls.
    pub fn pump(&mut self,w:&mut Workspace,quota:usize,out:&mut[Frame],cancel:bool)->Batch{
        if self.phase!=Phase::Running{return Batch{written:0,invocations:0,phase:self.phase};}
        if cancel{self.phase=Phase::Cancelled;return Batch{written:0,invocations:0,phase:self.phase};}
        self.pump_calls+=1;
        // Same admitted 1 us reference: cap the requested solve, not its states.
        let r=self.producer.run(w,quota,out,|w,p,s,c,h|voice::advance(w,p,s,c,h.min(1e-6)));
        let written=match self.collect(&out[..r.written]){Ok(n)=>n,Err(e)=>{self.phase=Phase::Fault(e);return Batch{written:0,invocations:r.invocations,phase:self.phase};}};
        self.phase=match r.stop{
            Stop::Complete=>if self.observed==self.body+1&&self.anchor.is_some(){Phase::Complete}else{Phase::Fault(StepError::InvalidInput)},
            Stop::Fault(e)=>Phase::Fault(e),_=>Phase::Running,
        };
        Batch{written,invocations:r.invocations,phase:self.phase}
    }
}
fn invalid()->io::Error{io::Error::new(io::ErrorKind::InvalidData,"incomplete, invalid or failed nominal WAV")}
/// Exact IEEE-float32 mono header of the existing listening export.
fn wav_header(frames:u32)->[u8;56]{
    let mut h=[0;56];h[0..4].copy_from_slice(b"RIFF");h[4..8].copy_from_slice(&(48+4*frames).to_le_bytes());h[8..16].copy_from_slice(b"WAVEfmt ");h[16..20].copy_from_slice(&16_u32.to_le_bytes());h[20..22].copy_from_slice(&3_u16.to_le_bytes());h[22..24].copy_from_slice(&1_u16.to_le_bytes());h[24..28].copy_from_slice(&48000_u32.to_le_bytes());h[28..32].copy_from_slice(&192000_u32.to_le_bytes());h[32..34].copy_from_slice(&4_u16.to_le_bytes());h[34..36].copy_from_slice(&32_u16.to_le_bytes());h[36..40].copy_from_slice(b"fact");h[40..44].copy_from_slice(&4_u32.to_le_bytes());h[44..48].copy_from_slice(&frames.to_le_bytes());h[48..52].copy_from_slice(b"data");h[52..56].copy_from_slice(&(4*frames).to_le_bytes());h
}
/// IO belongs outside RenderSession::pump. A failed writer cannot be resumed.
pub struct WavSink<W:Write>{inner:W,expected:u64,next:u64,failed:bool,finished:bool}
impl<W:Write> WavSink<W>{
    pub fn new(mut inner:W,frames:u32)->io::Result<Self>{
        if frames==0||frames>14400{return Err(invalid());}inner.write_all(&wav_header(frames))?;
        Ok(Self{inner,expected:frames as u64,next:0,failed:false,finished:false})
    }
    pub fn frames_written(&self)->u64{self.next}
    pub fn write_frames(&mut self,frames:&[Frame])->io::Result<()>{
        if self.failed||self.finished{return Err(invalid());}
        if frames.len()as u64>self.expected-self.next||frames.iter().enumerate().any(|(k,f)|f.source_index!=self.next+k as u64||f.ready_input_index!=8*f.source_index+384||!f.voltage_v.is_finite()||f.voltage_v.abs()>=1.){self.failed=true;return Err(invalid());}
        let mut bytes=[0_u8;512];
        for block in frames.chunks(128){
            for(k,f)in block.iter().enumerate(){bytes[4*k..4*k+4].copy_from_slice(&(f.voltage_v as f32).to_le_bytes());}
            if let Err(e)=self.inner.write_all(&bytes[..4*block.len()]){self.failed=true;return Err(e);}
            self.next+=block.len()as u64;
        }Ok(())
    }
    pub fn finish(&mut self)->io::Result<()>{
        if self.finished{return Ok(());}if self.failed||self.next!=self.expected{self.failed=true;return Err(invalid());}
        if let Err(e)=self.inner.flush(){self.failed=true;return Err(e);}self.finished=true;Ok(())
    }
}
#[cfg(test)]
#[path="../tests/support/mixer_chain_lab.rs"]mod lab;
#[cfg(test)]mod tests{
    use super::*;
    fn frame(i:u64)->Frame{Frame{source_index:i,ready_input_index:8*i+384,voltage_v:0.125}}
    fn synthetic()->RenderSession{let(a,b,c)=lab::lab_parameters();let raw=rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()};let p=producer::stream::startup::Parameters::new(raw).unwrap();RenderSession{producer:Producer::from_initial(p,producer::stream::startup::State::new([0.;118],false),2000*US).unwrap(),body:48,observed:0,pump_calls:0,anchor:None,phase:Phase::Running}}
    #[test]fn body_anchor_and_terminal_cancel(){
        let mut s=synthetic();for i in 0..48{assert_eq!(s.collect(&[frame(i)]).unwrap(),1);}assert!(s.anchor.is_none());assert_eq!(s.collect(&[frame(48)]).unwrap(),0);assert_eq!(s.anchor,Some(frame(48)));assert_eq!(s.progress().body_frames,48);assert!(s.collect(&[frame(49)]).is_err());assert_eq!(s.observed,49);
        let mut s=synthetic();let mut w=Workspace::new();let old=s.progress();let mut out=[frame(99)];let sentinel=out;
        let r=s.pump(&mut w,100,&mut out,true);assert_eq!(r.phase,Phase::Cancelled);assert_eq!(r.invocations,0);assert_eq!(s.progress(),old);assert_eq!(out,sentinel);
        for cancel in[false,true]{let r=s.pump(&mut w,usize::MAX,&mut out,cancel);assert_eq!(r.phase,Phase::Cancelled);assert_eq!(r.written,0);assert_eq!(r.invocations,0);assert_eq!(out,sentinel);assert_eq!(s.progress(),old);}
    }
    #[test]fn wav_preflight_rejects_whole_block_and_requires_complete_body(){
        let mut bytes=Vec::new();{let mut s=WavSink::new(&mut bytes,2).unwrap();let mut bad=frame(1);bad.voltage_v=f64::NAN;assert!(s.write_frames(&[frame(0),bad]).is_err());assert_eq!(s.frames_written(),0);assert!(s.write_frames(&[frame(0)]).is_err());assert!(s.finish().is_err());}assert_eq!(bytes,wav_header(2));
        let mut bytes=Vec::new();{let mut s=WavSink::new(&mut bytes,2).unwrap();s.write_frames(&[frame(0)]).unwrap();assert!(s.finish().is_err());assert!(s.write_frames(&[frame(1)]).is_err());}assert_eq!(bytes.len(),60);
        let mut bytes=Vec::new();{let mut s=WavSink::new(&mut bytes,2).unwrap();s.write_frames(&[frame(0),frame(1)]).unwrap();s.finish().unwrap();s.finish().unwrap();}assert_eq!(&bytes[..56],&wav_header(2));assert_eq!(&bytes[56..60],&0.125_f32.to_le_bytes());assert_eq!(bytes.len(),64);
    }
    #[test]fn partial_io_and_flush_failures_are_terminal(){
        struct Failing{remaining:usize,flush_fail:bool}
        impl Write for Failing{fn write(&mut self,b:&[u8])->io::Result<usize>{let n=b.len().min(self.remaining);self.remaining-=n;if n==0{Err(io::Error::new(io::ErrorKind::WriteZero,"injected"))}else{Ok(n)}}fn flush(&mut self)->io::Result<()>{if self.flush_fail{Err(io::Error::new(io::ErrorKind::Other,"injected flush"))}else{Ok(())}}}
        let mut s=WavSink::new(Failing{remaining:61,flush_fail:false},2).unwrap();assert!(s.write_frames(&[frame(0),frame(1)]).is_err());assert_eq!(s.frames_written(),0);assert!(s.finish().is_err());assert!(s.write_frames(&[]).is_err());
        let mut s=WavSink::new(Failing{remaining:100,flush_fail:true},1).unwrap();s.write_frames(&[frame(0)]).unwrap();assert!(s.finish().is_err());assert!(s.finish().is_err());assert!(s.write_frames(&[]).is_err());
    }
}
