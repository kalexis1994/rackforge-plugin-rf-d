"""Collect existing paired evidence and derive timing/zero-pivot kernels."""
import base64,json,re,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from prepare_release_voice import once
SOLVER='crates/rf-d-circuit/src/conditioned_voice_solver.rs'
VOICE='crates/rf-d-circuit/src/decay_voice.rs'
LABELS=['step','initialize','parts','joint_parts','unused','prepare','factor64','factor58','factor132','factor140','rhs64','rhs58','rhs132','rhs140','support','residual','correction','solve']
RUST=['tools/voice_pivot_profile_kernel.rs','tools/voice_pivot_profile_solver.rs','tools/voice_pivot_copy_kernel.rs','tools/voice_pivot_solver.rs','tools/voice_pivot_kernel.rs','tools/voice_pivot_bench.rs','tools/voice_pivot_paired.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RUST)).encode()

def solver():
 s=(ROOT/SOLVER).read_text(encoding='utf8')
 return once(s,'for row in col..N{let score=','for row in col..N{if a[row][col]==0.{continue;}let score=')

def kernel(path):
 s=(ROOT/VOICE).read_text(encoding='utf8')
 s=once(s,'#[path="conditioned_voice_solver.rs"]',f'#[path="{path}"]')
 for old in ['conditioned_voice_latch.rs','decay_contour.rs','joint_vco_fine.rs']:
  s=s.replace(f'#[path="{old}"]',f'#[path="../crates/rf-d-circuit/src/{old}"]')
 return s

def profile_sources():
 s=(ROOT/SOLVER).read_text(encoding='utf8')
 s=once(s,'use super::StepError;','use super::{StepError,record};')
 s=once(s,'fn factor_in_place(&mut self)','fn factor_in_place_impl(&mut self)')
 s=once(s,'fn solve(&self,b:[f64;N])','fn solve_impl(&self,b:[f64;N])')
 s=once(s,'impl Prepared{','impl Prepared{')
 # Names only: the arithmetic remains in the original implementations.
 require(s.count('fn initialize(&mut self,j:&[[f64;458];458])')==2,'two initialize methods');s=s.replace('fn initialize(&mut self,j:&[[f64;458];458])','fn initialize_impl(&mut self,j:&[[f64;458];458])',1)
 # Sparse has the same signature; after renaming the first match, rename it.
 s=s.replace('fn initialize(&mut self,j:&[[f64;458];458])','fn initialize_impl(&mut self,j:&[[f64;458];458])')
 s=once(s,'fn correction(&self,j:','fn correction_impl(&self,j:')
 s=once(s,'fn residual(s:','fn residual_impl(s:')
 s=once(s,'pub fn solve_observed(j:','pub fn solve_observed_impl(j:')
 s+='''
impl<const N:usize> Lu<N>{
 fn factor_in_place(&mut self)->Result<(),StepError>{let t=std::time::Instant::now();let r=self.factor_in_place_impl();record(match N{64=>6,58=>7,132=>8,140=>9,_=>panic!("LU size")},t);r}
 fn solve(&self,b:[f64;N])->Result<[f64;N],StepError>{let t=std::time::Instant::now();let r=self.solve_impl(b);record(match N{64=>10,58=>11,132=>12,140=>13,_=>panic!("LU size")},t);r}
}
impl Prepared{
 fn initialize(&mut self,j:&[[f64;458];458])->Result<(),StepError>{let t=std::time::Instant::now();let r=self.initialize_impl(j);record(5,t);r}
 fn correction(&self,j:&[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{let t=std::time::Instant::now();let r=self.correction_impl(j,b);record(16,t);r}
}
impl Sparse{fn initialize(&mut self,j:&[[f64;458];458])->Result<(),StepError>{let t=std::time::Instant::now();let r=self.initialize_impl(j);record(14,t);r}}
fn residual(s:&Sparse,b:&[f64;458],d:&[f64;458])->Result<([f64;458],f64),StepError>{let t=std::time::Instant::now();let r=residual_impl(s,b,d);record(15,t);r}
pub fn solve_observed(j:[[f64;458];458],b:[f64;458])->Result<Observation,StepError>{let t=std::time::Instant::now();let r=solve_observed_impl(j,b);record(17,t);r}
'''
 v=kernel('voice_pivot_profile_solver.rs');v=once(v,'pub fn parts(','pub fn parts_impl(');v=once(v,'pub fn initialize(','pub fn initialize_impl(');v=once(v,'pub fn step(&mut self','pub fn step_impl(&mut self')
 v=once(v,' let base=crate::joint_voice::parts',' let base_t=std::time::Instant::now();let base=crate::joint_voice::parts');v=once(v,' let mut s=Parts{',' record(3,base_t);let mut s=Parts{')
 v+='''
use std::sync::atomic::{AtomicU64,Ordering};
static TIMES:[AtomicU64;18]=[const{AtomicU64::new(0)};18];static CALLS:[AtomicU64;18]=[const{AtomicU64::new(0)};18];
pub fn record(id:usize,t:std::time::Instant){TIMES[id].fetch_add(t.elapsed().as_nanos() as u64,Ordering::Relaxed);CALLS[id].fetch_add(1,Ordering::Relaxed);}
pub fn profile(){for k in 0..18{println!("PROFILE,{k},{},{}",TIMES[k].load(Ordering::Relaxed),CALLS[k].load(Ordering::Relaxed));}}
pub fn parts(p:Parameters,o:State,d:State,h:f64)->Result<Parts,StepError>{let t=std::time::Instant::now();let r=parts_impl(p,o,d,h);record(2,t);r}
impl Stamp{pub fn initialize(&mut self,p:Parameters,o:State,d:[State;2],h:f64)->Result<(),StepError>{let t=std::time::Instant::now();let r=self.initialize_impl(p,o,d,h);record(1,t);r}}
impl Workspace{pub fn step(&mut self,p:Parameters,o:State,h:f64)->Result<Pair,StepError>{let t=std::time::Instant::now();let r=self.step_impl(p,o,h);record(0,t);r}}
'''
 return {RUST[0]:v,RUST[1]:s,RUST[2]:kernel('../crates/rf-d-circuit/src/conditioned_voice_solver.rs'),RUST[3]:solver(),RUST[4]:kernel('voice_pivot_solver.rs')}

def bank():
 records=[];inputs=[];observed=[]
 def add(ohm,h,old,states,ratio,counts):records.append(struct.pack('<2d458d1834d2Q',ohm,h,*old,*[x for s in states for x in s],*ratio,*counts))
 for maximum in [1048576,524288]:
  name=f'references-local/decay-voice02/{maximum}/selected.txt';inputs.append(name);lines=(ROOT/name).read_text(encoding='utf8').splitlines()
  for i,line in enumerate(lines):
   if line.startswith('JOINT_ROOT,'):
    _,mask,h,res,corr=line.split(',');states=[list(map(float,l.split(',')[1:])) for l in lines[i+1:i+6]];require(all(len(s)==458 for s in states),'root state widths');add(1000.,float(h),states[0],states[1:],list(map(float,[res,corr])),[2**64-1]*2)
  name=f'references-local/decay-voice02/{maximum}/nominal-old.bin';seed=f'references-local/decay-voice02/{maximum}/incoming-nominal.ckp';inputs.extend([name,seed]);raw=(ROOT/name).read_bytes();require(len(raw)==4*47934,'four logical accepted records');old=list(struct.unpack('<458d',(ROOT/seed).read_bytes()[64:]));
  for k in range(4):
   b=raw[k*47934:(k+1)*47934];half=struct.unpack_from('<I',b,44224)[0];h=half*125e-9/65536;mid=None
   for j,dt in enumerate([2*h,h,h]):
    p=struct.unpack_from('<1834d2Q',b,j*14688);states=[list(p[a*458:(a+1)*458]) for a in range(4)];add(100000.,dt,old if j<2 else mid,[states[2],states[3],states[0],states[1]],list(p[1832:1834]),list(p[1834:]));
    if j==1:mid=states[1]
   old=list(struct.unpack_from('<458d',b,44240))
 require(len(records)==78 and all(len(r)==18368 for r in records),'declared finite bank');return b'RFPIVT01'+struct.pack('<I',len(records))+b''.join(records),inputs

def main():
 previous='evidence/voice_decay_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='0a02e779c9afaa373f9f8c5bd6ac7037a27b56fb','base');require(not (ROOT/'evidence/voice_pivot_before01.json').exists(),'exclusive preparation')
 write('evidence/voice_pivot_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','crates/rf-d-circuit/src/lib.rs']}))
 for n,s in profile_sources().items():require(not (ROOT/n).exists(),'exclusive source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);data,inputs=bank();work=ROOT/'references-local/voice-pivot-inputs01';work.mkdir();(work/'pairs.bin').write_bytes(data)
 for n in inputs:require(sha(ROOT/n)==old['private_input_sha256'][n],'admitted bank input')
 write('evidence/voice_pivot_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_voice_pivot.py','docs/VOZ_COSTO_PIVOTE_PROTOCOLO.md',SOLVER,VOICE,*profile_sources()]},private_used_sha256={n:sha(ROOT/n) for n in inputs},outputs=[dict(path='references-local/voice-pivot-inputs01/pairs.bin',sha256=sha(work/'pairs.bin'),bytes=len(data))],pairs=78,expected_f64_per_pair=1834,nominal_counters_known_pairs=24,selected_counters_unknown_pairs=54))
 print('PIVOT_INPUTS',78,len(data))
if __name__=='__main__':main()
