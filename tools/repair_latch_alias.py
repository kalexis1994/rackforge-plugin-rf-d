"""Restore the zero-volt contact alias in the scoped full-graph auditor."""
import json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
OLD="core,_,y=follower_problem(0.,0.,r61,mask,sources);n=network(on,short)"
NEW=OLD+";n.alias['EXTERNAL_S_TRIGGER']='GROUND'"
def main():
 bad=json.loads((ROOT/'evidence/voice_latch_charge_reference03.json').read_text(encoding='utf8'));require(not bad['passed'] and bad['failure'].splitlines()[-1]==bad['replay'].splitlines()[-1]=="KeyError: 'EXTERNAL_S_TRIGGER'",'same alias rejection');p=ROOT/'tools/check_latch_charge.py';s=p.read_text(encoding='utf8');require(s==bad['failed_source_text'] and s.count(OLD)==1,'failed source');data={p['path']:p['sha256'] for p in json.loads((ROOT/'evidence/voice_latch_charge_native03.json').read_text(encoding='utf8'))['outputs']};p.write_text(s.replace(OLD,NEW),encoding='utf8',newline='\n');require(all(sha(ROOT/n)==h for n,h in data.items()),'same native data');write('evidence/voice_latch_charge_alias_adapter01.json',dict(passed=True,failed_receipt_sha256=sha(ROOT/'evidence/voice_latch_charge_reference03.json'),private_input_sha256=data,substitution_old=OLD,substitution_new=NEW,native_reexecuted=False,numerical_gates_changed=False))
if __name__=='__main__':main()
