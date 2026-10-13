"""Publish already public synthetic ON/OFF histories; preserve base byte identities."""
import base64,json,re,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

EXPORT=b'\npub mod conditioned_recipe;\n'
RUST=['crates/rf-d-circuit/src/conditioned_recipe.rs',
      'crates/rf-d-circuit/src/conditioned_recipe_seed.rs',
      'crates/rf-d-circuit/examples/conditioned_render.rs',
      'crates/rf-d-circuit/tests/conditioned_recipe.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RUST)).encode()

def generated_seed():
    source=(ROOT/'crates/rf-d-circuit/tests/support/conditioned_seed.rs').read_text(encoding='utf8')
    arrays=[re.search(r'pub const '+tag+r'_STATE:\[u64;458\]=\[.*?\];',source,re.S).group(0) for tag in ['A','D']]
    return '// Already public synthetic nominal histories, unchanged IEEE-754 bits.\n'+'\n'.join(arrays)+'\n'

def main():
    previous='evidence/voice_conditioned_portable_tests01.json'
    old=json.loads((ROOT/previous).read_text(encoding='utf8'))
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    require(head=='aa496b55513ddff7476e1e6625114d7b8064ee85' and old['passed'],'base')
    mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','crates/rf-d-circuit/src/lib.rs']
    write('evidence/voice_conditioned_recipe_before01.json',dict(base_commit=head,
        previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    path=ROOT/RUST[1];require(not path.exists(),'exclusive synthetic seed');path.write_text(generated_seed(),encoding='utf8',newline='\n')
    for n,suffix in [('.gitattributes',ATTR),('crates/rf-d-circuit/src/lib.rs',EXPORT)]:
        p=ROOT/n;p.write_bytes(p.read_bytes()+suffix)
    write('evidence/voice_conditioned_recipe_seed01.json',dict(passed=True,
        source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_conditioned_recipe.py',RUST[1],'crates/rf-d-circuit/tests/support/conditioned_seed.rs']},
        own_synthetic_model_histories=True,proprietary_capture=False,arrays=2,float_bits_per_array=458,
        history_start_ticks=4423942144,history_start_s=.008438,physical_startup=False,
        parameters_source='tools/conditioned_portable_runner.rs::scene',
        history_source='crates/rf-d-circuit/tests/support/conditioned_seed.rs::A_STATE,D_STATE'))
    print('CONDITIONED_RECIPE_SEED',2,458)
if __name__=='__main__':main()
