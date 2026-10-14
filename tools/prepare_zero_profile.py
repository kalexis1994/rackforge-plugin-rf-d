"""Instrument current public arithmetic using the previously declared clock wrappers."""
import inspect
from prepare_vco1_portable import ROOT
from prepare_zero_voice import kernel,probe
from prepare_release_voice import once
from joint_cycles_analysis import require
import prepare_voice_pivot as original
RUST=['tools/zero_current_profile_solver.rs','tools/zero_current_profile_kernel.rs','tools/zero_baseline_solver.rs','tools/zero_baseline_kernel.rs','tools/zero_current_profile_bench.rs']
ATTR=b'\n/tools/zero_current_profile_solver.rs text eol=lf\n/tools/zero_current_profile_kernel.rs text eol=lf\n/tools/zero_current_profile_bench.rs text eol=lf\n'
def sources():
 names=['tools/zero_current_profile_kernel.rs','tools/zero_current_profile_solver.rs',*original.RUST[2:]]
 scope=dict(original.__dict__,RUST=names,SOLVER='crates/rf-d-circuit/src/block_decay_solver.rs',VOICE='crates/rf-d-circuit/src/block_decay_voice.rs',kernel=kernel)
 exec(compile(inspect.getsource(original.profile_sources),'<same-clock-wrappers-current-family>','exec'),scope);sources=scope['profile_sources']();solver=probe(sources[names[1]],False);voice=sources[names[0]].replace('path="voice_pivot_profile_solver.rs"','path="zero_current_profile_solver.rs"')
 s=(ROOT/'tools/zero_voice_bench.rs').read_text(encoding='utf8').replace('path="zero_voice_kernel.rs"','path="zero_current_profile_kernel.rs"');a=s.index('fn main(){');s=s[:a]+'''fn main(){let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),168);let(a,gold)=run_baseline(&cs);let(b,observed)=run_candidate(&cs);assert_eq!(gold,observed);candidate::profile();println!("CURRENT_PROFILE_PASSED,168,{a},{b}");}
'''
 return {RUST[0]:solver,RUST[1]:voice,RUST[-1]:s}
def main():
 for n,s in sources().items():require(not (ROOT/n).exists(),'exclusive profile source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);print('CURRENT_PROFILE_PREPARED')
if __name__=='__main__':main()
