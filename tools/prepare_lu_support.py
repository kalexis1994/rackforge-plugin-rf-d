"""Generate a dynamically rebuilt exact-zero pivot support, keeping the old solver."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from prepare_newton_reuse import instrument as timer_instrument
ATTR=b'\n/tools/joint_lu_support_kernel.rs text eol=lf\n/tools/joint_lu_support_runner.rs text eol=lf\n/tools/lu_support_bench.rs text eol=lf\n'
def support_solver():
 s=(ROOT/'tools/joint_newton_reuse_kernel.rs').read_text(encoding='utf8');s=s[s.index('fn solve_linear_internal'):];s=s.replace('fn solve_linear_internal<const M: usize, const SKIP_ZERO: bool>','pub fn solve_linear_support<const M: usize>').replace('if SKIP_ZERO &&','if')
 s=s.replace('        let diagonal = j[col][col];','        let diagonal = j[col][col];\n        let mut support=[0_usize;M];let mut used=0;\n        for k in (col+1)..M {if j[col][k]!=0. {support[used]=k;used+=1;}}')
 s=s.replace('            for k in (col + 1)..M {','            for &k in &support[..used] {')
 return s
def kernel():
 s=(ROOT/'tools/joint_newton_reuse_kernel.rs').read_text(encoding='utf8');a=s.index('pub fn step(');b=s.index('\nmod fine',a);return s[:a]+s[a:b].replace('solve_linear_sparse(','solve_linear_support(')+s[b:]+'\n'+support_solver()
def caller():return (ROOT/'tools/joint_newton_reuse_runner.rs').read_text(encoding='utf8').replace('path="joint_newton_reuse_kernel.rs"','path="joint_lu_support_kernel.rs"')
def instrument(s):
 # Preserve the same timers; route the wrapper to the support solver when present.
 if 'pub fn solve_linear_support' in s:
  a=s.index('pub fn step(');b=s.index('\nmod fine',a);s=s[:a]+s[a:b].replace('solve_linear_support(','solve_linear_sparse(')+s[b:];s=timer_instrument(s);s=s.replace('let q=solve_linear_sparse(j,r);','let q=solve_linear_support(j,r);');return s
 return timer_instrument(s)
def main():
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='444a96278b542e5220232765cedf45e581774c34','base');old=json.loads((ROOT/'evidence/newton_reuse_tests01.json').read_text(encoding='utf8'));require(old['passed'],'QA');write('evidence/voice_lu_support_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/newton_reuse_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}));work=ROOT/'references-local/lu-support-inputs01';require(not work.exists(),'exclusive input');work.mkdir()
 for n,s in [('tools/joint_lu_support_kernel.rs',kernel()),('tools/joint_lu_support_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 for name,s in [('reference_profile.rs',instrument((ROOT/'tools/joint_newton_reuse_kernel.rs').read_text(encoding='utf8'))),('reuse_profile.rs',instrument(kernel()))]:
  s=s.replace('path="latch_charge_driver.rs"','path="'+(ROOT/'tools/latch_charge_driver.rs').as_posix()+'"').replace('path="contour_closed_driver.rs"','path="'+(ROOT/'tools/contour_closed_driver.rs').as_posix()+'"');(work/name).write_text(s,encoding='utf8',newline='\n')
 bench=(ROOT/'tools/newton_reuse_bench.rs').read_text(encoding='utf8').replace('newton-reuse-inputs01','lu-support-inputs01');(ROOT/'tools/lu_support_bench.rs').write_text(bench,encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);packet='references-local/newton-reuse-inputs01/pairs.bin';require(sha(ROOT/packet)==old['private_input_sha256'][packet],'original pairs');write('evidence/voice_lu_support_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_lu_support.py','tools/joint_lu_support_kernel.rs','tools/joint_lu_support_runner.rs','tools/lu_support_bench.rs','docs/LU_SOPORTE_PROTOCOLO.md']},private_used_sha256={packet:sha(ROOT/packet),**{p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()}},pair_packet=packet,selected_pairs=84,seeds=json.loads((ROOT/'evidence/newton_reuse_inputs01.json').read_text(encoding='utf8'))['seeds']));print('LU_SUPPORT_INPUTS',84)
if __name__=='__main__':main()
