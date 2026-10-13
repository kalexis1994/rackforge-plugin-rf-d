"""Publish the standalone recipe/render release with bounded auditable scope."""
import base64,json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_conditioned_recipe_tests01.json'

def audit():
    previous='evidence/voice_conditioned_portable_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'))
    ref=json.loads((ROOT/'evidence/voice_conditioned_recipe_reference01.json').read_text(encoding='utf8'))
    require(old['passed'] and ref['passed'] and ref['public_conditioned_recipe_admitted'] and ref['standalone_offline_render_admitted'],'recipe/render reference')
    require(ref['resolution_specific_own_histories']==4 and ref['covered_test_count']==255 and ref['native_test_count']==7 and ref['inherited_test_count']==248 and ref['native_python_test_count']==2,'new/rerun/inherited scopes')
    require(ref['new_audio_files']==4 and ref['new_extended_duration_s']==0 and not ref['physical_fidelity'] and not ref['real_time'] and not ref['periodicity_admitted'],'audible limits')
    for n,h in ref['private_input_sha256'].items():require(sha(ROOT/n)==h,'private identity '+n)
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA')
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/public-own-history-finite-render/v1',**ref,
        source_sha256=sources,source_sha256_after=sources,previous_audio=old['previous_audio'],
        native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],
        official_executable_sha256=old['official_executable_sha256'],
        conditioned_transient_listening='evidence/voice_conditioned_recipe_listening01.json',
        local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))

def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),failed_source_base64=base64.b64encode((ROOT/'tools/validate_conditioned_recipe.py').read_bytes()).decode());k=1
        while(ROOT/f'evidence/voice_conditioned_recipe_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_conditioned_recipe_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print('RECIPE_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']))
if __name__=='__main__':main()
