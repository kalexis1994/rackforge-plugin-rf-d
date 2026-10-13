"""Prepare a longer ON trajectory, unchanged circuit/public library and own seeds."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
START=4423942144;BOUNDARIES=[0,2097152,4196401152,6293553152];CUT=157286400
KEY=[0.,10.,0.];SHORT=[False,True,False];MAXIMUM=[1048576,524288]
EXAMPLE='crates/rf-d-circuit/examples/sustained_voice.rs'
ATTR=('\n/tools/sustained_voice_body.rs text eol=lf\n/'+EXAMPLE+' text eol=lf\n').encode()

def cuts(phase):
    end=START+BOUNDARIES[phase+1]
    if phase==0:return [end]
    return list(range(START+BOUNDARIES[phase]+CUT,end,CUT))+[end]

def caller():
    old=(ROOT/'tools/conditioned_portable_runner.rs').read_text(encoding='utf8')
    prefix=old[old.index('fn write_state('):old.index('fn run()->Result<(),String>{')]
    prefix=prefix.replace('const REL:[u64;4]=[0,2097152,788529152,1574961152]','const REL:[u64;4]=[0,2097152,4196401152,6293553152]').replace('RFCYCT01','RFHLD001')
    return '''//! ON diagnostic: 4 us rest, 8 ms gate, 4 ms release; own public histories.
//! No audio-thread admission. See docs/VOZ_SOSTENIDA_PROTOCOLO.md.
use rf_d_circuit::{conditioned_voice as joint,conditioned_engine as temporal};
use std::{fs,io::Write,time::Instant};
fn scene()->joint::Parameters{
 rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution:rf_d_circuit::conditioned_recipe::Resolution::Half2Us}.parameters()
}
'''+prefix+(ROOT/'tools/sustained_voice_body.rs').read_text(encoding='utf8')

def main():
    previous='evidence/voice_conditioned_recipe_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    require(head=='8e839b8429d8c779c4cc517ad4a40ecda0511cd1' and old['passed'],'base')
    write('evidence/voice_sustained_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    p=ROOT/EXAMPLE;require(not p.exists(),'exclusive example');p.write_text(caller(),encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
    lib='references-local/conditioned-recipe-library02/librf_d_circuit.rlib';require(sha(ROOT/lib)==old['private_input_sha256'][lib],'frozen public library')
    write('evidence/voice_sustained_inputs01.json',dict(passed=True,start_ticks=START,boundaries_relative_ticks=BOUNDARIES,keyboard_v=KEY,short=SHORT,maximum_half_ticks=MAXIMUM,grid_targets=[cuts(p) for p in range(3)],final_decay=True,own_history_source='conditioned_recipe::Recipe::engine',source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_sustained_voice.py','tools/sustained_voice_body.rs',EXAMPLE,'docs/VOZ_SOSTENIDA_PROTOCOLO.md']},private_used_sha256={lib:sha(ROOT/lib)},new_library_compile=False))
    print('SUSTAINED_INPUTS',len(cuts(0))+len(cuts(1))+len(cuts(2)),.012004)
if __name__=='__main__':main()
