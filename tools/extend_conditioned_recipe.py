"""Bind each resolution to its already published own incoming history."""
import base64,json,struct
from prepare_vco1_portable import ROOT,sha,write
from prepare_conditioned_recipe import generated_seed
from joint_cycles_analysis import require
FINE='crates/rf-d-circuit/tests/support/conditioned_recipe_fine_seed.rs'
HIST_ATTR=('\n/'+FINE+' text eol=lf\n').encode()

def fine_seed():
    name='evidence/voice_schur_chain_trajectory01.json'
    r=json.loads((ROOT/name).read_text(encoding='utf8'));extra='// Own 1 us synthetic histories already published in the temporal oracle.\n';records=[]
    for tag,on in [('A_FINE',True),('D_FINE',False)]:
        p=next(p for p in r['profiles'] if p['final_decay']==on and p['maximum_half_ticks']==524288)
        values=struct.pack('<458d',*p['grids'][0]['values']);bits=struct.unpack('<458Q',values)
        private=f'references-local/contour-cycle-inputs01/{int(on)}-524288.ckp';raw=(ROOT/private).read_bytes()
        require(raw[56:]==values and struct.unpack_from('<Q',raw,8)[0]==4423942144 and struct.unpack_from('<3I',raw,16)==(524288,20,1024),'own fine history metadata and public bits')
        extra+=f'pub const {tag}_STATE:[u64;458]=['+','.join(map(str,bits))+'];\n'
        records.append(dict(name=tag,source_public_path=name,private_origin=private,private_origin_sha256=sha(ROOT/private),public_bits_identical=True))
    return extra,records

def main():
    rejection='evidence/voice_conditioned_recipe_rejection_replay01.json';r=json.loads((ROOT/rejection).read_text(encoding='utf8'))
    require(r['passed'] and r['identical_native_replay'],'unchanged native rejection replay before repair')
    names=['crates/rf-d-circuit/src/conditioned_recipe.rs','crates/rf-d-circuit/src/conditioned_recipe_seed.rs',
        'crates/rf-d-circuit/tests/conditioned_recipe.rs','tools/test_conditioned_recipe.py','tools/run_conditioned_recipe.py']
    saved={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    p=ROOT/names[1];require(p.read_text(encoding='utf8')==generated_seed(),'unextended published seed')
    extra,records=fine_seed();p.write_bytes(p.read_bytes()+extra.encode())
    p=ROOT/FINE;require(not p.exists(),'exclusive fine fixture');p.write_text(extra,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+HIST_ATTR)
    # Exact source changes: history selector only, no solver/equation change.
    p=ROOT/names[0];s=p.read_text(encoding='utf8');old='let bits = match self.final_decay { FinalDecay::On => seed::A_STATE, FinalDecay::Off => seed::D_STATE };'
    new='''let bits = match (self.final_decay, self.resolution) {
            (FinalDecay::On, Resolution::Half2Us) => seed::A_STATE,
            (FinalDecay::Off, Resolution::Half2Us) => seed::D_STATE,
            (FinalDecay::On, Resolution::Half1Us) => seed::A_FINE_STATE,
            (FinalDecay::Off, Resolution::Half1Us) => seed::D_FINE_STATE,
        };'''
    require(s.count(old)==1,'exclusive selector repair');p.write_text(s.replace(old,new),encoding='utf8',newline='\n')
    p=ROOT/names[2];s=p.read_text(encoding='utf8');anchor='#[allow(dead_code)] #[path="support/conditioned_seed.rs"] mod seed;'
    require(s.count(anchor)==1,'test fixture anchor');s=s.replace(anchor,anchor+'\n#[allow(dead_code)] #[path="support/conditioned_recipe_fine_seed.rs"] mod fine_seed;')
    old='assert_eq!(bits(q.state),if mode==FinalDecay::On{seed::A_STATE}else{seed::D_STATE});'
    new='''let expected=match(mode,resolution){
            (FinalDecay::On,Resolution::Half2Us)=>seed::A_STATE,
            (FinalDecay::Off,Resolution::Half2Us)=>seed::D_STATE,
            (FinalDecay::On,Resolution::Half1Us)=>fine_seed::A_FINE_STATE,
            (FinalDecay::Off,Resolution::Half1Us)=>fine_seed::D_FINE_STATE,
        };assert_eq!(bits(q.state),expected);'''
    require(s.count(old)==1,'test selector');p.write_text(s.replace(old,new),encoding='utf8',newline='\n')
    p=ROOT/names[3];s=p.read_text(encoding='utf8');require(s.count('from conditioned_recipe_native import')==1,'test library adapter');p.write_text(s.replace('from conditioned_recipe_native import','from conditioned_recipe_native02 import'),encoding='utf8',newline='\n')
    p=ROOT/names[4];s=p.read_text(encoding='utf8').replace('recipe_library01','recipe_library02').replace('recipe-library01','recipe-library02').replace("+'tests03.json'","+'tests04.json'")
    p.write_text(s,encoding='utf8',newline='\n')
    write('evidence/voice_conditioned_recipe_history_repair01.json',dict(passed=True,
        source_sha256={'tools/extend_conditioned_recipe.py':sha(ROOT/'tools/extend_conditioned_recipe.py'),
            'docs/RECETA_CONDICIONADA_HISTORIAS.md':sha(ROOT/'docs/RECETA_CONDICIONADA_HISTORIAS.md'),
            'evidence/voice_schur_chain_trajectory01.json':sha(ROOT/'evidence/voice_schur_chain_trajectory01.json')},
        failed_native_receipt_sha256=sha(ROOT/'evidence/voice_conditioned_recipe_native01.json'),
        rejected_replay_sha256=sha(ROOT/rejection),before_source_base64=saved,
        repaired_source_sha256={n:sha(ROOT/n) for n in names+[FINE]},
        private_used_sha256={p['private_origin']:p['private_origin_sha256'] for p in records},records=records,
        initial_histories=4,resolution_specific_histories=True,previous_seed_prefix_preserved=True,
        numerical_gates_changed=False,solver_or_topology_changed=False,new_temporal_duration_s=0))
    print('RECIPE_HISTORY_REPAIR',4,458)
if __name__=='__main__':main()
