"""Release the extended conditional window, original graph gates and native audio."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from prepare_sustained_voice import ATTR,EXAMPLE,caller,START,BOUNDARIES
from prepare_sustained_auditor import source as auditor_source
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_sustained_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_conditioned_recipe_tests01.json';old=read(previous);before=read('evidence/voice_sustained_before01.json')
    require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'admitted prior release');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base HEAD')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'exact added Rust rules');require((ROOT/EXAMPLE).read_text(encoding='utf8')==caller(),'declared caller transformation');require((ROOT/'tools/check_sustained_voice.py').read_text(encoding='utf8')==auditor_source(),'declared graph adapter')
    for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic doc prefix')
    require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_conditioned_recipe_tests01.json',b'voice_sustained_tests01.json')),'README declared QA replacement')
    names=['evidence/voice_sustained_'+tag+'01.json' for tag in ['inputs','native','reference','listening','cli','diagnostic']];receipts=[read(n) for n in names]
    for name,r in zip(names,receipts):
        require(r['passed'],'passed experiment '+name)
        for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h,'measured source '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable measured sources')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private use '+n);private[n]=h
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable measured private')
        for output in r.get('outputs',[])+r.get('files',[]):
            n,h=output['path'],output['sha256'];require(sha(ROOT/n)==h,'new output '+n);private[n]=h
        if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
    inp,native,ref,listening,cli,diagnostic=receipts
    require(not native['new_library_compile'] and not native['new_cargo_cache'] and native['lab_stack_bytes']==33554432 and len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120,'frozen library, bounded caller compile')
    require(len(native['profiles'])==2 and not native['replays'] and native['wall_s']<=3300 and all(p['exit_code']==0 and p['wall_s']<=1590 for p in native['profiles']),'bounded campaign')
    require(ref['sustained_on_window_admitted'] and ref['duration_per_profile_s']==.012004 and ref['held_s']==.008 and ref['release_s']==.004 and ref['wall_s']<=600,'extended independent graph/refinement')
    require(len(ref['profiles'])==2 and len(ref['same_clock_refinement'])==43 and all(p['final_decay'] and len(p['grids'])==43 for p in ref['profiles']),'43 full state comparisons')
    require(ref['independent_nonlinear_rows']==1374*sum(p['selected_accepted_count'] for p in ref['profiles']) and ref['independent_candidates']==6*sum(p['selected_accepted_count'] for p in ref['profiles']),'selected original graph coverage')
    require(ref['maximum_active_replay_probes']<=3 and ref['rejected_corruptions']==8 and ref['atomic_rollbacks']==4 and ref['restores']==sum(p['restores'] for p in ref['profiles']) and ref['replayed_accepted_steps']==sum(p['replayed_accepted_steps'] for p in ref['profiles']),'bounded serial replay/rollback coverage')
    require(all(p['all_exported_prefix_bits_identical'] and p['grid_states']==7 and p['prefix_end_ticks']==START+788529152 for p in ref['admitted_prefix_identity']),'admitted own prefix')
    for p in ref['profiles']:
        for n,h in p['input_sha256'].items():require(private[n]==h,'graph inputs inventory')
        require(len(p['resets'])>=3 and sum(x['phase']==1 for x in p['resets'])>=3,'held complete cycles')
        for balance in [p['total_ledger'],*[q['ledger'] for q in p['phases']]]:
            require(len(balance['rows'])==9 and all(__import__('decimal').Decimal(r['error_c'])<=__import__('decimal').Decimal(r['gate_c']) for r in balance['rows']),'oriented charge balances')
    require(listening['identical_derived_replay'] and listening['native_resolution_max_error_v']<=2e-6 and listening['native_resolution_max_pcm_lsb']<=7 and listening['simulated_window_s']==.012004,'native audio resolution')
    require(not any(listening[k] for k in ['native_repeated','native_dc_removed','native_fades','peak_normalization','steady_periodicity_admitted','real_time','physical_fidelity']),'native audio boundaries')
    native_files=[f for f in listening['files'] if f['adaptation']=='native'];microscopes=[f for f in listening['files'] if f['adaptation']=='microscope']
    require(len(native_files)==2 and len(microscopes)==1 and all(f['frames']==576 and f['stretch']==1 and not f['repeated'] for f in native_files) and microscopes[0]['frames']==57619 and microscopes[0]['stretch']==100,'finite native/mapped durations')
    require(listening['cycle_repeated']==ref['repetition_candidate'] and bool([f for f in listening['files'] if f['adaptation']=='observed-cycle-repeated'])==ref['repetition_candidate'],'cycle proposal gate preserved')
    require(cli['user_cli_wav_identical'] and cli['sidecar_verified'] and cli['existing_output_rejected_without_mutation'],'public CLI checks')
    require(len(diagnostic['observations'])==2 and diagnostic['repetition_candidate_unchanged']==ref['repetition_candidate'] and not diagnostic['numerical_gates_changed'] and not diagnostic['dc_subtraction_applied_to_native_wav'],'diagnosis leaves audio/admission gates unchanged')
    require(not ref['steady_periodicity_admitted'] and not ref['full_contour_from_silence_admitted'] and not ref['physical_fidelity'] and not ref['real_time'],'extended window scope')
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));require(size<=96*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'new outputs and reserve budget')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA')
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/held-released-own-trajectory/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),
        source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),new_private_bytes=size,
        sustained_on_window_admitted=True,conditioned_own_histories=2,duration_per_profile_s=.012004,held_s=.008,release_s=.004,
        independent_nonlinear_rows=ref['independent_nonlinear_rows'],independent_candidates=ref['independent_candidates'],accepted_steps=ref['accepted_steps'],fine_steps=ref['fine_steps'],same_clock_states=43,
        reset_crossings=ref['reset_crossings'],replayed_accepted_steps=ref['replayed_accepted_steps'],restores=ref['restores'],maximum_active_replay_probes=ref['maximum_active_replay_probes'],rejected_corruptions=8,atomic_rollbacks=4,
        admitted_prefix_identical=True,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,native_wall_s=native['wall_s'],lab_stack_bytes=33554432,
        inherited_test_count=255,native_test_count=0,covered_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,user_cli_integration_checks=2,
        heap_measured_this_block=False,deadline_measured=False,new_audio=True,new_audio_files=len(listening['files']),cycle_repeated=ref['repetition_candidate'],full_audio_duration_simulated=False,
        full_contour_from_silence_admitted=False,steady_periodicity_admitted=False,physical_fidelity=False,real_time=False,
        previous_audio=old['previous_audio'],native_listening=old['native_listening'],native_chain_listening=old['native_chain_listening'],official_executable_sha256=old['official_executable_sha256'],
        conditioned_transient_listening=old['conditioned_transient_listening'],sustained_listening='evidence/voice_sustained_listening01.json',sustained_diagnostic='evidence/voice_sustained_diagnostic01.json',local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))

def main():
    try:r=audit()
    except Exception:
        # Preserve the failed adapter and one unchanged replay before repairs.
        first=traceback.format_exc()
        try:audit();second='unexpected pass'
        except Exception:second=traceback.format_exc()
        r=dict(passed=False,failure=first,replay=second,failed_source_base64=base64.b64encode((ROOT/'tools/validate_sustained_voice.py').read_bytes()).decode());k=1
        while(ROOT/f'evidence/voice_sustained_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_sustained_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('SUSTAINED_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
