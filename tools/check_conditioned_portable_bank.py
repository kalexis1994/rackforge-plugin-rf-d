"""Public-library roots, complete stamps and replay of frozen original linear systems."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
from conditioned_portable_native import experiment
MAIN='''macro_rules! input{($name:ident,$m:ident)=>{fn $name(c:&Case)->($m::Parameters,$m::State,[$m::State;2]){
 let(mut a,b,d)=lab::lab_parameters();a.r61_ohm=200.;let mut chain=Chain{circuit:a,conversion:b,headphone:d,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};chain.boundary.panel.cutoff_fraction_from_neg10=1.;let mut p=$m::Parameters::new(Controls::default(),chain,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap();p.final_decay=c.on;p.keyboard=[0.,10.,0.][c.phase];p.short=c.phase==1;
 let state=|i:usize|$m::State{high:std::array::from_fn(|k|c.states[i][k]),low:std::array::from_fn(|k|c.states[i][k+229])};(p,state(0),[state(1),state(2)])
}}}
input!(reference_input,reference);input!(public_input,public);
fn fields(q:public::Pair)->(Vec<u64>,usize,usize){let mut out=Vec::with_capacity(1834);for s in q.increments.into_iter().chain(q.candidates){out.extend(s.high.into_iter().chain(s.low).map(f64::to_bits));}out.extend([q.residual_ratio.to_bits(),q.correction_ratio.to_bits()]);(out,q.iterations,q.trials)}
#[inline(never)]fn stamp(c:&Case){let(p,o,d)=reference_input(c);let a=reference::linearize(p,o,d,c.h).unwrap();let(p,o,d)=public_input(c);let b=public::linearize(p,o,d,c.h).unwrap();for i in 0..458{assert_eq!(a.residual[i].to_bits(),b.residual[i].to_bits());for k in 0..458{assert_eq!(a.jacobian[i][k].to_bits(),b.jacobian[i][k].to_bits());}}for i in 0..2{assert_eq!(a.candidates[i].high.map(f64::to_bits),b.candidates[i].high.map(f64::to_bits));assert_eq!(a.candidates[i].low.map(f64::to_bits),b.candidates[i].low.map(f64::to_bits));}}
#[inline(never)]fn linear(path:&str,out:&str){
 use std::io::Write;let raw=std::fs::read(path).unwrap();assert_eq!(&raw[..8],b"RFSCLR01");let mut p=8;let mut count=0;let mut target=std::fs::File::create(out).unwrap();target.write_all(b"RFPUBL01").unwrap();
 while p<raw.len(){let nnz=u32::from_le_bytes(raw[p..p+4].try_into().unwrap()) as usize;p+=4;let mut j=[[0.;458];458];for _ in 0..nnz{let i=u16::from_le_bytes(raw[p..p+2].try_into().unwrap()) as usize;let k=u16::from_le_bytes(raw[p+2..p+4].try_into().unwrap()) as usize;let a=f64::from_le_bytes(raw[p+4..p+12].try_into().unwrap());p+=12;j[i][k]=a;}let f=|k:usize|f64::from_le_bytes(raw[p+8*k..p+8*k+8].try_into().unwrap());let b=std::array::from_fn(f);let expected:[f64;458]=std::array::from_fn(|k|f(458+k));let q=public::dynamic_schur::solve_observed(j,b).unwrap();assert_eq!(q.correction.map(f64::to_bits),expected.map(f64::to_bits));assert!(q.final_backward<=1e-11);for v in q.correction{target.write_all(&v.to_le_bytes()).unwrap();}p+=1832*8;count+=1;}
 assert_eq!(p,raw.len());assert_eq!(count,396);println!("PUBLIC_LINEAR,396,181368,exact_correction_bits");
}
fn main(){let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),84);let mut workspace=public::Workspace::new();let mut roots=std::fs::File::create(&args[3]).unwrap();
 for(i,c)in cs.iter().enumerate(){stamp(c);let expected=run_reference(c);let(p,o,_)=public_input(c);let actual=fields(workspace.step(p,o,c.h).unwrap());assert_eq!(expected,actual,"public root {i}");save(&mut roots,c,&actual);}
 for &i in &[0,83,0]{let c=&cs[i];let(p,o,_)=public_input(c);assert_eq!(fields(workspace.step(p,o,c.h).unwrap()),run_reference(c));}
 let c=&cs[0];let(mut p,o,_)=public_input(c);p.keyboard=11.;assert!(workspace.step(p,o,c.h).is_err());let(p,o,_)=public_input(c);assert_eq!(fields(workspace.step(p,o,c.h).unwrap()),run_reference(c));
 println!("PUBLIC_STAMPS,84,17620176,38472,76944");println!("PUBLIC_WORKSPACE,reuse84,A_B_A,error_recovery");linear(&args[2],&args[4]);println!("PUBLIC_BANK_PASSED,84,396");
}
'''

def validate(work,q):
    lines=q['stdout'].splitlines();require(lines[-1]=='PUBLIC_BANK_PASSED,84,396' and 'PUBLIC_STAMPS,84,17620176,38472,76944' in lines and 'PUBLIC_WORKSPACE,reuse84,A_B_A,error_recovery' in lines,'public bank scope')
    require((work/'roots.txt').read_bytes()==(ROOT/'references-local/schur-refined-radauinplacebench01/roots.txt').read_bytes(),'84 frozen roots by bytes')
    raw=(work/'corrections.bin').read_bytes();require(len(raw)==8+396*458*8 and raw[:8]==b'RFPUBL01','all replayed corrections')
    return dict(public_roots=84,root_bit_fields_per_pair=1834,iterations_and_trials_identical=True,roots_identical=True,complete_stamps=84,jacobian_bit_coordinates=17620176,residual_bit_coordinates=38472,candidate_high_low_bit_coordinates=76944,stored_linear_systems_replayed=396,replayed_linear_corrections_bit_coordinates=181368,linear_corrections_identical=True,active_linear_archive_exported=False,inherited_independent_linear_rows=181368,inherited_bank_nonlinear_rows=38472,independent_equations_reexecuted=0,workspace_reuse_across_all_cases=True,workspace_error_recovery=True,full_trajectory_admitted=False)

def main():
    s=(ROOT/'tools/radau_inplace_bench.rs').read_text(encoding='utf8').split('fn main(){')[0]
    s=s.replace('path="joint_schur_chain_kernel.rs"','path="'+(ROOT/'tools/joint_radau_inplace_kernel.rs').as_posix()+'"')
    for n in ['joint_radau_inplace_kernel.rs','joint_lu_extent_kernel.rs']:s=s.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    s=s.replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix());s+='use rf_d_circuit::conditioned_voice as public;\n'
    experiment('bank02',s+MAIN,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin',ROOT/'references-local/schur-refined-radauinplacebank01/linear.bin','WORK/roots.txt','WORK/corrections.bin'],['tools/check_conditioned_portable_bank.py','tools/radau_inplace_bench.rs','tools/joint_radau_inplace_kernel.rs','tools/dynamic_schur_chain_solver.rs','docs/CONJUNTO_PORTABLE_PROTOCOLO.md'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/schur-refined-radauinplacebank01/linear.bin','references-local/schur-refined-radauinplacebench01/roots.txt'],validate)
if __name__=='__main__':main()
