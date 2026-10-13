"""Bind the original graph/FD oracle to the declared electrical resistance."""
from prepare_vco1_portable import ROOT
from prepare_release_voice import once
from joint_cycles_analysis import require

def reference():
 s=(ROOT/'tools/check_latch_charge.py').read_text(encoding='utf8').split('def profile(p,inp):')[0]
 s=once(s,'from latch_charge_reference import network,charges,D','from latch_charge_reference import network as nominal_network,charges,D')
 s=once(s,"CODEC=struct.Struct",'''from prepare_decay_control import DECAY
def network(on,short):
 n=nominal_network(on,short);require(sum(r[0]=='PANEL_R16' for r in n.resistors)==1,'one documentary panel decay branch');n.resistors=[(ref,a,b,DECAY if ref=='PANEL_R16' else ohm) for ref,a,b,ohm in n.resistors];return n
CODEC=struct.Struct''')
 return s

def source():
 s=(ROOT/'tools/check_release_voice.py').read_text(encoding='utf8').split('import numpy as np')[0]
 s=s.replace('from prepare_release_voice import START,BOUNDARIES,KEY,SHORT,CUT,cuts','from prepare_decay_control import START,BOUNDARIES,KEY,SHORT,CUT,cuts,DECAY')
 s=s.replace('from check_latch_charge import state,lift,packed,scoped,currents,ledger,D,checkpoint as latch_checkpoint','from decay_control_reference import state,lift,packed,scoped,currents,ledger,D')
 s=s.replace("'<8sQ6IdQ458d'","'<8sQ6IdQd458d'").replace('3720','3728').replace("b'RFREL001'","b'RFDCY001'")
 s=once(s,'flags,key,reserved,*v=r','flags,key,reserved,decay,*v=r')
 s=once(s,'and reserved==0 and ticks%8','and reserved==0 and decay==DECAY and ticks%8')
 s=once(s,'on=bool(flags&1),values=v','on=bool(flags&1),decay_ohm=decay,values=v')
 s=s.replace('evidence/voice_sustained_reference01.json','evidence/voice_release_reference01.json').replace('29*3728','22*3728').replace('pc==29','pc==22')
 s=once(s,"points[0]['next_full']==4096","points[0]['next_full']==struct.unpack('<8sQ6IdQ458d',(ROOT/f'references-local/release-voice01/{maximum}/final.ckp').read_bytes())[4]")
 s=once(s,"rollbacks=2,input_sha256", "rollbacks=1,input_sha256")
 return s+'\nimport numpy as np\n'+(ROOT/'tools/decay_audit_body.py').read_text(encoding='utf8')

def main():
 for n,s in [('tools/decay_control_reference.py',reference()),('tools/check_decay_control.py',source())]:require(not (ROOT/n).exists(),'exclusive controlled auditor');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 print('DECAY_AUDITOR_PREPARED')
if __name__=='__main__':main()
