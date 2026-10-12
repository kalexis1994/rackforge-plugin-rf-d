"""Preserve failed source bytes; add only the declared CR10 Newton seed."""
import base64,json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
PREDICTOR=''' let mut seed=[0.;N];
 if p.keyboard-(old.high[222]+old.low[222])>0.5{seed[222]=p.keyboard-0.5-old.high[222]-old.low[222];}
'''
def main():
 bad=json.loads((ROOT/'evidence/voice_latch_charge_native01.json').read_text(encoding='utf8'));require(not bad['passed'] and bad['profiles'][0]['stderr']==bad['replays'][0]['stderr']=='FAILURE,step,phase=1,k=0:ExponentialDomain\n','same domain rejection');raw={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in bad['failed_source_text']};write('evidence/voice_latch_charge_failure_bytes01.json',dict(source_base64=raw));p=ROOT/'tools/joint_latch_kernel.rs';s=p.read_text(encoding='utf8');require(s.count(' let seed=[0.;N];\n')==1,'only seed');p.write_text(s.replace(' let seed=[0.;N];\n',PREDICTOR),encoding='utf8',newline='\n');p=ROOT/'tools/joint_latch_runner.rs';s=p.read_text(encoding='utf8');p.write_text(s,encoding='utf8',newline='\n')
 inp=json.loads((ROOT/'evidence/voice_latch_charge_inputs01.json').read_text(encoding='utf8'));inp['source_sha256']={n:sha(ROOT/n) for n in inp['source_sha256']};inp['source_sha256'].update({n:sha(ROOT/n) for n in ['tools/repair_latch_seed.py','docs/VOZ_BIESTABLE_SEMILLA_PROTOCOLO.md']});inp['predictor_substitution']=PREDICTOR;inp['failed_receipt_sha256']=sha(ROOT/'evidence/voice_latch_charge_native01.json');write('evidence/voice_latch_charge_inputs02.json',inp)
if __name__=='__main__':main()
