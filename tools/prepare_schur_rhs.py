"""Finite-row invariant permits exact-zero skips without per-product finiteness checks."""
import json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'/tools/dynamic_schur_rhs_solver.rs text eol=lf\n/tools/joint_schur_rhs_kernel.rs text eol=lf\n/tools/joint_schur_rhs_runner.rs text eol=lf\n/tools/schur_rhs_bench.rs text eol=lf\n'
def solver():
    s=(ROOT/'tools/dynamic_schur_refined_sparse_solver.rs').read_text(encoding='utf8');s=s.replace('let mut x=[0.;N]','let mut x=[0_f64;N]',1)
    for old in ['for col in 0..row{v-=self.a[row][col]*x[col];}','for col in row+1..N{v-=self.a[row][col]*x[col];}']:
        require(old in s,'original substitution');head=old.split('{')[0];s=s.replace(old,head+'{let a=self.a[row][col];if a==0.&&v!=0.{continue;}v-=a*x[col];}',1)
    s=s.replace('x[row]=v;}','if !v.is_finite(){return Err(StepError::SingularJacobian);}x[row]=v;}',1).replace('x[row]=v/self.a[row][row];}','x[row]=v/self.a[row][row];if !x[row].is_finite(){return Err(StepError::SingularJacobian);}}',1);return s
def kernel():return (ROOT/'tools/joint_schur_refined_sparse_kernel.rs').read_text(encoding='utf8').replace('dynamic_schur_refined_sparse_solver.rs','dynamic_schur_rhs_solver.rs')
def caller():return (ROOT/'tools/joint_schur_refined_sparse_runner.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_rhs_kernel.rs')
def main():
    r=json.loads((ROOT/'evidence/voice_schur_refined_supportbench02.json').read_text(encoding='utf8'));require(r['passed'] and not r['utility_passed'],'second hypothesis retained');write('evidence/voice_schur_cost_rhs_decision01.json',dict(passed=True,numerical_gates_changed=False,previous_bench_sha256=sha(ROOT/'evidence/voice_schur_refined_supportbench02.json'),previous_bank_sha256=sha(ROOT/'evidence/voice_schur_refined_supportbank01.json'),previous_source_sha256={n:sha(ROOT/n) for n in ['tools/dynamic_schur_support_solver.rs','tools/prepare_schur_support.py','tools/joint_schur_support_kernel.rs','tools/schur_support_bench.rs']}))
    for n,s in [('tools/dynamic_schur_rhs_solver.rs',solver()),('tools/joint_schur_rhs_kernel.rs',kernel()),('tools/joint_schur_rhs_runner.rs',caller()),('tools/schur_rhs_bench.rs',(ROOT/'tools/schur_refined_sparse_bench.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_rhs_kernel.rs'))]:
        p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);r=json.loads((ROOT/'evidence/voice_schur_cost_inputs03.json').read_text(encoding='utf8'));r['source_sha256']={n:sha(ROOT/n) for n in ['tools/prepare_schur_rhs.py','tools/dynamic_schur_rhs_solver.rs','tools/joint_schur_rhs_kernel.rs','tools/joint_schur_rhs_runner.rs','tools/schur_rhs_bench.rs','docs/SCHUR_RHS_FINITO.md']};r.pop('type_repair_sha256',None);write('evidence/voice_schur_cost_inputs04.json',r)
if __name__=='__main__':main()
