"""Prepare isolated public family and a late-release paired caller after lab utility."""
import json,struct
from prepare_vco1_portable import ROOT,sha,write
from prepare_assembly_voice import public_voice
from prepare_voice_paired import paired as original_paired
from prepare_release_voice import once
from joint_cycles_analysis import require
START=35883319296;SPAN=2097152000;CUT=419430400
PUBLIC=['crates/rf-d-circuit/src/assembly_decay_voice.rs','crates/rf-d-circuit/src/assembly_decay_engine.rs']
PAIRED='tools/assembly_voice_paired.rs'
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in [*PUBLIC,PAIRED])).encode()
EXPORT=b'\npub mod assembly_decay_voice;\npub mod assembly_decay_engine;\n'
def sources():return {PUBLIC[0]:public_voice(),PUBLIC[1]:(ROOT/'crates/rf-d-circuit/src/block_decay_engine.rs').read_text(encoding='utf8').replace('crate::block_decay_voice','crate::assembly_decay_voice')}
def paired():
 s=original_paired(True);s=once(s,'use rf_d_circuit::{decay_voice as joint,decay_engine as temporal};','use rf_d_circuit::{block_decay_voice as joint,block_decay_engine as temporal};');s=once(s,'const START:u64=14911799296;const REL:[u64;2]=[0,8388608000];','const START:u64=35883319296;const REL:[u64;2]=[0,2097152000];');s=once(s,'use rf_d_circuit::{block_decay_voice as candidate,block_decay_engine as alt};','use rf_d_circuit::{assembly_decay_voice as candidate,assembly_decay_engine as alt};');return s
def main():
 lab=json.loads((ROOT/'evidence/voice_assembly_lab03.json').read_text(encoding='utf8'));require(lab['passed'] and lab['cost_utility_passed'],'laboratory numeric and cost admission');qa=json.loads((ROOT/'evidence/voice_zero_tests01.json').read_text(encoding='utf8'));names={**sources(),PAIRED:paired()}
 for n,s in names.items():require(not (ROOT/n).exists(),'exclusive public family');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);p=ROOT/'crates/rf-d-circuit/src/lib.rs';p.write_bytes(p.read_bytes()+EXPORT);work=ROOT/'references-local/voice-assembly-seeds01';work.mkdir();seeds=[];private={}
 for maximum in [1048576,524288]:
  n=f'references-local/extended-release01/{maximum}/checkpoints.bin';require(sha(ROOT/n)==qa['private_input_sha256'][n],'own checkpoints unchanged');raw=(ROOT/n).read_bytes();matches=[raw[k:k+3728] for k in range(0,len(raw),3728) if struct.unpack_from('<Q',raw,k+8)[0]==START];require(len(matches)==1,'unique own seed clock');p=work/f'{maximum}.ckp';p.write_bytes(matches[0]);seeds.append(dict(maximum_half_ticks=maximum,path=p.relative_to(ROOT).as_posix(),sha256=sha(p)));private[n]=sha(ROOT/n)
 write('evidence/voice_assembly_promotion01.json',dict(passed=True,prepared_only=True,public_admission_pending=True,source_sha256={n:sha(ROOT/n) for n in ['tools/promote_assembly_voice.py','tools/prepare_assembly_voice.py','tools/prepare_voice_paired.py','evidence/voice_assembly_lab03.json',*names]},private_used_sha256=private,outputs=[dict(path=s['path'],sha256=s['sha256'],bytes=3728) for s in seeds],seeds=seeds,start_ticks=START,end_ticks=START+SPAN,new_circuit_duration_s=0,new_audio=False));print('ASSEMBLY_PUBLIC_PREPARED')
if __name__=='__main__':main()
