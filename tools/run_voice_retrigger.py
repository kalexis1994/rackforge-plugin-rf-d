"""Run the frozen continuation harness against explicit loaded source events."""
from prepare_vco1_portable import ROOT
def main():
 s=(ROOT/'tools/run_extended_release.py').read_text(encoding='utf8')
 s=s.replace('from prepare_extended_release import EXAMPLE','from prepare_voice_retrigger import EXAMPLE').replace('extended-release{attempt:02d}','voice-retrigger{attempt:02d}').replace('voice_extended_native','voice_retrigger_native').replace('voice_extended_inputs01','voice_retrigger_inputs01').replace('voice_block_tests01','voice_tail_tests01').replace('voice_block_library02','voice_assembly_public01').replace('references-local/voice-block-library02/librf_d_circuit.rlib','references-local/voice-assembly-public01/librf_d_circuit.rlib').replace('tools/run_extended_release.py','tools/run_voice_retrigger.py').replace('128*1024**2','96*1024**2').replace('new_source_event=False','new_source_event=True,event_compared_accepted=16')
 s=s.replace("names=set(inp['source_sha256'])|", "names={'tools/run_extended_release.py'}|set(inp['source_sha256'])|")
 scope={'__name__':'voice_retrigger_harness'};exec(compile(s,'<frozen-retrigger-harness>','exec'),scope);scope['main']()
if __name__=='__main__':main()
