//! Cooperative OFFLINE scheduling for the admitted nominal scene.
//! See OFFLINE_PRODUCER_PROTOCOLO.md. A work quota is not a CPU deadline.
#[path="j7_stream_output.rs"]pub mod stream;
use stream::{Frame,Pipeline,startup::{self,voice,Accepted,Pair,State,Parameters,Controls,Workspace}};
use crate::StepError;
pub const US:u64=524_288;
pub const END_TICKS:u64=301_000*US;
const GRID:u64=125*US;
const MAXIMUM:u64=2*US;
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
    base:Parameters,state:State,solved:u64,end:u64,next_grid:u64,proposal:u64,
    output:Pipeline,pending:Option<Pending>,calls:u64,steps:u64,fault:Option<StepError>,
}
fn key(t:u64)->f64{if (1000*US..200_000*US).contains(&t){10.}else{0.}}
fn edge(t:u64,end:u64,grid:u64)->u64{
    let event=if t<1000*US{1000*US}else if t<200_000*US{200_000*US}else{end};
    end.min(grid).min(event)
}
fn frame_count(end:u64)->u64{let i=(end as u128*stream::INPUT_RATE as u128/TPS as u128)as u64;if i<384{0}else{(i-384)/8+1}}
impl Producer{
    /// DC setup is outside the cooperative work quota.
    pub fn cold_start(raw:rf_d_circuit::chain_charge::Parameters,end:u64)->Result<Self,StepError>{
        Self::validate_end(end)?;let initial=startup::cold_start(raw)?;Self::from_initial(Parameters::new(raw)?,initial.state,end)
    }
    fn validate_end(end:u64)->Result<(),StepError>{if end==0||end>END_TICKS||end%GRID!=0{Err(StepError::InvalidInput)}else{Ok(())}}
    /// A valid representation at time zero does not by itself prove electrical DC.
    pub fn from_initial(base:Parameters,initial:State,end:u64)->Result<Self,StepError>{
        Self::validate_end(end)?;if base.time.to_bits()!=0_f64.to_bits(){return Err(StepError::InvalidInput);}
        Ok(Self{base,state:initial,solved:0,end,next_grid:GRID,proposal:MAXIMUM,output:Pipeline::new(initial)?,pending:None,calls:0,steps:0,fault:None})
    }
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
            let remain=edge(self.solved,self.end,self.next_grid)-self.solved;
            let span=self.proposal.min(1_u64<<(63-remain.leading_zeros()));
            let mut parameters=self.base;parameters.time=self.solved as f64*TICK;
            let controls=Controls{key:key(self.solved),short:false,optional:false};let old=self.state;
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
            self.proposal=if error<0.05{(2*actual).min(MAXIMUM)}else{actual};
            if self.solved==self.next_grid{self.next_grid+=GRID;}
        }
    }
}
#[cfg(test)]
#[path="../tests/support/mixer_chain_lab.rs"]mod lab;
#[cfg(test)]mod tests{
    use super::*;
    fn parameters()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
    fn fake(h:f64,s:State)->Accepted{let p=||Pair{delta:[State::new([0.;118],false);2],stages:[s;2],residual_a:0.,correction_v:0.,iterations:1};Accepted{coarse:p(),fine:[p(),p()],h,error:0.,attempts:1}}
    #[test]fn constructor_and_event_boundaries(){
        let p=parameters();let s=State::new([0.;118],false);
        for end in[0,1,GRID-1,END_TICKS+GRID]{assert!(Producer::from_initial(p,s,end).is_err());}
        let mut bad=p;bad.time=1.;assert!(Producer::from_initial(bad,s,GRID).is_err());
        assert!(Producer::from_initial(p,State::new([0.;118],true),GRID).is_err());
        assert!(Producer::from_initial(p,State::new([f64::NAN;118],false),GRID).is_err());
        for(t,e,k)in[(999*US,1000*US,0.),(1000*US,1125*US,10.),(199999*US,200000*US,10.),(200000*US,200125*US,0.)]{assert_eq!(edge(t,END_TICKS,e),e);assert_eq!(key(t),k);}
    }
    #[test]fn solver_fault_preserves_partial_progress_and_is_terminal(){
        let mut p=Producer::from_initial(parameters(),State::new([0.;118],false),GRID).unwrap();let mut w=Workspace::new();let mut n=0;
        let r=p.run(&mut w,8,&mut[],|_,_,s,_,h|{n+=1;if n==2{*s=State::new([1.;118],false);Err(StepError::NoDecrease)}else{Ok(fake(h,*s))}});
        assert_eq!(r,Report{written:0,invocations:2,published_steps:1,stop:Stop::Fault(StepError::NoDecrease)});
        assert_eq!(p.solved_ticks(),MAXIMUM);assert_eq!(p.output.through_ticks(),MAXIMUM);assert_eq!(p.state,State::new([0.;118],false));assert!(p.pending.is_none());assert_eq!(p.calls,2);assert_eq!(p.steps,1);
        let r=p.run(&mut w,8,&mut[],|_,_,_,_,_|panic!("fault must be terminal"));assert_eq!(r.invocations,0);assert_eq!(r.published_steps,0);assert_eq!(r.stop,Stop::Fault(StepError::NoDecrease));
    }
    #[test]fn quota_zero_and_complete_are_idempotent_without_future_padding(){
        let mut p=Producer::from_initial(parameters(),State::new([0.;118],false),GRID).unwrap();let mut w=Workspace::new();
        let r=p.run(&mut w,0,&mut[],|_,_,_,_,_|panic!("zero quota"));assert_eq!(r.stop,Stop::WorkQuota);assert_eq!(p.solved,0);
        let r=p.run(&mut w,1,&mut[],|_,_,s,_,h|Ok(fake(h,*s)));assert_eq!(r.invocations,1);assert_eq!(r.published_steps,1);assert_eq!(r.stop,Stop::WorkQuota);
        let r=p.run(&mut w,1000,&mut[],|_,_,s,_,h|Ok(fake(h,*s)));assert_eq!(r.stop,Stop::Complete);assert_eq!(p.solved,GRID);assert_eq!(p.output.produced(),0);assert!(p.pending.is_none());
        for quota in[0,1,usize::MAX]{let r=p.run(&mut w,quota,&mut[],|_,_,_,_,_|panic!("completed"));assert_eq!(r,Report{written:0,invocations:0,published_steps:0,stop:Stop::Complete});}
    }
}
