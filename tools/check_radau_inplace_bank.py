"""Observe original rows, ports and memories; inherit equations only by full trace identity."""
import json
from prepare_vco1_portable import ROOT
from prepare_dynamic_schur import maps
from joint_cycles_analysis import require
from schur_refined_native import experiment
from check_schur_chain_bank import PROXY
from run_dynamic_schur_scaled_diagnostic import MAIN

def validate(work,q):
    require((work/'linear.bin').read_bytes()==(ROOT/'references-local/schur-refined-chainbank01/linear.bin').read_bytes(),'all 396 J/b/correction traces by bytes')
    lines=q['stdout'].splitlines();linear=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('REFINED_LINEAR,')];port=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('PORT,')]
    require(len(linear)==396 and len(port)==336 and lines[-1]=='DIAGNOSTIC_PASSED,84,336,1680,2016','bank scope')
    require(max(x[2] for x in port)<=1 and max(x[3] for x in port)<=2e-11,'original memory/current gates')
    old=json.loads((ROOT/'evidence/voice_schur_refined_chainbank01.json').read_text(encoding='utf8'));require(old['passed'] and old['independent_linear_rows']==181368,'admitted exact reference')
    return dict(linear_solves=396,all_linear_traces_identical=True,independent_linear_rows=0,inherited_independent_linear_rows=181368,independent_linear_checks_reexecuted=False,decimal_precision=100,exact_linear_checks=old['exact_linear_checks'],refinement_histogram={str(i):sum(int(x[0])==i for x in linear) for i in range(4)},target_final_backward_max=max(x[2] for x in linear),memory_observations=1680,terminal_and_ground_currents=2016,memory_max_ratio=max(x[2] for x in port),port_current_max_a=max(x[3] for x in port),full_trajectory_admitted=False)

def main():
    text=(ROOT/'tools/radau_inplace_bench.rs').read_text(encoding='utf8').split('fn main(){')[0]
    kp=(ROOT/'tools/joint_radau_inplace_kernel.rs').read_text(encoding='utf8')
    kp=kp.replace('#[path="dynamic_schur_chain_solver.rs"] pub mod dynamic_schur;','pub mod dynamic_schur{'+PROXY.replace('SOLVER',(ROOT/'tools/dynamic_schur_chain_solver.rs').as_posix())+'}')
    for n in ['latch_charge_driver.rs','contour_closed_driver.rs']:kp=kp.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    kp='\n'.join(x for x in kp.splitlines() if not x.startswith('//!'))
    text=text.replace('#[path="joint_radau_inplace_kernel.rs"] mod reuse;','mod reuse{'+kp+'}')
    for n in ['joint_schur_chain_kernel.rs','joint_lu_extent_kernel.rs']:text=text.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=text.replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())
    _,_,_,raw=maps();node=lambda k:'usize::MAX' if k==134 else str(k if k<108 else k-1);m='['+','.join('['+','.join(node(k) for k in row)+']' for row in raw)+']'
    main=MAIN.replace('MAPS',m).replace(' let args:Vec<_>=std::env::args().collect();',' let args:Vec<_>=std::env::args().collect();std::fs::write(&args[2],b"RFSCLR01").unwrap();',1)
    experiment('radauinplacebank01',text+main,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin','WORK/linear.bin'],['tools/check_radau_inplace_bank.py','tools/check_schur_chain_bank.py','tools/radau_inplace_bench.rs','tools/joint_radau_inplace_kernel.rs','tools/joint_schur_chain_kernel.rs','tools/dynamic_schur_chain_solver.rs','tools/joint_lu_extent_kernel.rs','tools/run_dynamic_schur_scaled_diagnostic.py','docs/RADAU_EN_SITIO_PROTOCOLO.md','evidence/voice_schur_refined_chainbank01.json'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib','references-local/schur-refined-chainbank01/linear.bin'],validate,replay=True)
if __name__=='__main__':main()
