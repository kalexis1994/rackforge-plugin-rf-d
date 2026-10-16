//! Derived pitch variant; PITCH_PROGRAM_PROTOCOLO.md.
//! Cooperative OFFLINE scheduling for the admitted nominal scene.
//! See OFFLINE_PRODUCER_PROTOCOLO.md. A work quota is not a CPU deadline.
#[path="pitch_program_output.rs"]pub mod stream;
#[path="pitch_program_schedule.rs"]pub mod schedule;
use schedule::{Program,Profile};
use stream::{Frame,Pipeline,startup::{self,voice,Accepted,Pair,State,Parameters,Controls,Workspace}};
use crate::StepError;
pub const US:u64=524_288;
pub const END_TICKS:u64=301_000*US;
const GRID:u64=125*US;

const TICK:f64=stream::reference_readout::TICK_S;
const TPS:u64=stream::reference_readout::TICKS_PER_SECOND;
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum Stop{WorkQuota,OutputFull,Complete,Fault(StepError)}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Report{pub written:usize,pub invocations:usize,pub published_steps:usize,pub stop:Stop}
/// Immutable inspection of the single solved step not yet consumed by Pipeline.
pub struct Pending{pub old:State,pub accepted:Accepted,pub start:u64,pub span:u64}
fn copy_pair(p:&Pair)->Pair{Pair{delta:p.delta,stages:p.stages,residual_a:p.residual_a,correction_v:p.correction_v,iterations:p.iterations}}
impl Clone for Pending{
    fn clone(&self)->Self{let q=&self.accepted;Self{old:self.old,start:self.start,span:self.span,accepted:Accepted{coarse:copy_pair(&q.coarse),fine:[copy_pair(&q.fine[0]),copy_pair(&q.fine[1])],h:q.h,error:q.error,attempts:q.attempts}}}
}
#[derive(Clone)]
pub struct Producer{
    base:Parameters,state:State,solved:u64,end:u64,next_grid:u64,proposal:u64,program:Program,maximum:u64,
    output:Pipeline,pending:Option<Pending>,calls:u64,steps:u64,fault:Option<StepError>,
}
fn frame_count(end:u64)->u64{let i=(end as u128*stream::INPUT_RATE as u128/TPS as u128)as u64;if i<384{0}else{(i-384)/8+1}}
impl Producer{
    /// Same own DC, before any program event; initial program is nominal/KEY OFF.
    pub fn cold_start(raw:rf_d_circuit::chain_charge::Parameters,program:Program,profile:Profile)->Result<Self,StepError>{
        let initial=startup::cold_start(raw)?;Self::from_initial(Parameters::new(raw)?,initial.state,program,profile)
    }
    pub fn from_initial(base:Parameters,initial:State,program:Program,profile:Profile)->Result<Self,StepError>{
        if base.time.to_bits()!=0_f64.to_bits()||base.pitch!=voice::phase::Law::nominal(){return Err(StepError::InvalidInput);}
        let maximum=profile.ticks();Ok(Self{base,state:initial,solved:0,end:program.end_ticks(),next_grid:GRID,proposal:maximum,program,maximum,output:Pipeline::new(initial)?,pending:None,calls:0,steps:0,fault:None})
    }
    pub fn program(&self)->Program{self.program}
    pub fn state(&self)->State{self.state}
    pub fn solved_ticks(&self)->u64{self.solved}
    pub fn end_ticks(&self)->u64{self.end}
    pub fn next_grid_ticks(&self)->u64{self.next_grid}
    pub fn proposal_ticks(&self)->u64{self.proposal}
    pub fn output(&self)->&Pipeline{&self.output}
    pub fn pending(&self)->Option<&Pending>{self.pending.as_ref()}
    pub fn invocations(&self)->u64{self.calls}
    pub fn accepted_steps(&self)->u64{self.steps}
    /// Partial call progress is reported even on Fault. A fault is terminal.
    /// Quota zero may drain a pending step; it never invokes the solver.
    pub fn pump(&mut self,w:&mut Workspace,quota:usize,out:&mut[Frame])->Report{
        self.run(w,quota,out,voice::advance)
    }
    // Crate-only substitution seam for native fault/control verification.
    pub(crate) fn run<F>(&mut self,w:&mut Workspace,quota:usize,out:&mut[Frame],mut advance:F)->Report
    where F:FnMut(&mut Workspace,Parameters,&mut State,Controls,f64)->Result<Accepted,StepError>{
        let mut r=Report{written:0,invocations:0,published_steps:0,stop:Stop::WorkQuota};
        loop{
            if let Some(e)=self.fault{r.stop=Stop::Fault(e);return r;}
            if let Some(p)=self.pending.as_ref(){
                let needed=frame_count(p.start+p.span)-self.output.produced();
                if needed>(out.len()-r.written)as u64{r.stop=Stop::OutputFull;return r;}
                match self.output.append(p.old,&p.accepted,p.start,p.span,&mut out[r.written..]){
                    Ok(n)=>{r.written+=n;r.published_steps+=1;self.pending=None;}
                    Err(e)=>{self.fault=Some(e);r.stop=Stop::Fault(e);return r;}
                }
            }
            if self.solved==self.end{r.stop=Stop::Complete;return r;}
            if r.invocations==quota{return r;}
            let (segment,event_end)=self.program.at(self.solved);
            let remain=event_end.min(self.next_grid)-self.solved;
            let span=self.proposal.min(1_u64<<(63-remain.leading_zeros()));
            let mut parameters=self.base;parameters.time=self.solved as f64*TICK;parameters.pitch=segment.law;
            let controls=Controls{key:if segment.key_on{10.}else{0.},short:false,optional:false};let old=self.state;
            // Integrate into a local candidate, retaining the last coherent state on error.
            let mut candidate=old;r.invocations+=1;self.calls+=1;
            let q=match advance(w,parameters,&mut candidate,controls,span as f64*TICK){
                Ok(q)=>q,Err(e)=>{self.fault=Some(e);r.stop=Stop::Fault(e);return r;}
            };
            let actual=(q.h/TICK).round()as u64;
            // Internal engine contract, never interpreted as output backpressure.
            if actual==0||actual%2!=0||actual>span||q.h.to_bits()!=(actual as f64*TICK).to_bits()
                ||candidate!=q.fine[1].stages[1]||!q.error.is_finite()||q.error<0.||q.error>1.{
                self.fault=Some(StepError::InvalidInput);r.stop=Stop::Fault(StepError::InvalidInput);return r;
            }
            self.pending=Some(Pending{old,accepted:q,start:self.solved,span:actual});
            let error=self.pending.as_ref().unwrap().accepted.error;
            self.state=candidate;self.solved+=actual;self.steps+=1;
            self.proposal=if error<0.05{(2*actual).min(self.maximum)}else{actual};
            if self.solved==self.next_grid{self.next_grid+=GRID;}
        }
    }
}
