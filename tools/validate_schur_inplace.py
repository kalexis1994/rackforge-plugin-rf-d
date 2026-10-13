"""Publish admitted conditional Schur trajectories with exact provenance and bounded scope."""
import json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_schur_inplace_tests01.json'
def audit():
    previous='evidence/voice_schur_cost_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));ref=json.loads((ROOT/'evidence/voice_schur_inplace_reference01.json').read_text(encoding='utf8'));require(old['passed'] and ref['passed'] and ref['lab_collection_verified'] and ref['numeric_bank_passed'] and ref['cost_utility_passed'] and ref['dynamic_schur_admitted'] and ref['schur_cycle_window_admitted'],'admitted scoped trajectory');require(ref['independent_nonlinear_rows_reexecuted']==38472 and ref['inherited_independent_linear_rows']==181368 and ref['solver_regressions']==26 and ref['fine_steps']==26770 and ref['restores']==24 and ref['replayed_accepted_steps']==368,'fresh/inherited scope');require(not any(ref[k] for k in ['new_audio','physical_fidelity','real_time','full_contour_from_silence_admitted']),'admission limits')
    for n,h in ref['private_input_sha256'].items():require(sha(ROOT/n)==h,'private identity '+n)
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/schur-inplace-conditional-cycle/v1',**ref,source_sha256=sources,source_sha256_after=sources,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),failed_source_base64=__import__('base64').b64encode((ROOT/'tools/validate_schur_inplace.py').read_bytes()).decode());k=1
        while (ROOT/f'evidence/voice_schur_inplace_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_schur_inplace_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('SCHUR_INPLACE_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),'ADMITTED',r['dynamic_schur_admitted'])
if __name__=='__main__':main()
