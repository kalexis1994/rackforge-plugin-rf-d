//! Experimental pitch lifecycle; PITCH_RENDER_PROTOCOLO.md.
#[path="pitch_program_producer.rs"]pub mod producer;
use producer::{Producer,Stop,US,stream::{Frame,startup::{voice,Workspace}}};
use crate::StepError;
use producer::schedule::{Program,Profile};
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
    pub fn cold_start(raw:rf_d_circuit::chain_charge::Parameters,program:Program,profile:Profile,body_ms:u64)->Result<Self,StepError>{
        if !(1..=300).contains(&body_ms)||program.end_ticks()!=(body_ms+1)*1000*US{return Err(StepError::InvalidInput);}
        let producer=Producer::cold_start(raw,program,profile)?;
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
        self.run(w,quota,out,cancel,voice::advance)
    }
    // Diagnostic seam: accepted readout stays passive and never changes the solve.
    pub(crate) fn run<F>(&mut self,w:&mut Workspace,quota:usize,out:&mut[Frame],cancel:bool,advance:F)->Batch
    where F:FnMut(&mut Workspace,producer::stream::startup::Parameters,&mut producer::stream::startup::State,producer::stream::startup::Controls,f64)->Result<producer::stream::startup::Accepted,StepError>{
        if self.phase!=Phase::Running{return Batch{written:0,invocations:0,phase:self.phase};}
        if cancel{self.phase=Phase::Cancelled;return Batch{written:0,invocations:0,phase:self.phase};}
        self.pump_calls+=1;
        let r=self.producer.run(w,quota,out,advance);
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
