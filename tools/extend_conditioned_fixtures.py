"""Add the original OFF starting history for within-window temporal API tests."""
import base64,json,struct
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    n='crates/rf-d-circuit/tests/support/conditioned_seed.rs';p=ROOT/n;before=p.read_bytes();old=sha(p);name='evidence/voice_schur_chain_trajectory01.json';r=json.loads((ROOT/name).read_text(encoding='utf8'));q=next(x for x in r['profiles'] if not x['final_decay'] and x['maximum_half_ticks']==1048576)
    private='references-local/radau-inplace01/0-1048576/checkpoints.bin';raw=(ROOT/private).read_bytes()[:3720];require(raw[56:]==struct.pack('<458d',*q['grids'][0]['values']),'additional history already public by bits');ticks=struct.unpack_from('<Q',raw,8)[0];maximum,limit,next_full=struct.unpack_from('<3I',raw,16);bits=struct.unpack_from('<458Q',raw,56);require(b'D_STATE' not in before,'exclusive fixture extension')
    extra=('pub const D_STATE:[u64;458]=['+','.join(map(str,bits))+'];\n'+f'pub const D_METADATA:(u64,u32,u32,u32,f64,bool,bool)=({ticks},{maximum},{limit},{next_full},0.0,false,false);\n').encode();p.write_bytes(before+extra)
    write('evidence/voice_conditioned_portable_fixture_extension01.json',dict(passed=True,source_sha256={'tools/extend_conditioned_fixtures.py':sha(ROOT/'tools/extend_conditioned_fixtures.py'),name:sha(ROOT/name),n:sha(p)},previous_fixture_sha256=old,previous_fixture_base64=base64.b64encode(before).decode(),prefix_preserved=True,private_used_sha256={private:sha(ROOT/private)},additional_public_history='OFF original start8.438ms',new_temporal_duration=False))
    test=ROOT/'crates/rf-d-circuit/tests/conditioned_portable.rs';s=test.read_text(encoding='utf8');s=s.replace('fixture::B_STATE,fixture::B_METADATA','fixture::D_STATE,fixture::D_METADATA');test.write_text(s,encoding='utf8',newline='\n');print('PUBLIC_FIXTURE_INITIAL_OFF')
if __name__=='__main__':main()
