"""Run the same every-Accepted caller against the second measured public library."""
import json,sys
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
import run_voice_paired as harness

def main():
 r=json.loads((ROOT/'evidence/voice_block_library02.json').read_text(encoding='utf8'));require(r['passed'] and r['public_bank_exact'] and r['cost_utility_passed'],'public identity and contemporaneous cost')
 source=(ROOT/'tools/run_voice_paired.py').read_text(encoding='utf8').replace('voice-block-library01','voice-block-library02').replace('names=[src,','names=[\'tools/run_voice_public.py\',\'evidence/voice_block_library02.json\',src,')
 namespace=dict(harness.__dict__,__name__='public-accepted-identity-harness');exec(compile(source,'<public-library-only-selector>','exec'),namespace);sys.argv=[sys.argv[0],'--public'];namespace['main']()
if __name__=='__main__':main()
