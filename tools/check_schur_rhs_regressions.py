"""Loaded-stage regressions plus fixed-capacity, nonfinite and refinement-budget rejection."""
from prepare_vco1_portable import ROOT
from prepare_dynamic_schur import maps
from check_dynamic_schur_structure import MAIN
from schur_refined_native import experiment
from joint_cycles_analysis import require
PROBES='''fn probes(){
 let identity=||std::array::from_fn(|i|std::array::from_fn(|k|if i==k{1_f64}else{0.}));
 let cases:[(&str,[[f64;8];8],[f64;8]);9]=[
 ("positive_zero",identity(),[0.;8]),("negative_zero",identity(),[-0.;8]),
 ("signed_zero_coefficients",{let mut a=identity();a[1][0]=-0.;a[2][1]=-0.;a},[1.,-0.,0.,-2.,-0.,0.,3.,0.]),
 ("subnormal",identity(),[f64::from_bits(1),-f64::from_bits(1),0.,-0.,1e-300,-1e-300,0.,-0.]),
 ("pivot",{let mut a=identity();a[0][0]=0.;a[0][1]=1.;a[1][0]=1.;a[1][1]=2.;a},[1.,2.,3.,4.,5.,6.,7.,8.]),
 ("overflow",{let mut a=identity();a[0][0]=1e-300;a},[f64::MAX;8]),
 ("nan_rhs",identity(),[f64::NAN;8]),("infinite_rhs",identity(),[f64::INFINITY;8]),
 ("singular",[[0.;8];8],[1.;8])];
 for(label,a,b)in cases{let old=source_base::probe(a,b);let new=source_candidate::probe(a,b);match(old,new){(Ok(x),Ok(y))=>assert_eq!(x.map(f64::to_bits),y.map(f64::to_bits),"{label}"),(Err(e),Err(f))=>assert_eq!(format!("{e:?}"),format!("{f:?}"),"{label}"),_=>panic!("different acceptance {label}")};println!("SUBSTITUTION,{label}");}println!("SUBSTITUTION_PASSED,9");
}
'''

def validate(work,q):
    lines=q['stdout'].splitlines();require(lines[-1]=='STRUCTURAL_PASSED,12' and len([x for x in lines if x.startswith('STRUCTURE,')])==12,'twelve finite structural regressions');require(len([x for x in lines if x.startswith('SUBSTITUTION,')])==9,'nine substitution controls');return dict(regressions=21,structural_regressions=12,substitution_regressions=9,full_trajectory_admitted=False,zero_budget_variant_is_test_only=True)

def main():
    kernel=(ROOT/'tools/joint_schur_rhs_kernel.rs').read_text(encoding='utf8');budget='\n'.join(x for x in kernel.splitlines() if not x.startswith('//!'));solver='\n'.join(x for x in (ROOT/'tools/dynamic_schur_rhs_solver.rs').read_text(encoding='utf8').splitlines() if not x.startswith('//!'));require('MAX_REFINEMENTS:usize=3' in solver,'production budget');solver=solver.replace('MAX_REFINEMENTS:usize=3','MAX_REFINEMENTS:usize=0',1);budget=budget.replace('#[path="dynamic_schur_rhs_solver.rs"] pub mod dynamic_schur;','pub mod dynamic_schur{'+solver+'}')
    for n in ['latch_charge_driver.rs','contour_closed_driver.rs']:budget=budget.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=MAIN.replace('KERNEL',(ROOT/'tools/joint_schur_rhs_kernel.rs').as_posix());text='mod budget{'+budget+'}\n'+text
    external=maps()[2][:80];extra='''let mut j=identity();let external:[usize;80]=EXTERNAL;for &i in &external{for &k in &external{j[i][k]=1.;}}assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::InvalidInput)));println!("STRUCTURE,capacity_rejection");
 let mut j=identity();j[0][0]=f64::NAN;assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::InvalidInput)));println!("STRUCTURE,nonfinite_rejection");
 let args:Vec<_>=std::env::args().collect();let bytes=std::fs::read(&args[1]).unwrap();let v:Vec<f64>=bytes[8..].chunks_exact(8).map(|b|f64::from_le_bytes(b.try_into().unwrap())).collect();let j=std::array::from_fn(|i|std::array::from_fn(|k|v[i*458+k]));let b=std::array::from_fn(|k|v[458*458+k]);assert!(matches!(budget::dynamic_schur::solve(j,b),Err(rf_d_circuit::StepError::IterationBudget)));println!("STRUCTURE,zero_budget_rejection");
 println!("STRUCTURAL_PASSED,12");'''.replace('EXTERNAL',str(external))
    text=text.replace('println!("STRUCTURAL_PASSED,9");',extra)
    old='\n'.join(x for x in (ROOT/'tools/dynamic_schur_refined_sparse_solver.rs').read_text(encoding='utf8').splitlines() if not x.startswith('//!'));new='\n'.join(x for x in (ROOT/'tools/dynamic_schur_rhs_solver.rs').read_text(encoding='utf8').splitlines() if not x.startswith('//!'));probe='pub fn probe(a:[[f64;8];8],b:[f64;8])->Result<[f64;8],StepError>{Lu::factor(a)?.solve(b)}';text='use rf_d_circuit::StepError;mod source_base{'+old+probe+'}mod source_candidate{'+new+probe+'}'+text;text+=PROBES;text=text.replace('println!(\"STRUCTURAL_PASSED,12\");','probes();println!(\"STRUCTURAL_PASSED,12\");')
    experiment('rhsstructure01',text,[ROOT/'references-local/dynamic-schur-scaled-inspection01/failed-system.bin'],['tools/check_schur_rhs_regressions.py','tools/check_dynamic_schur_structure.py','tools/dynamic_schur_rhs_solver.rs','tools/joint_schur_rhs_kernel.rs','docs/SCHUR_REFINADO_PROTOCOLO.md','docs/SCHUR_RHS_FINITO.md'],['references-local/dynamic-schur-scaled-inspection01/failed-system.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate,replay=True,timeout=120)
if __name__=='__main__':main()
