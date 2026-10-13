"""Preserve indexed-support experiment; try contiguous extent with disjoint rows."""
import json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from prepare_newton_reuse import instrument as timer_instrument
ATTR=b'/tools/joint_lu_extent_kernel.rs text eol=lf\n/tools/joint_lu_extent_runner.rs text eol=lf\n/tools/lu_extent_bench.rs text eol=lf\n'
SOLVER='''pub fn solve_linear_extent<const M:usize>(mut j:[[f64;M];M],mut rhs:[f64;M])->Result<[f64;M],StepError>{
 let mut scale=[0.;M];for i in 0..M{scale[i]=max_abs(&j[i]);if scale[i]==0.{return Err(StepError::SingularJacobian);}}
 for col in 0..M{
  let mut pivot=col;let mut best=0.;for row in col..M{if j[row][col]==0.{continue;}let score=j[row][col].abs()/scale[row];if score>best{best=score;pivot=row;}}
  if best<1e-12{return Err(StepError::SingularJacobian);}j.swap(col,pivot);rhs.swap(col,pivot);scale.swap(col,pivot);
  let diagonal=j[col][col];let end=j[col].iter().rposition(|v|*v!=0.).unwrap()+1;
  let (prefix,suffix)=j.split_at_mut(col+1);let pivot_row=&prefix[col];
  for(offset,current)in suffix.iter_mut().enumerate(){let row=col+1+offset;if current[col]==0.{continue;}let factor=current[col]/diagonal;current[col]=0.;
   for(target,coefficient)in current[col+1..end].iter_mut().zip(&pivot_row[col+1..end]){*target-=factor*coefficient;}
   rhs[row]-=factor*rhs[col];
  }
 }
 let mut out=[0.;M];for row in(0..M).rev(){let mut value=rhs[row];for k in row+1..M{value-=j[row][k]*out[k];}out[row]=value/j[row][row];}
 if out.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(out)
}
'''
def kernel():
 s=(ROOT/'tools/joint_newton_reuse_kernel.rs').read_text(encoding='utf8');a=s.index('pub fn step(');b=s.index('\nmod fine',a);return s[:a]+s[a:b].replace('solve_linear_sparse(','solve_linear_extent(')+s[b:]+'\n'+SOLVER
def caller():return (ROOT/'tools/joint_newton_reuse_runner.rs').read_text(encoding='utf8').replace('path="joint_newton_reuse_kernel.rs"','path="joint_lu_extent_kernel.rs"')
def instrument(s):
 if 'pub fn solve_linear_extent' in s:
  a=s.index('pub fn step(');b=s.index('\nmod fine',a);s=s[:a]+s[a:b].replace('solve_linear_extent(','solve_linear_sparse(')+s[b:];s=timer_instrument(s);return s.replace('let q=solve_linear_sparse(j,r);','let q=solve_linear_extent(j,r);')
 return timer_instrument(s)
def main():
 prior='evidence/voice_lu_support_bench_native01.json';old=json.loads((ROOT/prior).read_text(encoding='utf8'));require(old['passed'],'indexed hypothesis recorded');write('evidence/voice_lu_extent_decision01.json',dict(passed=True,prior_bench_sha256=sha(ROOT/prior),first_experiment_source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_lu_support.py','tools/joint_lu_support_kernel.rs','tools/joint_lu_support_runner.rs','tools/lu_support_bench.rs','docs/LU_SOPORTE_PROTOCOLO.md']},reason='Indexed-support total wall improvement is marginal and variable; test contiguous extent',numerical_gates_changed=False));work=ROOT/'references-local/lu-extent-inputs01';require(not work.exists(),'exclusive second input');work.mkdir()
 for n,s in [('tools/joint_lu_extent_kernel.rs',kernel()),('tools/joint_lu_extent_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 for name,s in [('reference_profile.rs',instrument((ROOT/'tools/joint_newton_reuse_kernel.rs').read_text(encoding='utf8'))),('reuse_profile.rs',instrument(kernel()))]:
  s=s.replace('path="latch_charge_driver.rs"','path="'+(ROOT/'tools/latch_charge_driver.rs').as_posix()+'"').replace('path="contour_closed_driver.rs"','path="'+(ROOT/'tools/contour_closed_driver.rs').as_posix()+'"');(work/name).write_text(s,encoding='utf8',newline='\n')
 (ROOT/'tools/lu_extent_bench.rs').write_text((ROOT/'tools/newton_reuse_bench.rs').read_text(encoding='utf8').replace('newton-reuse-inputs01','lu-extent-inputs01'),encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);inp=json.loads((ROOT/'evidence/voice_lu_support_inputs01.json').read_text(encoding='utf8'));packet=inp['pair_packet'];write('evidence/voice_lu_extent_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_lu_extent.py','tools/joint_lu_extent_kernel.rs','tools/joint_lu_extent_runner.rs','tools/lu_extent_bench.rs','docs/LU_EXTENSION_PROTOCOLO.md']},private_used_sha256={packet:sha(ROOT/packet),**{p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()}},pair_packet=packet,selected_pairs=84,seeds=inp['seeds']));print('LU_EXTENT_INPUTS',84)
if __name__=='__main__':main()
