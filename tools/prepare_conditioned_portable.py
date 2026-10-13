"""Export the admitted 229-state voice and explicit reusable workspace into Rust."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_schur_contour import replace_once
from joint_cycles_analysis import require
NAMES=['crates/rf-d-circuit/src/conditioned_voice.rs','crates/rf-d-circuit/src/conditioned_voice_solver.rs','crates/rf-d-circuit/src/conditioned_voice_latch.rs','crates/rf-d-circuit/src/conditioned_voice_contour.rs','crates/rf-d-circuit/src/conditioned_engine.rs','tools/conditioned_portable_runner.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in NAMES)).encode()
EXPORT=b'\npub mod conditioned_voice;\npub mod conditioned_engine;\n'

def voice():
    s=(ROOT/'tools/joint_radau_inplace_kernel.rs').read_text(encoding='utf8').replace('rf_d_circuit::','crate::').replace('dynamic_schur_chain_solver.rs','conditioned_voice_solver.rs').replace('latch_charge_driver.rs','conditioned_voice_latch.rs').replace('contour_closed_driver.rs','conditioned_voice_contour.rs')
    s=replace_once(s,'/// Pure candidate solve. The caller publishes both block histories together.\npub fn step(p:Parameters,old:State,h:f64)->Result<Pair,StepError> {','''/// Owns two fully initialized assembly buffers; reuse only through &mut.
/// Constructor storage belongs to the caller; no deadline/stack admission.
pub struct Workspace{first:Stamp,second:Stamp}
impl Default for Workspace{fn default()->Self{Self::new()}}
impl Workspace{
 pub const fn new()->Self{Self{first:Stamp::blank(),second:Stamp::blank()}}
 pub const fn storage_bytes()->usize{std::mem::size_of::<Self>()}
 /// Pure candidate solve; publishes no state, including after a rejection.
 pub fn step(&mut self,p:Parameters,old:State,h:f64)->Result<Pair,StepError>{''')
    s=replace_once(s,' let mut first=Stamp::blank();let mut second=Stamp::blank();let(mut s,mut t)=(&mut first,&mut second);',' let(mut s,mut t)=(&mut self.first,&mut self.second);')
    anchor='\nmod fine {';require(s.count(anchor)==1,'step ending');s=s.replace(anchor,'''\n}
/// One-shot compatibility facade. Reusable callers should own a Workspace.
pub fn step(p:Parameters,old:State,h:f64)->Result<Pair,StepError>{Workspace::new().step(p,old,h)}

mod fine {''',1)
    return s

def solver():return (ROOT/'tools/dynamic_schur_chain_solver.rs').read_text(encoding='utf8')
def latch():return (ROOT/'tools/latch_charge_driver.rs').read_text(encoding='utf8').replace('rf_d_circuit::','crate::')
def contour():return (ROOT/'tools/contour_closed_driver.rs').read_text(encoding='utf8').replace('rf_d_circuit::','crate::')

def engine():
    s=(ROOT/'tools/contour_reset_engine.rs').read_text(encoding='utf8').replace('use super::joint::{self,State,N};','use crate::conditioned_voice::{self as joint,State,N,Workspace};').replace('rf_d_circuit::','crate::')
    s=replace_once(s,'pub fn advance_to(&mut self,target_ticks:u64)->Result<Accepted,Error> {','pub fn advance_to(&mut self,workspace:&mut Workspace,target_ticks:u64)->Result<Accepted,Error> {')
    require(s.count('joint::step(')==3,'three temporal calls');return s.replace('joint::step(','workspace.step(')

def caller():
    s=(ROOT/'tools/joint_radau_inplace_runner.rs').read_text(encoding='utf8')
    s=replace_once(s,'#[path="joint_radau_inplace_kernel.rs"] mod joint;','use rf_d_circuit::conditioned_voice as joint;')
    s=replace_once(s,'#[path="contour_reset_engine.rs"] mod temporal;','use rf_d_circuit::conditioned_engine as temporal;')
    s=replace_once(s,' let args:Vec<_>=std::env::args().collect();let dir=',' let mut workspace=joint::Workspace::new();let args:Vec<_>=std::env::args().collect();let dir=')
    require(s.count('.advance_to(')==4,'bounded caller advance sites');return s.replace('.advance_to(','.advance_to(&mut workspace,')

def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='a69a1e983f3f24d66c548fc007db3fdd922824da','base')
    previous='evidence/voice_radau_inplace_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));require(old['passed'] and old['radau_inplace_admitted'],'admitted laboratory')
    mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','crates/rf-d-circuit/src/lib.rs']
    write('evidence/voice_conditioned_portable_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    for n,f in zip(NAMES,[voice,solver,latch,contour,engine,caller]):
        p=ROOT/n;require(not p.exists(),'exclusive portable source');p.write_text(f(),encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);p=ROOT/'crates/rf-d-circuit/src/lib.rs';p.write_bytes(p.read_bytes()+EXPORT)
    private={n:sha(ROOT/n) for n in ['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib','references-local/schur-refined-radauinplacebank01/linear.bin']}
    for n,h in private.items():require(h==old['private_input_sha256'][n],'frozen private '+n)
    write('evidence/voice_conditioned_portable_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in NAMES+['tools/prepare_conditioned_portable.py','crates/rf-d-circuit/src/lib.rs','docs/CONJUNTO_PORTABLE_PROTOCOLO.md']},private_used_sha256=private,seeds=json.loads((ROOT/'evidence/voice_radau_inplace_inputs01.json').read_text(encoding='utf8'))['seeds']))
    print('CONDITIONED_PORTABLE_INPUTS',229,458)
if __name__=='__main__':main()
