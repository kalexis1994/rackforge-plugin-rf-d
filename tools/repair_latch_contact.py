"""Reuse accepted storage-free trigger predictor without choosing latch state."""
import base64,json
from prepare_vco1_portable import ROOT,sha,write
from repair_trigger_seed import PREDICTOR as OLD
from joint_cycles_analysis import require
PREDICTOR=OLD.replace('p.reset_v+0.4','v(227)+0.4')
def main():
 bad=json.loads((ROOT/'evidence/voice_latch_charge_native02.json').read_text(encoding='utf8'));require(not bad['passed'] and bad['profiles'][0]['stderr']==bad['replays'][0]['stderr']=='FAILURE,step,phase=2,k=0:IterationBudget\n','same contact rejection');raw={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in bad['failed_source_text']};write('evidence/voice_latch_charge_failure_bytes02.json',dict(source_base64=raw));p=ROOT/'tools/joint_latch_kernel.rs';s=p.read_text(encoding='utf8');require(s.count(' let mut delta=[State::from_nodes(seed);2];')==1,'only seed');p.write_text(s.replace(' let mut delta=[State::from_nodes(seed);2];',PREDICTOR+' let mut delta=[State::from_nodes(seed);2];'),encoding='utf8',newline='\n')
 inp=json.loads((ROOT/'evidence/voice_latch_charge_inputs02.json').read_text(encoding='utf8'));inp['source_sha256']={n:sha(ROOT/n) for n in inp['source_sha256']};inp['source_sha256'].update({n:sha(ROOT/n) for n in ['tools/repair_latch_contact.py','docs/VOZ_BIESTABLE_CONTACTO_PROTOCOLO.md']});inp['contact_predictor_substitution']=PREDICTOR;inp['contact_failed_receipt_sha256']=sha(ROOT/'evidence/voice_latch_charge_native02.json');write('evidence/voice_latch_charge_inputs03.json',inp)
if __name__=='__main__':main()
