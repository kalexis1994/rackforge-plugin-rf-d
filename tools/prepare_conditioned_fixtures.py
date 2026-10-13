"""Freeze existing published synthetic histories for public API tests."""
import json,struct
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/crates/rf-d-circuit/tests/conditioned_portable.rs text eol=lf\n/crates/rf-d-circuit/tests/support/conditioned_seed.rs text eol=lf\n'

def main():
    name='evidence/voice_schur_chain_trajectory01.json';old=json.loads((ROOT/name).read_text(encoding='utf8'));require(old['passed'],'admitted published states');records=[];text='//! Frozen synthetic Model D laboratory histories already published in the oracle.\n'
    for tag,on,suffix,public in [('A',True,'checkpoints.bin','initial'),('B',False,'final.ckp','final'),('TRIGGER',True,'phase1-start.ckp','phase0')]:
        n=f'references-local/radau-inplace01/{int(on)}-1048576/{suffix}';raw=(ROOT/n).read_bytes()[:3720];require(len(raw)==3720 and raw[:8]==b'RFCYCT01','typed existing checkpoint');ticks=struct.unpack_from('<Q',raw,8)[0];maximum,limit,next_full,phase,model,flags=struct.unpack_from('<6I',raw,16);key=struct.unpack_from('<d',raw,40)[0];bits=struct.unpack_from('<458Q',raw,56)
        p=next(p for p in old['profiles'] if p['final_decay']==on and p['maximum_half_ticks']==1048576)
        v=p['grids'][0 if public=='initial' else -1]['values'] if public!='phase0' else p['phases'][0]['final_high_low'];require(struct.pack('<458d',*v)==raw[56:],'fixture states already published by bits')
        text+=f'pub const {tag}_STATE:[u64;458]=['+','.join(map(str,bits))+'];\n'
        text+=f'pub const {tag}_METADATA:(u64,u32,u32,u32,f64,bool,bool)=({ticks},{maximum},{limit},{next_full},{key!r},{str(on).lower()},{str(bool(flags&2)).lower()});\n'
        records.append(dict(name=tag,original_path=n,original_sha256=sha(ROOT/n),published_temporal_sha256=sha(ROOT/name),state_bits_already_public=True,phase=phase))
    n='crates/rf-d-circuit/tests/support/conditioned_seed.rs';p=ROOT/n;require(not p.exists(),'exclusive fixture');p.write_text(text,encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
    write('evidence/voice_conditioned_portable_fixture01.json',dict(passed=True,source_sha256={'tools/prepare_conditioned_fixtures.py':sha(ROOT/'tools/prepare_conditioned_fixtures.py'),name:sha(ROOT/name),n:sha(ROOT/n)},private_used_sha256={q['original_path']:q['original_sha256'] for q in records},records=records,proprietary_capture_or_audio=False,synthetic_model_histories_only=True))
    print('PUBLIC_SYNTHETIC_FIXTURES',len(records))
if __name__=='__main__':main()
