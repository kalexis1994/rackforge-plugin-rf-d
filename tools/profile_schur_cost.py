"""Nested timing on a private copy; verify exact results against untouched source."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from schur_refined_native import experiment
COUNTERS='''use std::sync::atomic::{AtomicU64,Ordering};
static TIMES:[AtomicU64;9]=[const{AtomicU64::new(0)};9];
static CALLS:[AtomicU64;9]=[const{AtomicU64::new(0)};9];
fn record(k:usize,t:std::time::Instant){TIMES[k].fetch_add(t.elapsed().as_nanos() as u64,Ordering::Relaxed);CALLS[k].fetch_add(1,Ordering::Relaxed);}
pub fn summary(){for i in 0..9{println!("PROFILE,{i},{},{}",TIMES[i].load(Ordering::Relaxed),CALLS[i].load(Ordering::Relaxed));}}
'''
def instrument(s):
    s='\n'.join(x for x in s.splitlines() if not x.startswith('//!'));s=COUNTERS+s
    s=s.replace(' fn factor(mut a:[[f64;N];N])->Result<Self,StepError>{',' fn factor(mut a:[[f64;N];N])->Result<Self,StepError>{let timing=std::time::Instant::now();',1).replace('Ok(Self{a,perm})','record(if N==64{1}else{2},timing);Ok(Self{a,perm})',1)
    s=s.replace(' fn solve(&self,b:[f64;N])->Result<[f64;N],StepError>{',' fn solve(&self,b:[f64;N])->Result<[f64;N],StepError>{let timing=std::time::Instant::now();',1).replace('Ok(x)','record(if N==64{4}else{5},timing);Ok(x)',1)
    s=s.replace(' fn new(j:&[[f64;458];458])->Result<Self,StepError>{',' fn new(j:&[[f64;458];458])->Result<Self,StepError>{let timing=std::time::Instant::now();',1).replace('  Ok(Self{inner,outer:Lu::factor(s)?,response,position,sparse})','  let outer=Lu::factor(s)?;record(0,timing);Ok(Self{inner,outer,response,position,sparse})',1)
    s=s.replace(' fn correction(&self,j:&[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{',' fn correction(&self,j:&[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{let timing=std::time::Instant::now();',1).replace('Ok(d)','record(6,timing);Ok(d)',1)
    # The second constructor belongs to the exact sparse support.
    a=s.index('impl Sparse{');s=s[:a]+s[a:].replace(' fn new(j:&[[f64;458];458])->Result<Self,StepError>{',' fn new(j:&[[f64;458];458])->Result<Self,StepError>{let timing=std::time::Instant::now();',1).replace('Ok(out)','record(3,timing);Ok(out)',1)
    s=s.replace(' let mut r=[0.;458];let mut worst=0_f64;',' let timing=std::time::Instant::now();let mut r=[0.;458];let mut worst=0_f64;',1).replace(' Ok((r,worst))',' record(7,timing);Ok((r,worst))',1)
    s=s.replace(' if b.iter().any',' let timing=std::time::Instant::now();if b.iter().any',1).replace('if metric<=BACKWARD_GATE{return Ok(Observation','if metric<=BACKWARD_GATE{record(8,timing);return Ok(Observation',1);return s
def validate(work,q):
    lines=q['stdout'].splitlines();rows=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('PROFILE,')];require(len(rows)==9 and [x[0] for x in rows]==list(range(9)) and lines[-1]=='PROFILED_PASSED,84,1834','profile scope');times=[r[1] for r in rows];calls=[r[2] for r in rows];require(calls==[396,792,396,396,8752,416,416,416,396],'same factor/refinement calls');require(times[1]+times[2]+times[3]<=times[0] and times[0]+times[6]+times[7]<=times[8],'nested timing accounting')
    labels=['prepare','factor64','factor330','support','rhs64','rhs330','correction','residual','solve'];return dict(selected_pairs=84,exact_bit_fields_per_pair=1834,phases=[dict(name=n,time_ns=t,calls=c) for n,t,c in zip(labels,times,calls)],prepare_fraction_of_solve=times[0]/times[8],correction_fraction_of_solve=times[6]/times[8],residual_fraction_of_solve=times[7]/times[8],timing_is_nested=True,benchmark_utility_claim=False,full_trajectory_admitted=False)
def main():
    previous='evidence/voice_schur_refined_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='1e02f98a83b3dbc70ca408074f1e668d8ff1fb59' and old['passed'],'base');write('evidence/voice_schur_cost_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    solver=instrument((ROOT/'tools/dynamic_schur_refined_sparse_solver.rs').read_text(encoding='utf8'));kernel=(ROOT/'tools/joint_schur_refined_sparse_kernel.rs').read_text(encoding='utf8');kernel='\n'.join(x for x in kernel.splitlines() if not x.startswith('//!'));kernel=kernel.replace('#[path="dynamic_schur_refined_sparse_solver.rs"] pub mod dynamic_schur;','pub mod dynamic_schur{'+solver+'}')
    for n in ['latch_charge_driver.rs','contour_closed_driver.rs']:kernel=kernel.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=(ROOT/'tools/schur_refined_sparse_bench.rs').read_text(encoding='utf8').split('fn main(){')[0];text=text.replace('#[path="joint_schur_refined_sparse_kernel.rs"] mod reuse;','mod reuse{'+kernel+'}').replace('path="joint_lu_extent_kernel.rs"','path="'+(ROOT/'tools/joint_lu_extent_kernel.rs').as_posix()+'"').replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix());text+='\n#[path="'+(ROOT/'tools/joint_schur_refined_sparse_kernel.rs').as_posix()+'"] mod plain;execute!(run_plain,plain);\nfn main(){let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),84);for c in &cs{let a=run_plain(c);let b=run_reuse(c);assert_eq!(a,b);}reuse::dynamic_schur::summary();println!("PROFILED_PASSED,84,1834");}\n'
    experiment('profile01',text,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin'],['tools/profile_schur_cost.py','tools/dynamic_schur_refined_sparse_solver.rs','tools/joint_schur_refined_sparse_kernel.rs','tools/schur_refined_sparse_bench.rs','docs/SCHUR_COSTO_PROTOCOLO.md'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate)
if __name__=='__main__':main()
