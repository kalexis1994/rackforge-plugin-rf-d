"""Pair in-place Radau assembly against the admitted loaded-chain kernel."""
from prepare_vco1_portable import ROOT
from run_schur_inplace_bench import validate as original_validate
from schur_refined_native import experiment
from joint_cycles_analysis import require

def validate(work,q):
    r=original_validate(work,q)
    require((work/'roots.txt').read_bytes()==(ROOT/'references-local/schur-refined-chainbench01/roots.txt').read_bytes(),'all 84 admitted roots by bytes')
    return dict(**r,exact_bit_fields_per_pair=1834,iterations_and_trials_identical=True,roots_identical=True)

def main():
    text=(ROOT/'tools/radau_inplace_bench.rs').read_text(encoding='utf8')
    for n in ['joint_lu_extent_kernel.rs','joint_schur_chain_kernel.rs','joint_radau_inplace_kernel.rs']:text=text.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=text.replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())
    experiment('radauinplacebench01',text,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin','WORK/roots.txt'],['tools/run_radau_inplace_bench.py','tools/run_schur_inplace_bench.py','tools/radau_inplace_bench.rs','tools/joint_radau_inplace_kernel.rs','tools/joint_schur_chain_kernel.rs','tools/dynamic_schur_chain_solver.rs','tools/joint_lu_extent_kernel.rs','docs/RADAU_EN_SITIO_PROTOCOLO.md','evidence/voice_radau_inplace_inputs01.json'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib','references-local/schur-refined-chainbench01/roots.txt'],validate)
if __name__=='__main__':main()
