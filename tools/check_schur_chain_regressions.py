"""Loaded-stage regressions plus fixed-capacity, nonfinite and refinement-budget rejection."""
from prepare_vco1_portable import ROOT
from prepare_dynamic_schur import maps
from check_dynamic_schur_structure import MAIN
from schur_refined_native import experiment
from joint_cycles_analysis import require
WORKSPACE='''pub fn workspace(){
 let identity=||std::array::from_fn(|i|std::array::from_fn(|k|if i==k{1_f64}else{0.}));let a=identity();let mut changed=identity();changed[56][56]=3.;changed[285][285]=4.;changed[56][285]=0.75;changed[285][56]=-0.5;changed[200][200]=3.;changed[429][429]=4.;changed[200][429]=0.75;changed[429][200]=-0.5;changed[200][165]=-0.2;changed[165][200]=0.4;changed[133][133]=3.;changed[362][362]=4.;changed[133][362]=0.75;changed[362][133]=-0.5;changed[133][12]=-0.2;changed[12][133]=0.4;changed[133][165]=-0.15;changed[165][133]=0.25;changed[56][8]=-0.2;changed[8][56]=0.4;
 let b:[f64;458]=std::array::from_fn(|k|((k%17) as f64-8.)*1e-3);
 let fresh=|j:&[[f64;458];458]|{let mut p=Prepared::blank();p.initialize(j).unwrap();p.correction(j,b).unwrap().map(f64::to_bits)};
 let mut p=Prepared::blank();for j in [&a,&changed,&a]{p.initialize(j).unwrap();assert_eq!(p.correction(j,b).unwrap().map(f64::to_bits),fresh(j));}println!("WORKSPACE,changed_matrix_reuse");
 let mut bad=identity();for kind in 0..10{for row in 0..458{bad[row].copy_from_slice(&changed[row]);}let label=match kind{0=>{bad[0][0]=f64::NAN;"after_nonfinite"},1=>{bad[56]=[0.;458];"after_singular"},2=>{bad[56][134]=1.;"after_coupling"},3=>{for &i in &EXTERNAL[..80]{for &k in &EXTERNAL[..80]{bad[i][k]=1.;}}"after_capacity"},4=>{bad[200]=[0.;458];"after_contour_singular"},5=>{bad[200][134]=1.;"after_contour_voltage"},6=>{bad[134][200]=1.;"after_contour_return"},7=>{bad[133]=[0.;458];"after_chain_singular"},8=>{bad[133][0]=1.;"after_chain_voltage"},_=>{bad[0][133]=1.;"after_chain_return"}};assert!(p.initialize(&bad).is_err());p.initialize(&a).unwrap();assert_eq!(p.correction(&a,b).unwrap().map(f64::to_bits),fresh(&a));println!("WORKSPACE,{label}");}
}
'''
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
    lines=q['stdout'].splitlines();require(lines[-1]=='STRUCTURAL_PASSED,25' and len([x for x in lines if x.startswith('STRUCTURE,')])==25,'twenty-five finite structural regressions');require(len([x for x in lines if x.startswith('SUBSTITUTION,')])==9,'nine substitution controls');require(len([x for x in lines if x.startswith('WORKSPACE,')])==11,'eleven reinitialization controls');return dict(regressions=45,workspace_regressions=11,structural_regressions=25,substitution_regressions=9,full_trajectory_admitted=False,zero_budget_variant_is_test_only=True)

def main():
    kernel=(ROOT/'tools/joint_schur_chain_kernel.rs').read_text(encoding='utf8');budget='\n'.join(x for x in kernel.splitlines() if not x.startswith('//!'));solver='\n'.join(x for x in (ROOT/'tools/dynamic_schur_chain_solver.rs').read_text(encoding='utf8').splitlines() if not x.startswith('//!'));require('MAX_REFINEMENTS:usize=3' in solver,'production budget');solver=solver.replace('MAX_REFINEMENTS:usize=3','MAX_REFINEMENTS:usize=0',1);budget=budget.replace('#[path="dynamic_schur_chain_solver.rs"] pub mod dynamic_schur;','pub mod dynamic_schur{'+solver+'}')
    for n in ['latch_charge_driver.rs','contour_closed_driver.rs']:budget=budget.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=MAIN.replace('KERNEL',(ROOT/'tools/joint_schur_chain_kernel.rs').as_posix());text='mod budget{'+budget+'}\n'+text
    external=maps()[2][:80];extra='''let mut j=identity();let external:[usize;80]=EXTERNAL;for &i in &external{for &k in &external{j[i][k]=1.;}}assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::InvalidInput)));println!("STRUCTURE,capacity_rejection");
 let mut j=identity();j[0][0]=f64::NAN;assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::InvalidInput)));println!("STRUCTURE,nonfinite_rejection");
 let args:Vec<_>=std::env::args().collect();let bytes=std::fs::read(&args[1]).unwrap();let v:Vec<f64>=bytes[8..].chunks_exact(8).map(|b|f64::from_le_bytes(b.try_into().unwrap())).collect();let j=std::array::from_fn(|i|std::array::from_fn(|k|v[i*458+k]));let b=std::array::from_fn(|k|v[458*458+k]);assert!(matches!(budget::dynamic_schur::solve(j,b),Err(rf_d_circuit::StepError::IterationBudget)));println!("STRUCTURE,zero_budget_rejection");
let mut j=identity();j[200][200]=3.;j[429][429]=4.;j[200][429]=0.75;j[429][200]=-0.5;j[200][165]=-0.2;j[429][394]=-0.3;j[165][200]=0.4;j[394][429]=-0.6;j[165][394]=0.125;compare(j);println!("STRUCTURE,contour_two_stage_loaded_mass");
 let mut j=identity();j[200][200]=0.;j[200][201]=1.;j[201][200]=1.;j[201][201]=2.;compare(j);println!("STRUCTURE,contour_pivot");
 let mut j=identity();for kind in 0..4{for row in 0..458{j[row].fill(0.);j[row][row]=1.;}let label=match kind{0=>{j[200]=[0.;458];"contour_singular"},1=>{j[200][134]=1.;"contour_foreign_voltage"},2=>{j[134][200]=1.;"contour_foreign_return"},_=>{j[200][56]=1.;"contour_cross_chip"}};assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::SingularJacobian)));println!("STRUCTURE,{label}");}
let mut j=identity();j[133][133]=3.;j[362][362]=4.;j[133][362]=0.75;j[362][133]=-0.5;j[133][12]=-0.2;j[362][241]=-0.3;j[12][133]=0.4;j[241][362]=-0.6;j[133][165]=-0.125;j[165][133]=0.25;j[165][394]=0.125;compare(j);println!("STRUCTURE,chain_two_stage_loaded_mass");
 let mut j=identity();j[133][165]=-0.2;j[165][133]=0.4;j[200][165]=-0.3;j[165][200]=0.6;j[133][133]=3.;j[200][200]=4.;compare(j);println!("STRUCTURE,chain_contour_shared_port");
 let mut j=identity();j[133][133]=0.;j[133][134]=1.;j[134][133]=1.;j[134][134]=2.;compare(j);println!("STRUCTURE,chain_pivot");
 let mut j=identity();for kind in 0..4{for row in 0..458{j[row].fill(0.);j[row][row]=1.;}let label=match kind{0=>{j[133]=[0.;458];"chain_singular"},1=>{j[133][0]=1.;"chain_foreign_voltage"},2=>{j[0][133]=1.;"chain_foreign_return"},_=>{j[133][200]=1.;"chain_cross_contour"}};assert!(matches!(kernel::dynamic_schur::solve(j,[0.;458]),Err(rf_d_circuit::StepError::SingularJacobian)));println!("STRUCTURE,{label}");}
 println!("STRUCTURAL_PASSED,25");'''.replace('EXTERNAL',str(external))
    text=text.replace('println!("STRUCTURAL_PASSED,9");',extra)
    old='\n'.join(x for x in (ROOT/'tools/dynamic_schur_refined_sparse_solver.rs').read_text(encoding='utf8').splitlines() if not x.startswith('//!'));new='\n'.join(x for x in (ROOT/'tools/dynamic_schur_chain_solver.rs').read_text(encoding='utf8').splitlines() if not x.startswith('//!'));probe='pub fn probe(a:[[f64;8];8],b:[f64;8])->Result<[f64;8],StepError>{Lu::factor(a)?.solve(b)}';inplace_probe='pub fn probe(a:[[f64;8];8],b:[f64;8])->Result<[f64;8],StepError>{let mut lu=Lu{a,perm:[0;8]};lu.factor_in_place()?;lu.solve(b)}';text='use rf_d_circuit::StepError;mod source_base{'+old+probe+'}mod source_candidate{'+new+inplace_probe+WORKSPACE+'}'+text;text+=PROBES;text=text.replace('println!(\"STRUCTURAL_PASSED,25\");','probes();source_candidate::workspace();println!(\"STRUCTURAL_PASSED,25\");')
    # End the structural driver frame before running workspace probes.
    # Keep the same 32 MiB stack and the unchanged solver/cases.
    require(text.count('fn main(){')==1,'single structural entry')
    text=text.replace('fn main(){','#[inline(never)] fn structural(){',1)
    require(text.count('probes();source_candidate::workspace();println!("STRUCTURAL_PASSED,25");')==1,'driver frame boundary')
    text=text.replace('probes();source_candidate::workspace();println!("STRUCTURAL_PASSED,25");','',1)
    text+='fn main(){structural();probes();source_candidate::workspace();println!("STRUCTURAL_PASSED,25");}'
    experiment('chainstructure02',text,[ROOT/'references-local/dynamic-schur-scaled-inspection01/failed-system.bin'],['tools/check_schur_chain_regressions.py','tools/check_dynamic_schur_structure.py','tools/dynamic_schur_chain_solver.rs','tools/joint_schur_chain_kernel.rs','docs/SCHUR_REFINADO_PROTOCOLO.md','docs/SCHUR_CADENA_PROTOCOLO.md'],['references-local/dynamic-schur-scaled-inspection01/failed-system.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate,replay=True,timeout=120)
if __name__=='__main__':main()
