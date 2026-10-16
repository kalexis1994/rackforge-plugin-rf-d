"""Derive only parameter/source bindings; keep admitted numerical algorithms intact."""
from prepare_dual_chain import ROOT

def replace_once(s,a,b):
    assert s.count(a)==1,a
    return s.replace(a,b,1)

def images():
    root=ROOT/'crates/rf-d-circuit/src';out={}
    s=(root/'incidence_hybrid_voice.rs').read_text(encoding='utf8')
    s=replace_once(s,'#[path="hybrid_phase_source.rs"] pub mod phase;','#[path="pitch_phase_source.rs"] pub mod phase;')
    s=replace_once(s,'pub use graph::{Parameters,State,Controls,Parts,N,M,B,currents};','''pub use graph::{State,Controls,Parts,N,M,B,currents};
#[derive(Clone,Copy)]
pub struct Parameters{base:graph::Parameters,pub time:f64,pub pitch:phase::Law}
impl Parameters{
    pub fn new(raw:rf_d_circuit::chain_charge::Parameters)->Result<Self,StepError>{Ok(Self{base:graph::Parameters::new(raw)?,time:0.,pitch:phase::Law::nominal()})}
    fn electrical(self)->graph::Parameters{let mut p=self.base;p.time=self.time;p}
}''')
    s=replace_once(s,'graph::parts::<FULL>(p,old,delta,c,h,t)?','graph::parts::<FULL>(p.electrical(),old,delta,c,h,t)?')
    s=replace_once(s,'phase::observe(t,s.now.high[116])','phase::observe(p.pitch,t,s.now.high[116])');out['pitch_program_voice.rs']=s
    s=(root/'nominal_chain_startup.rs').read_text(encoding='utf8');out['pitch_program_startup.rs']=replace_once(s,'active_nominal_voice.rs','pitch_program_voice.rs')
    s=(root/'j7_oversampled_readout.rs').read_text(encoding='utf8');out['pitch_program_readout.rs']=replace_once(s,'nominal_chain_startup.rs','pitch_program_startup.rs')
    s=(root/'j7_stream_output.rs').read_text(encoding='utf8');s=replace_once(s,'j7_oversampled_readout.rs','pitch_program_readout.rs');a=s.index('#[cfg(test)]mod tests{');b=s.index('fn voltage(',a);s=s[:a]+s[b:];out['pitch_program_output.rs']=s
    s=(root/'nominal_offline_producer.rs').read_text(encoding='utf8');s=s[:s.index('#[cfg(test)]')]
    s=replace_once(s,'#[path="j7_stream_output.rs"]pub mod stream;','#[path="pitch_program_output.rs"]pub mod stream;\n#[path="pitch_program_schedule.rs"]pub mod schedule;\nuse schedule::{Program,Profile};')
    s=replace_once(s,'const MAXIMUM:u64=2*US;','')
    s=replace_once(s,'base:Parameters,state:State,solved:u64,end:u64,next_grid:u64,proposal:u64,','base:Parameters,state:State,solved:u64,end:u64,next_grid:u64,proposal:u64,program:Program,maximum:u64,')
    a=s.index('fn key(');b=s.index('fn frame_count(',a);s=s[:a]+s[b:]
    a=s.index('    /// DC setup');b=s.index('    pub fn state(',a)
    s=s[:a]+'''    /// Same own DC, before any program event; initial program is nominal/KEY OFF.
    pub fn cold_start(raw:rf_d_circuit::chain_charge::Parameters,program:Program,profile:Profile)->Result<Self,StepError>{
        let initial=startup::cold_start(raw)?;Self::from_initial(Parameters::new(raw)?,initial.state,program,profile)
    }
    pub fn from_initial(base:Parameters,initial:State,program:Program,profile:Profile)->Result<Self,StepError>{
        if base.time.to_bits()!=0_f64.to_bits()||base.pitch!=voice::phase::Law::nominal(){return Err(StepError::InvalidInput);}
        let maximum=profile.ticks();Ok(Self{base,state:initial,solved:0,end:program.end_ticks(),next_grid:GRID,proposal:maximum,program,maximum,output:Pipeline::new(initial)?,pending:None,calls:0,steps:0,fault:None})
    }
    pub fn program(&self)->Program{self.program}
''' +s[b:]
    s=replace_once(s,'let remain=edge(self.solved,self.end,self.next_grid)-self.solved;','let (segment,event_end)=self.program.at(self.solved);\n            let remain=event_end.min(self.next_grid)-self.solved;')
    s=replace_once(s,'parameters.time=self.solved as f64*TICK;','parameters.time=self.solved as f64*TICK;parameters.pitch=segment.law;')
    s=replace_once(s,'key:key(self.solved)','key:if segment.key_on{10.}else{0.}')
    s=replace_once(s,'(2*actual).min(MAXIMUM)','(2*actual).min(self.maximum)');out['pitch_program_producer.rs']=s
    return {'crates/rf-d-circuit/src/'+k:'//! Derived pitch variant; PITCH_PROGRAM_PROTOCOLO.md.\n'+v for k,v in out.items()}

def main():
    for n,s in images().items():
        p=ROOT/n
        if p.exists():assert p.read_bytes()==s.encode(),n
        else:p.write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
