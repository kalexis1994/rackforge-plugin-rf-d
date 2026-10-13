"""Observe the reduced voice and solver on a private copy with exact root checks."""
from prepare_vco1_portable import ROOT
from prepare_schur_contour import replace_once
from joint_cycles_analysis import require
from schur_refined_native import experiment
LABELS=['step','linearize','parts','solve','prepare','support','factor64','factor58','factor132','factor140','rhs64','rhs58','rhs132','rhs140','correction','residual']
COUNTERS='''pub mod observer{
use std::sync::atomic::{AtomicU64,Ordering};
static TIMES:[AtomicU64;16]=[const{AtomicU64::new(0)};16];
static CALLS:[AtomicU64;16]=[const{AtomicU64::new(0)};16];
static REJECTIONS:[AtomicU64;2]=[const{AtomicU64::new(0)};2];
pub fn reject(stage:usize){REJECTIONS[stage].fetch_add(1,Ordering::Relaxed);}
pub struct Timer{index:usize,start:std::time::Instant}
impl Timer{pub fn new(index:usize)->Self{Self{index,start:std::time::Instant::now()}}}
impl Drop for Timer{fn drop(&mut self){TIMES[self.index].fetch_add(self.start.elapsed().as_nanos() as u64,Ordering::Relaxed);CALLS[self.index].fetch_add(1,Ordering::Relaxed);}}
pub fn summary(){for i in 0..16{println!("PROFILE,{i},{},{}",TIMES[i].load(Ordering::Relaxed),CALLS[i].load(Ordering::Relaxed));}println!("STAGE_REJECTIONS,{},{}",REJECTIONS[0].load(Ordering::Relaxed),REJECTIONS[1].load(Ordering::Relaxed));}
}
'''

def instrument():
    s=(ROOT/'tools/dynamic_schur_chain_solver.rs').read_text(encoding='utf8')
    anchors=[(' fn factor_in_place(&mut self)->Result<(),StepError>{','if N==64{6}else if N==58{7}else if N==132{8}else{9}'),(' fn solve(&self,b:[f64;N])->Result<[f64;N],StepError>{','if N==64{10}else if N==58{11}else if N==132{12}else{13}'),(' fn initialize(&mut self,j:&[[f64;458];458])->Result<(),StepError>{','4'),(' fn correction(&self,j:&[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{','14'),('fn residual(s:&Sparse,b:&[f64;458],d:&[f64;458])->Result<([f64;458],f64),StepError>{','15'),('pub fn solve_observed(j:[[f64;458];458],b:[f64;458])->Result<Observation,StepError>{','3')]
    # Two initialize functions share a signature; identify their impl scopes.
    for anchor,index in anchors:
        if index=='4':
            a=s.index('impl Prepared{');b=s.index('fn tau(',a);s=s[:a]+replace_once(s[a:b],anchor,anchor+'let _timer=super::observer::Timer::new(4);')+s[b:]
        else:s=replace_once(s,anchor,anchor+'let _timer=super::observer::Timer::new('+index+');')
    a=s.index('impl Sparse{');s=s[:a]+replace_once(s[a:],' fn initialize(&mut self,j:&[[f64;458];458])->Result<(),StepError>{',' fn initialize(&mut self,j:&[[f64;458];458])->Result<(),StepError>{let _timer=super::observer::Timer::new(5);')
    s='\n'.join(x for x in s.splitlines() if not x.startswith('//!'))
    k=(ROOT/'tools/joint_schur_chain_kernel.rs').read_text(encoding='utf8')
    k=replace_once(k,'#[path="dynamic_schur_chain_solver.rs"] pub mod dynamic_schur;','pub mod dynamic_schur{'+s+'}')
    for name,index in [('parts','2'),('linearize','1'),('step','0')]:
        a=k.index('pub fn '+name+'(');b=k.index('{',a);k=k[:b+1]+'let _timer=observer::Timer::new('+index+');'+k[b+1:]
    k=replace_once(k,' let q=[parts(p,old,delta[0],h)?,parts(p,old,delta[1],h)?];',' let first=parts(p,old,delta[0],h);if first.is_err(){observer::reject(0);}let first=first?;let second=parts(p,old,delta[1],h);if second.is_err(){observer::reject(1);}let q=[first,second?];')
    for n in ['latch_charge_driver.rs','contour_closed_driver.rs']:k=k.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    return COUNTERS+'\n'.join(x for x in k.splitlines() if not x.startswith('//!'))

def validate(work,q):
    lines=q['stdout'].splitlines();rows=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('PROFILE,')]
    require(len(rows)==16 and [r[0] for r in rows]==list(range(16)) and lines[-1]=='PROFILED_PASSED,84,1834','profile scope')
    t=[r[1] for r in rows];c=[r[2] for r in rows]
    rejected=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('STAGE_REJECTIONS,')];require(len(rejected)==1 and rejected[0]==[64,0],'first/second stage rejection accounting');first,second=rejected[0]
    require(c[0]==84 and c[2]==2*c[1]-first and c[1]==c[3]+first+second and c[3:]==[396,396,396,792,396,396,396,8752,1208,2000,416,416,416],'exact profile calls')
    require(t[2]<=t[1] and t[1]+t[3]<=t[0] and t[5]+sum(t[6:10])<=t[4] and t[4]+t[14]+t[15]<=t[3],'nested phase accounting')
    return dict(selected_pairs=84,exact_bit_fields_per_pair=1834,iterations_and_trials_identical=True,first_stage_rejections=first,second_stage_rejections=second,phases=[dict(name=n,time_ns=a,calls=b) for n,a,b in zip(LABELS,t,c)],linearize_fraction_of_step=t[1]/t[0],solve_fraction_of_step=t[3]/t[0],prepare_fraction_of_solve=t[4]/t[3],timing_is_nested=True,benchmark_utility_claim=False,full_trajectory_admitted=False)

def main():
    text=(ROOT/'tools/schur_chain_bench.rs').read_text(encoding='utf8').split('fn main(){')[0]
    text=replace_once(text,'#[path="joint_schur_chain_kernel.rs"] mod reuse;','mod reuse{'+instrument()+'}')
    for n in ['joint_lu_extent_kernel.rs','joint_schur_contour_kernel.rs']:text=text.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=text.replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())
    text+='\n#[path="'+(ROOT/'tools/joint_schur_chain_kernel.rs').as_posix()+'"] mod plain;execute!(run_plain,plain);\nfn main(){let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),84);for c in &cs{let a=run_plain(c);let b=run_reuse(c);assert_eq!(a,b);}reuse::observer::summary();println!("PROFILED_PASSED,84,1834");}\n'
    experiment('chainprofile02',text,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin'],['tools/profile_schur_chain_cost.py','tools/dynamic_schur_chain_solver.rs','tools/joint_schur_chain_kernel.rs','tools/schur_chain_bench.rs','tools/prepare_schur_contour.py','docs/SCHUR_CADENA_PERFIL_PROTOCOLO.md','docs/SCHUR_CADENA_PERFIL_REPARACION.md','evidence/voice_schur_chain_profile_replay01.json'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate)
if __name__=='__main__':main()
