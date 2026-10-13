"""Use the unchanged bench gates for the Jacobian quadrant traversal candidate."""
from prepare_vco1_portable import ROOT
import run_voice_pivot_bench as harness
from prepare_voice_block import block_kernel,block_bench
from joint_cycles_analysis import require

def main():
 require((ROOT/'tools/voice_block_kernel.rs').read_text(encoding='utf8')==block_kernel() and (ROOT/'tools/voice_block_bench.rs').read_text(encoding='utf8')==block_bench(),'declared block traversal')
 # Run a renamed instance of the frozen profiling/utility harness. The gates,
 # seed, alternation and timers are byte-identical; add the new measured sources.
 source=(ROOT/'tools/run_voice_pivot_bench.py').read_text(encoding='utf8').replace('voice-pivot-bench','voice-block-bench').replace('voice_pivot_bench','voice_block_bench').replace('PIVOT_BENCH_PASSED','BLOCK_BENCH_PASSED')
 source=source.replace("*profile_sources()];before=", "*profile_sources(),'tools/voice_block_kernel.rs','tools/prepare_voice_block.py','docs/VOZ_COSTO_BLOQUES_PROTOCOLO.md','evidence/voice_pivot_bench01.json'];before=")
 source=source.replace("'ERRORS_PASSED,6' in lines", "'ERRORS_PASSED,6' in lines and 'STAMPS_PASSED,78,211138' in lines")
 source=source.replace('error_policy_checks=6,phases=', 'error_policy_checks=6,complete_stamp_bit_fields=78*211138,phases=')
 namespace=dict(harness.__dict__,__name__='voice_block_harness');exec(compile(source,'<unchanged-utility-gates-block-harness>','exec'),namespace);namespace['main']()
if __name__=='__main__':main()
