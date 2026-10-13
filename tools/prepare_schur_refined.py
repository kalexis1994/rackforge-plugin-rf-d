"""Freeze the prior rejected experiment; derive only a new numerical kernel and caller."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/dynamic_schur_refined_solver.rs text eol=lf\n/tools/joint_schur_refined_kernel.rs text eol=lf\n/tools/joint_schur_refined_runner.rs text eol=lf\n/tools/schur_refined_bench.rs text eol=lf\n'
def kernel():return (ROOT/'tools/joint_dynamic_schur_fast_kernel.rs').read_text(encoding='utf8').replace('path="dynamic_schur_fast_solver.rs"','path="dynamic_schur_refined_solver.rs"')
def caller():return (ROOT/'tools/joint_dynamic_schur_fast_runner.rs').read_text(encoding='utf8').replace('path="joint_dynamic_schur_fast_kernel.rs"','path="joint_schur_refined_kernel.rs"')
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='869f4eca734ca1ce495d43c86c0a5896715b7b86','base');previous='evidence/voice_dynamic_schur_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));require(old['passed'] and not old['dynamic_schur_admitted'],'rejected baseline retained')
    write('evidence/voice_schur_refined_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    p=ROOT/'tools/dynamic_schur_refined_solver.rs';s=p.read_text(encoding='utf8');require('/*MAPS*/' in s,'new solver');maps='\n'.join(x for x in (ROOT/'tools/dynamic_schur_fast_solver.rs').read_text(encoding='utf8').splitlines() if x.startswith('const '));p.write_text(s.replace('/*MAPS*/',maps),encoding='utf8',newline='\n')
    for n,s in [('tools/joint_schur_refined_kernel.rs',kernel()),('tools/joint_schur_refined_runner.rs',caller()),('tools/schur_refined_bench.rs',(ROOT/'tools/dynamic_schur_fast_bench.rs').read_text(encoding='utf8').replace('joint_dynamic_schur_fast_kernel.rs','joint_schur_refined_kernel.rs'))]:
        p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);private={n:sha(ROOT/n) for n in ['references-local/dynamic-schur-scaled-inspection01/failed-system.bin','references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib']}
    for n,h in private.items():require(h==old['private_input_sha256'][n],'frozen private '+n)
    write('evidence/voice_schur_refined_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_schur_refined.py','tools/dynamic_schur_refined_solver.rs','tools/joint_schur_refined_kernel.rs','tools/joint_schur_refined_runner.rs','tools/schur_refined_bench.rs','docs/SCHUR_REFINADO_PROTOCOLO.md']},private_used_sha256=private,maximum_refinements=3,mixed_backward_gate=1e-11,correction_v=2e-9,correction_a=2e-12))
if __name__=='__main__':main()
