"""Loaded-stage regressions plus fixed-capacity, nonfinite and refinement-budget rejection."""
from prepare_vco1_portable import ROOT
from prepare_dynamic_schur import maps
from check_dynamic_schur_structure import MAIN
from schur_refined_native import experiment
from joint_cycles_analysis import require

def validate(work,q):
    lines=q['stdout'].splitlines();require(lines[-1]=='STRUCTURAL_PASSED,12' and len([x for x in lines if x.startswith('STRUCTURE,')])==12,'twelve finite structural regressions');return dict(regressions=12,full_trajectory_admitted=False,zero_budget_variant_is_test_only=True)

def main():
    kernel=(ROOT/'tools/joint_schur_inline_kernel.rs').read_text(encoding='utf8');budget='\n'.join(x for x in kernel.splitlines() if not x.startswith('//!'));solver='\n'.join(x for x in (ROOT/'tools/dynamic_schur_inline_solver.rs').read_text(encoding='utf8').splitlines() if not x.startswith('//!'));require('MAX_REFINEMENTS:usize=3' in solver,'production budget');solver=solver.replace('MAX_REFINEMENTS:usize=3','MAX_REFINEMENTS:usize=0',1);budget=budget.replace('#[path="dynamic_schur_inline_solver.rs"] pub mod dynamic_schur;','pub mod dynamic_schur{'+solver+'}')
    for n in ['latch_charge_driver.rs','contour_closed_driver.rs']:budget=budget.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=MAIN.replace('KERNEL',(ROOT/'tools/joint_schur_inline_kernel.rs').as_posix());text='mod budget{'+budget+'}\n'+text
    external=maps()[2][:80];extra='''let mut j=identity();let external:[usize;80]=EXTERNAL;for &i in &external{for &k in &external{j[i][k]=1.;}}assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::InvalidInput)));println!("STRUCTURE,capacity_rejection");
 let mut j=identity();j[0][0]=f64::NAN;assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::InvalidInput)));println!("STRUCTURE,nonfinite_rejection");
 let args:Vec<_>=std::env::args().collect();let bytes=std::fs::read(&args[1]).unwrap();let v:Vec<f64>=bytes[8..].chunks_exact(8).map(|b|f64::from_le_bytes(b.try_into().unwrap())).collect();let j=std::array::from_fn(|i|std::array::from_fn(|k|v[i*458+k]));let b=std::array::from_fn(|k|v[458*458+k]);assert!(matches!(budget::dynamic_schur::solve(j,b),Err(rf_d_circuit::StepError::IterationBudget)));println!("STRUCTURE,zero_budget_rejection");
 println!("STRUCTURAL_PASSED,12");'''.replace('EXTERNAL',str(external))
    text=text.replace('println!("STRUCTURAL_PASSED,9");',extra)
    experiment('inlinestructure01',text,[ROOT/'references-local/dynamic-schur-scaled-inspection01/failed-system.bin'],['tools/check_schur_inline_structure.py','tools/check_dynamic_schur_structure.py','tools/dynamic_schur_inline_solver.rs','tools/joint_schur_inline_kernel.rs','docs/SCHUR_REFINADO_PROTOCOLO.md','docs/SCHUR_CONSTRUCCION_INLINE.md'],['references-local/dynamic-schur-scaled-inspection01/failed-system.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate,replay=True,timeout=120)
if __name__=='__main__':main()
