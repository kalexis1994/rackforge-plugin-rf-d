"""Use the admitted continuation harness with the frozen assembly library and larger finite span."""
from prepare_vco1_portable import ROOT
def main():
 s=(ROOT/'tools/run_extended_release.py').read_text(encoding='utf8');s=s.replace('from prepare_extended_release import EXAMPLE','from prepare_long_tail import EXAMPLE').replace('extended-release{attempt:02d}','long-tail{attempt:02d}').replace('voice_extended_native','voice_tail_native').replace('voice_extended_inputs01','voice_tail_inputs01').replace('voice_block_tests01','voice_assembly_tests01').replace('voice_block_library02','voice_assembly_public01').replace('references-local/voice-block-library02/librf_d_circuit.rlib','references-local/voice-assembly-public01/librf_d_circuit.rlib').replace('tools/run_extended_release.py','tools/run_long_tail.py').replace('128*1024**2','192*1024**2')
 s=s.replace("names=set(inp['source_sha256'])|","names={'tools/run_extended_release.py'}|set(inp['source_sha256'])|")
 scope={'__name__':'long_tail_harness'};exec(compile(s,'<frozen-continuation-harness-long-tail>','exec'),scope);scope['main']()
if __name__=='__main__':main()
