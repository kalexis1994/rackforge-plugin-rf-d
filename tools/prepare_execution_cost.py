"""Generate laboratory timing copies; original engines remain byte protected."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
def entry(s,signature,k):return once(s,signature,signature+f'\n    let _clock=crate::execution_clock::enter({k});')
def phase(s,statement,k):return once(s,statement,f'let phase_clock=crate::execution_clock::enter({k});'+statement+'drop(phase_clock);')
def derive():
    out={};prefix='crates/rf-d-circuit/src/'
    clock='''//! Laboratory-only inclusive wall timers; errors also close their scopes.
use std::{time::Instant,sync::atomic::{AtomicU64,Ordering}};
const N:usize=19;
static NS:[AtomicU64;N]=[const{AtomicU64::new(0)};N];
static COUNT:[AtomicU64;N]=[const{AtomicU64::new(0)};N];
pub struct Scope{index:usize,start:Instant}
pub fn enter(index:usize)->Scope{COUNT[index].fetch_add(1,Ordering::Relaxed);Scope{index,start:Instant::now()}}
impl Drop for Scope{fn drop(&mut self){NS[self.index].fetch_add(self.start.elapsed().as_nanos()as u64,Ordering::Relaxed);}}
pub fn read()->[(u64,u64);N]{std::array::from_fn(|k|(NS[k].load(Ordering::Relaxed),COUNT[k].load(Ordering::Relaxed)))}
'''
    out['tools/execution_clock.rs']=clock
    a=(ROOT/(prefix+'affine_newton_voice.rs')).read_text(encoding='utf8')
    a=once(a,'#[path="affine_newton_frame.rs"]','#[path="profile_execution_frame.rs"]')
    a=entry(a,'pub fn evaluate<const FULL:bool>(p:Parameters,old:State,d:Reduced,c:Controls,h:f64,t:f64)->Result<Stage,StepError>{','if FULL{0}else{1}')
    for stmt,k in [('let local=p.model.solve(y,seed,ladder::Budget::default())?;',2),('let mut physical=binding::parent_parts::<FULL>(p.parent,p.time,old,delta,c,h,t)?;',3),('binding::validate_parent::<FULL>(&physical)?;',4),('binding::merge::<FULL>(&mut physical,&local)?;',5)]:a=phase(a,stmt,k)
    a=entry(a,"pub fn prepare<'w,'s>(&'w mut self,s:&'s[Stage;2])->Result<affine::Frame<'w,'s>,StepError>{",6)
    a=phase(a,'self.physical.initialize(s,B)?;',7)
    a=phase(a,'let local=[affine::Local::new(&s[0].physical.j,&s[0].physical.mass)?,affine::Local::new(&s[1].physical.j,&s[1].physical.mass)?];',8)
    a=phase(a,'for i in 0..2{local[i].coefficients(&s[i].physical.j,&s[i].physical.mass,&mut self.dc[i],&mut self.mass[i])?;}',9)
    a=phase(a,'let reduced=self.reduced.prepare([solver::Stage{dc:&self.dc[0],mass:&self.mass[0]},solver::Stage{dc:&self.dc[1],mass:&self.mass[1]}],B)?;',10)
    a=entry(a,'pub fn advance(w:&mut Workspace,p:Parameters,state:&mut State,c:Controls,mut h:f64)->Result<Accepted,StepError>{',18)
    out[prefix+'profile_execution_affine.rs']=a
    f=(ROOT/(prefix+'affine_newton_frame.rs')).read_text(encoding='utf8')
    f=entry(f,'pub fn solve(&mut self,b:[f64;M])->Result<([f64;RM],[f64;M]),StepError>{',11)
    f=phase(f,'let dy=self.reduced.solve(rhs)?;',12)
    f=entry(f,'pub fn residual(&self,b:&[f64;M],d:&[f64;M])->Result<([f64;M],f64),StepError>{',13)
    out[prefix+'profile_execution_frame.rs']=f
    d=(ROOT/(prefix+'direct_hybrid_voice.rs')).read_text(encoding='utf8')
    d=once(d,'#[path="direct_hybrid_solver.rs"]','#[path="profile_execution_direct_solver.rs"]')
    d=entry(d,'pub fn parts<const FULL:bool>(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{','if FULL{0}else{1}')
    d=entry(d,'pub fn advance(w:&mut Workspace,p: Parameters, state: &mut State, c: Controls, mut h: f64) -> Result<Accepted, StepError> {',18)
    out[prefix+'profile_execution_direct.rs']=d
    s=(ROOT/(prefix+'direct_hybrid_solver.rs')).read_text(encoding='utf8')
    s=entry(s,'fn initialize(&mut self,stages:[Stage;2],weights:[[f64;2];2])->Result<(),StepError>{',6)
    s=entry(s,'pub fn solve(&mut self,stages:[Stage;2],weights:[[f64;2];2],b:[f64;M])->Result<[f64;M],StepError>{',11)
    s=entry(s,'fn correction(&self,b:[f64;M])->Result<[f64;M],StepError>{',12)
    s=entry(s,'fn residual(&self,b:&[f64;M],d:&[f64;M])->Result<([f64;M],f64),StepError>{',13)
    s=once(s,'self.contour.factor(&mut self.outer.a)?;self.audio.factor(&mut self.outer.a)?;self.outer.factor()', 'let _factor_clock=crate::execution_clock::enter(10);self.contour.factor(&mut self.outer.a)?;self.audio.factor(&mut self.outer.a)?;self.outer.factor()')
    out[prefix+'profile_execution_direct_solver.rs']=s
    p=(ROOT/'tools/affine_newton_probe.rs').read_text(encoding='utf8')
    p='#[path="execution_clock.rs"]mod execution_clock;\n'+p
    p=once(p,'src/affine_newton_voice.rs','src/profile_execution_affine.rs');p=once(p,'src/direct_hybrid_voice.rs','src/profile_execution_direct.rs')
    p=once(p,'    assert_eq!(heap,0);','    {write!(w,"EXECUTION").unwrap();for(ns,count)in execution_clock::read(){write!(w,",{ns},{count}").unwrap();}writeln!(w).unwrap();}\n    assert_eq!(heap,0);')
    out['tools/execution_cost_probe.rs']=p
    return out
def main():
    path=ROOT/'evidence/execution_cost_before01.json';assert not path.exists()
    previous='evidence/affine_newton_tests01.json';names=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write(path,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    for n,s in derive().items():assert not(ROOT/n).exists();(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
