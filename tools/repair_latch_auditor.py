"""Restore the already-native dead-ended FAST_K row in the oracle adapter."""
import json
from decimal import localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
OLD="core,_,y=follower_problem(0.,0.,r61,mask,sources);n=network(on,short)"
NEW=OLD+"\n if on:n.resistors.append(('LHC_FAST_DECAY','FAST_DIODE_K','RESET_DRIVER',1500.))"
def main():
 import check_latch_charge as c
 bad=json.loads((ROOT/'evidence/voice_latch_charge_reference01.json').read_text(encoding='utf8'));require(not bad['passed'] and bad['failure'].splitlines()[-1]==bad['replay'].splitlines()[-1]=='numpy.linalg.LinAlgError: Singular matrix','same empty row');native=json.loads((ROOT/'evidence/voice_latch_charge_native03.json').read_text(encoding='utf8'));data={o['path']:o['sha256'] for o in native['outputs']};lines=(ROOT/'references-local/latch-charge03/1-16384/selected.txt').read_text().splitlines();i=next(k for k,l in enumerate(lines) if l.startswith('JOINT_ROOT,'))
 with localcontext() as ctx:
  ctx.prec=100;x=c.state(lines[i+4])[0];high=np.array([float(x[c.ci(k)]) for k in range(97)]);dc,j,_=c.problem(0.,True,False,200.,0,(0.,.2,-.3,.1,.4));zeros=[k for k in range(97) if max(abs(v) for v in j(high)[k])==0]
 require(zeros==[66,84] and dc(high)[84]==0,'only FAST_K empty row');p=ROOT/'tools/check_latch_charge.py';s=p.read_text(encoding='utf8');require(s==bad['failed_source_text'] and s.count(OLD)==1,'exact failed source');p.write_text(s.replace(OLD,NEW),encoding='utf8',newline='\n');require(all(sha(ROOT/n)==h for n,h in data.items()),'same native data');write('evidence/voice_latch_charge_auditor_adapter01.json',dict(passed=True,failed_receipt_sha256=sha(ROOT/'evidence/voice_latch_charge_reference01.json'),native_receipt_sha256=sha(ROOT/'evidence/voice_latch_charge_native03.json'),private_input_sha256=data,empty_chain_row=84,empty_joint_row=216,substitution_old=OLD,substitution_new=NEW,native_reexecuted=False,numerical_gates_changed=False))
if __name__=='__main__':main()
