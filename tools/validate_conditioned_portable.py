"""Release an additive public API with owned scratch and scoped inherited equations."""
import json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_conditioned_portable_tests01.json'

def audit():
    previous='evidence/voice_radau_inplace_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));ref=json.loads((ROOT/'evidence/voice_conditioned_portable_reference01.json').read_text(encoding='utf8'))
    require(old['passed'] and ref['passed'] and ref['public_conditioned_voice_admitted'] and ref['public_conditioned_temporal_engine_admitted'] and ref['schur_cycle_window_admitted'],'scoped public integration')
    require(ref['native_test_count']==4 and ref['inherited_test_count']==248 and ref['covered_test_count']==252 and ref['heap_measured'] and ref['processing_allocations']==0 and ref['measured_successful_processing_calls']==9 and ref['measured_rejected_processing_calls']==3,'new and inherited tests')
    require(ref['inherited_independent_linear_rows']==181368 and ref['inherited_bank_nonlinear_rows']==ref['inherited_temporal_nonlinear_rows']==38472 and ref['independent_equations_reexecuted']==0 and ref['identical_temporal_data_files']==40,'identity inheritance')
    require(ref['new_library_compile'] and not ref['new_cargo_cache'] and not ref['active_linear_archive_exported'],'library and stored-matrix scope')
    require(not any(ref[k] for k in ['deadline_measured','physical_fidelity','real_time','full_contour_from_silence_admitted','new_audio']),'admission limits')
    for n,h in ref['private_input_sha256'].items():require(sha(ROOT/n)==h,'private identity '+n)
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/public-conditioned-owned-workspace/v1',**ref,source_sha256=sources,source_sha256_after=sources,previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))

def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),failed_source_base64=__import__('base64').b64encode((ROOT/'tools/validate_conditioned_portable.py').read_bytes()).decode());k=1
        while (ROOT/f'evidence/voice_conditioned_portable_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_conditioned_portable_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('PUBLIC_CONDITIONED_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),'TESTS',r['covered_test_count'])
if __name__=='__main__':main()
