"""Replace repeated partition searches with fixed-size index tables only."""
import json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'/tools/dynamic_schur_fast_solver.rs text eol=lf\n/tools/joint_dynamic_schur_fast_kernel.rs text eol=lf\n/tools/dynamic_schur_fast_bench.rs text eol=lf\n/tools/joint_dynamic_schur_fast_runner.rs text eol=lf\n'
def solver():
 s=(ROOT/'tools/dynamic_schur_solver.rs').read_text(encoding='utf8');s=s.replace(' let mut s=std::array::from_fn', ' let mut position=[usize::MAX;458];for(i,&k)in EXTERNAL.iter().enumerate(){position[k]=i;}\n let mut s=std::array::from_fn',1)
 s=s.replace('  let nodes=INNER[block];let ports=PORTS[block];','  let nodes=INNER[block];let ports=PORTS[block];let mut allowed=[false;458];for &k in nodes.iter().chain(ports.iter()){if k!=usize::MAX{allowed[k]=true;}}')
 s=s.replace('!nodes.contains(&k)&&!ports.contains(&k)','!allowed[k]').replace('EXTERNAL.iter().position(|k|*k==p).ok_or(StepError::SingularJacobian)?','position[p]').replace('EXTERNAL.iter().position(|v|*v==q).ok_or(StepError::SingularJacobian)?','position[q]');return s
def kernel():return (ROOT/'tools/joint_dynamic_schur_kernel.rs').read_text(encoding='utf8').replace('path="dynamic_schur_solver.rs"','path="dynamic_schur_fast_solver.rs"')
def caller():return (ROOT/'tools/joint_dynamic_schur_runner.rs').read_text(encoding='utf8').replace('path="joint_dynamic_schur_kernel.rs"','path="joint_dynamic_schur_fast_kernel.rs"')
def main():
 old='evidence/voice_dynamic_schur_bench_native02.json';r=json.loads((ROOT/old).read_text(encoding='utf8'));require(r['passed'],'first physical candidate gate');write('evidence/voice_dynamic_schur_index_decision01.json',dict(passed=True,first_bench_sha256=sha(ROOT/old),first_source_sha256={n:sha(ROOT/n) for n in ['tools/dynamic_schur_solver.rs','tools/joint_dynamic_schur_kernel.rs','tools/prepare_dynamic_schur.py']},only_indexing_changed=True,numerical_gates_changed=False))
 for n,s in [('tools/dynamic_schur_fast_solver.rs',solver()),('tools/joint_dynamic_schur_fast_kernel.rs',kernel()),('tools/joint_dynamic_schur_fast_runner.rs',caller()),('tools/dynamic_schur_fast_bench.rs',(ROOT/'tools/dynamic_schur_bench.rs').read_text(encoding='utf8').replace('joint_dynamic_schur_kernel.rs','joint_dynamic_schur_fast_kernel.rs'))]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);inp=json.loads((ROOT/'evidence/voice_dynamic_schur_inputs02.json').read_text(encoding='utf8'));inp['source_sha256']={**inp['source_sha256'],**{n:sha(ROOT/n) for n in ['tools/prepare_dynamic_schur_fast.py','tools/dynamic_schur_fast_solver.rs','tools/joint_dynamic_schur_fast_kernel.rs','tools/joint_dynamic_schur_fast_runner.rs','tools/dynamic_schur_fast_bench.rs','docs/SCHUR_DINAMICO_INDICES.md']}};write('evidence/voice_dynamic_schur_inputs03.json',inp);print('DYNAMIC_SCHUR_INDEX_TABLES')
if __name__=='__main__':main()
