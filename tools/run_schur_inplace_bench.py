"""Paired whole-step cost and raw-reference candidate gates for refined Schur."""
import statistics
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
from schur_refined_native import experiment
def validate(work,q):
    lines=q['stdout'].splitlines();cases=[x.split(',') for x in lines if x.startswith('CASE,')];rounds=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('ROUND,')];require(len(cases)==84 and [int(x[1]) for x in cases]==list(range(84)) and len(rounds)==5 and [r[0] for r in rounds]==list(range(5)) and lines[-1]=='PASSED,84,5,reconstructed_candidate_gates','paired bank scope');speed=[r[1]/r[2] for r in rounds];require(max(float(c[-1]) for c in cases)<=1,'candidate gates');return dict(selected_pairs=84,rounds=rounds,speedups=speed,median_paired_speedup=statistics.median(speed),utility_passed=statistics.median(speed)>1,max_candidate_gate_ratio=max(float(c[-1]) for c in cases),full_trajectory_admitted=False)
def main():
    text=(ROOT/'tools/schur_inplace_bench.rs').read_text(encoding='utf8')
    for n in ['joint_lu_extent_kernel.rs','joint_schur_inplace_kernel.rs']:text=text.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    text=text.replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())
    experiment('inplacebench01',text,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin','WORK/roots.txt'],['tools/run_schur_inplace_bench.py','tools/schur_inplace_bench.rs','tools/dynamic_schur_inplace_solver.rs','tools/joint_schur_inplace_kernel.rs','tools/joint_lu_extent_kernel.rs','docs/SCHUR_EN_SITIO_PROTOCOLO.md','evidence/voice_schur_inplace_inputs01.json'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate)
if __name__=='__main__':main()
