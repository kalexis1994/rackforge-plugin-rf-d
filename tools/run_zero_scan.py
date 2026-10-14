"""Use the same frozen bank and utility gates for isolated CSR bit traversal."""
from prepare_vco1_portable import ROOT
def main():
 source=(ROOT/'tools/run_zero_voice.py').read_text(encoding='utf8').replace('from prepare_zero_voice import RUST','from prepare_zero_scan import RUST').replace('voice-zero-bench','voice-zero-scan').replace('voice_zero_bench','voice_zero_scan').replace('tools/run_zero_voice.py','tools/run_zero_scan.py').replace('tools/prepare_zero_voice.py','tools/prepare_zero_scan.py').replace('docs/VOZ_CEROS_PROTOCOLO.md','docs/VOZ_CEROS_SCAN_PROTOCOLO.md').replace('ZERO_BENCH_PASSED','ZERO_SCAN_BENCH_PASSED')
 source=source.replace("names=[*RUST,","names=['tools/run_zero_voice.py','tools/prepare_zero_voice.py','evidence/voice_zero_bench01.json','evidence/voice_zero_scan_inputs01.json',*RUST,")
 namespace={'__name__':'zero_scan_harness'};exec(compile(source,'<frozen-utility-scan-adapter>','exec'),namespace);namespace['main']()
if __name__=='__main__':main()
