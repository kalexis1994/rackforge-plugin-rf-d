"""Pair loaded-chain condensation against the admitted contour Schur."""
from prepare_vco1_portable import ROOT
from run_schur_inplace_bench import validate
from schur_refined_native import experiment

def main():
    text=(ROOT/'tools/schur_chain_bench.rs').read_text(encoding='utf8')
    for n in ['joint_lu_extent_kernel.rs','joint_schur_contour_kernel.rs','joint_schur_chain_kernel.rs']:text=text.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=text.replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())
    experiment('chainbench01',text,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin','WORK/roots.txt'],['tools/run_schur_chain_bench.py','tools/run_schur_inplace_bench.py','tools/schur_chain_bench.rs','tools/dynamic_schur_chain_solver.rs','tools/joint_schur_chain_kernel.rs','tools/dynamic_schur_contour_solver.rs','tools/joint_schur_contour_kernel.rs','tools/joint_lu_extent_kernel.rs','docs/SCHUR_CADENA_PROTOCOLO.md','evidence/voice_schur_chain_inputs01.json'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate)
if __name__=='__main__':main()
