"""Bounded lifecycle adaptation; preserve the admitted sink and collector bytes."""
from prepare_dual_chain import ROOT
from prepare_pitch_program import replace_once

def images():
    s=(ROOT/'crates/rf-d-circuit/src/nominal_render.rs').read_text(encoding='utf8')
    s=s[:s.index('#[cfg(test)]')]
    s=replace_once(s,'//! Offline nominal lifecycle and a separate WAV sink; NOMINAL_RENDER_PROTOCOLO.md.','//! Experimental pitch lifecycle; PITCH_RENDER_PROTOCOLO.md.')
    s=replace_once(s,'nominal_offline_producer.rs','pitch_program_producer.rs')
    s=replace_once(s,'use crate::StepError;','use crate::StepError;\nuse producer::schedule::{Program,Profile};')
    s=replace_once(s,'raw:rf_d_circuit::chain_charge::Parameters,body_ms:u64','raw:rf_d_circuit::chain_charge::Parameters,program:Program,profile:Profile,body_ms:u64')
    s=replace_once(s,'if !(1..=300).contains(&body_ms)','if !(1..=300).contains(&body_ms)||program.end_ticks()!=(body_ms+1)*1000*US')
    s=replace_once(s,'Producer::cold_start(raw,(body_ms+1)*1000*US)?','Producer::cold_start(raw,program,profile)?')
    s=replace_once(s,'        if self.phase!=Phase::Running', '''        self.run(w,quota,out,cancel,voice::advance)
    }
    // Diagnostic seam: accepted readout stays passive and never changes the solve.
    pub(crate) fn run<F>(&mut self,w:&mut Workspace,quota:usize,out:&mut[Frame],cancel:bool,advance:F)->Batch
    where F:FnMut(&mut Workspace,producer::stream::startup::Parameters,&mut producer::stream::startup::State,producer::stream::startup::Controls,f64)->Result<producer::stream::startup::Accepted,StepError>{
        if self.phase!=Phase::Running''')
    s=replace_once(s,'        // Same admitted 1 us reference: cap the requested solve, not its states.\n        let r=self.producer.run(w,quota,out,|w,p,s,c,h|voice::advance(w,p,s,c,h.min(1e-6)));','        let r=self.producer.run(w,quota,out,advance);')
    return {'crates/rf-d-circuit/src/pitch_program_render.rs':s}

def main():
    for n,s in images().items():
        p=ROOT/n
        if p.exists():assert p.read_bytes()==s.encode(),n
        else:p.write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
