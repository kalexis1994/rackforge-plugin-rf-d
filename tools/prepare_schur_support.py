"""Exact-support frontier checks and IEEE-safe zero product omission only."""
import json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'/tools/dynamic_schur_support_solver.rs text eol=lf\n/tools/joint_schur_support_kernel.rs text eol=lf\n/tools/joint_schur_support_runner.rs text eol=lf\n/tools/schur_support_bench.rs text eol=lf\n'
GUARD='''  let mut owner=[2_usize;458];let mut allowed=[[false;458];2];for block in 0..2{for &k in &INNER[block]{owner[k]=block;allowed[block][k]=true;}for &k in &PORTS[block]{if k!=usize::MAX{allowed[block][k]=true;}}}
  for i in 0..458{for entry in sparse.row[i]..sparse.row[i+1]{let k=sparse.column[entry] as usize;if(owner[i]<2&&!allowed[owner[i]][k])||(owner[k]<2&&!allowed[owner[k]][i]){return Err(StepError::SingularJacobian);}}}
'''
def solver():
    s=(ROOT/'tools/dynamic_schur_refined_sparse_solver.rs').read_text(encoding='utf8');start=s.index('  for block in 0..2{let mut allowed=');end=s.index('  let a=',start);s=s[:start]+GUARD+s[end:]
    for old in ['for col in 0..row{v-=self.a[row][col]*x[col];}','for col in row+1..N{v-=self.a[row][col]*x[col];}']:
        require(old in s,'original substitution');head=old.split('{')[0];s=s.replace(old,head+'{let a=self.a[row][col];if a==0.&&v!=0.&&v.is_finite()&&x[col].is_finite(){continue;}v-=a*x[col];}',1)
    require('#[inline(always)]' not in s,'no rejected constructor hint');return s.replace('let mut x=[0.;N]','let mut x=[0_f64;N]',1)
def kernel():return (ROOT/'tools/joint_schur_refined_sparse_kernel.rs').read_text(encoding='utf8').replace('dynamic_schur_refined_sparse_solver.rs','dynamic_schur_support_solver.rs')
def caller():return (ROOT/'tools/joint_schur_refined_sparse_runner.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_support_kernel.rs')
def main():
    r=json.loads((ROOT/'evidence/voice_schur_refined_inlinebench01.json').read_text(encoding='utf8'));require(r['passed'] and not r['utility_passed'],'rejected inline utility');write('evidence/voice_schur_cost_support_decision01.json',dict(passed=True,rejected_inline_bench_sha256=sha(ROOT/'evidence/voice_schur_refined_inlinebench01.json'),rejected_source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_schur_inline.py','tools/dynamic_schur_inline_solver.rs','tools/joint_schur_inline_kernel.rs','tools/schur_inline_bench.rs']},numerical_gates_changed=False))
    for n,s in [('tools/dynamic_schur_support_solver.rs',solver()),('tools/joint_schur_support_kernel.rs',kernel()),('tools/joint_schur_support_runner.rs',caller()),('tools/schur_support_bench.rs',(ROOT/'tools/schur_refined_sparse_bench.rs').read_text(encoding='utf8').replace('joint_schur_refined_sparse_kernel.rs','joint_schur_support_kernel.rs'))]:
        p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);inp=json.loads((ROOT/'evidence/voice_schur_cost_inputs01.json').read_text(encoding='utf8'));inp['source_sha256']={n:sha(ROOT/n) for n in ['tools/prepare_schur_support.py','tools/dynamic_schur_support_solver.rs','tools/joint_schur_support_kernel.rs','tools/joint_schur_support_runner.rs','tools/schur_support_bench.rs','docs/SCHUR_SOPORTE_FRONTERAS.md']};write('evidence/voice_schur_cost_inputs02.json',inp)
if __name__=='__main__':main()
