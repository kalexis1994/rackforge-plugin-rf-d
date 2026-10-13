"""Only constructor/facade inline directives, derived from the frozen numerical solver."""
import json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/dynamic_schur_inline_solver.rs text eol=lf\n/tools/joint_schur_inline_kernel.rs text eol=lf\n/tools/joint_schur_inline_runner.rs text eol=lf\n/tools/schur_inline_bench.rs text eol=lf\n'
def solver():
    s=(ROOT/'tools/dynamic_schur_refined_sparse_solver.rs').read_text(encoding='utf8')
    for signature in [' fn factor(mut a:',' fn new(j:','pub fn solve_observed(j:','pub fn solve(j:']:
        require(signature in s,'declared constructor');s=s.replace(signature,(' #[inline(always)]\n' if signature.startswith(' ') else '#[inline(always)]\n')+signature)
    require(s.count('#[inline(always)]')==5,'five directives');return s
def kernel():return (ROOT/'tools/joint_schur_refined_sparse_kernel.rs').read_text(encoding='utf8').replace('dynamic_schur_refined_sparse_solver.rs','dynamic_schur_inline_solver.rs')
def caller():return (ROOT/'tools/joint_schur_refined_sparse_runner.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_inline_kernel.rs')
def main():
    r=json.loads((ROOT/'evidence/voice_schur_refined_profile01.json').read_text(encoding='utf8'));require(r['passed'] and r['prepare_fraction_of_solve']>.8,'profile evidence');write('evidence/voice_schur_cost_inline_decision01.json',dict(passed=True,profile_sha256=sha(ROOT/'evidence/voice_schur_refined_profile01.json'),baseline_solver_sha256=sha(ROOT/'tools/dynamic_schur_refined_sparse_solver.rs'),only_inline_directives=True,numerical_gates_changed=False))
    for n,s in [('tools/dynamic_schur_inline_solver.rs',solver()),('tools/joint_schur_inline_kernel.rs',kernel()),('tools/joint_schur_inline_runner.rs',caller()),('tools/schur_inline_bench.rs',(ROOT/'tools/schur_refined_sparse_bench.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_inline_kernel.rs'))]:
        p=ROOT/n;require(not p.exists(),'exclusive candidate');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);old=json.loads((ROOT/'evidence/voice_lu_extent_inputs01.json').read_text(encoding='utf8'));write('evidence/voice_schur_cost_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_schur_inline.py','tools/dynamic_schur_inline_solver.rs','tools/joint_schur_inline_kernel.rs','tools/joint_schur_inline_runner.rs','tools/schur_inline_bench.rs','docs/SCHUR_COSTO_PROTOCOLO.md','docs/SCHUR_CONSTRUCCION_INLINE.md']},private_used_sha256={n:sha(ROOT/n) for n in ['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib']},seeds=old['seeds'],mixed_backward_gate=1e-11,maximum_refinements=3,nonzero_capacity=4096))
if __name__=='__main__':main()
