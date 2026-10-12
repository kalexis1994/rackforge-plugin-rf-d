"""Preserve the failing source and add a storage-free contact predictor only."""
import base64,hashlib,json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
PREDICTOR=''' if p.short && old.high[218]+old.low[218]>1. {
  let v=|k|old.high[k]+old.low[k];
  for(k,target)in [(217,7.),(218,0.5),(219,0.45),(214,3.1),(210,3.7_f64.min(v(205)+0.6)),(211,v(205)),(216,7.),(224,p.reset_v+0.4)] {seed[k]=target-old.high[k]-old.low[k];}
 } else if !p.short && old.high[218]+old.low[218]<1. {
  let v=|k|old.high[k]+old.low[k];
  for(k,target)in [(217,0.03),(218,6.),(219,0.7),(214,0.7),(210,1.3),(211,0.7),(216,if p.final_decay {0.03} else {v(205)-0.6}),(224,p.reset_v+0.4)] {seed[k]=target-old.high[k]-old.low[k];}
 }
'''
def main():
 bad=json.loads((ROOT/'evidence/voice_trigger_charge_native01.json').read_text(encoding='utf8'));diag=json.loads((ROOT/'evidence/voice_trigger_charge_diagnostic01.json').read_text(encoding='utf8'));require(not bad['passed'] and diag['passed'] and bad['profiles'][0]['stderr']==bad['replays'][0]['stderr']=='FAILURE,step,phase=2,k=0:IterationBudget\n','same rejection');raw={n:(ROOT/n).read_bytes() for n in bad['source_sha256']}
 for n,b in raw.items():require(hashlib.sha256(b).hexdigest()==bad['source_sha256'][n],'failed source immutable')
 write('evidence/voice_trigger_charge_failure_bytes01.json',dict(source_sha256=bad['source_sha256'],source_base64={n:base64.b64encode(b).decode() for n,b in raw.items() if n in bad['failed_source_text']},predictor_source=PREDICTOR))
 p=ROOT/'tools/prepare_trigger_charge.py';s=p.read_text(encoding='utf8');s=s.replace('from joint_cycles_analysis import require','from joint_cycles_analysis import require\nfrom repair_trigger_seed import PREDICTOR');a=' module=\'#[path="trigger_charge_driver.rs"]';require(s.count(a)==1,'predictor insertion');s=s.replace(a,' s=s.replace(" let mut delta=[State::from_nodes(seed);2];",PREDICTOR+" let mut delta=[State::from_nodes(seed);2];")\n'+a);p.write_text(s,encoding='utf8',newline='\n')
 from prepare_trigger_charge import kernel
 (ROOT/'tools/joint_trigger_kernel.rs').write_text(kernel(),encoding='utf8',newline='\n');inp=json.loads((ROOT/'evidence/voice_trigger_charge_inputs01.json').read_text(encoding='utf8'));inp['predictor_substitution']=PREDICTOR;inp['source_sha256']={n:sha(ROOT/n) for n in [*inp['source_sha256'],'tools/repair_trigger_seed.py','docs/VOZ_GATILLO_SEMILLA_PROTOCOLO.md']};write('evidence/voice_trigger_charge_inputs02.json',inp);print('TRIGGER_SEED_REPAIR')
if __name__=='__main__':main()
