"""Admit the restored release, original graph audit and joined finite WAV."""
import base64,hashlib,json,shutil,subprocess,traceback
from decimal import Decimal
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,TICK
from prepare_release_voice import ATTR,EXAMPLE,caller,START,SPAN
from prepare_release_auditor import source as auditor_source
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_release_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_sustained_tests01.json';old=read(previous);before=read('evidence/voice_release_before01.json')
    require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'admitted prior release');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base HEAD')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'exact added Rust rules');require((ROOT/EXAMPLE).read_text(encoding='utf8')==caller(),'declared caller transformation');require((ROOT/'tools/check_release_voice.py').read_text(encoding='utf8')==auditor_source(),'declared original graph adapter')
    for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historic doc prefix')
    require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_sustained_tests01.json',b'voice_release_tests01.json')),'README declared QA replacement')
    names=['evidence/voice_release_'+tag+'01.json' for tag in ['inputs','native','reference','review','listening','cli']];receipts=[read(n) for n in names]
    for name,r in zip(names,receipts):
        require(r['passed'],'passed experiment '+name)
        for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h,'measured source '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable measured sources')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private use '+n);private[n]=h
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable measured private')
        for output in r.get('outputs',[])+r.get('files',[]):
            n,h=output['path'],output['sha256'];require(sha(ROOT/n)==h,'new output '+n);private[n]=h
        for executable in ['compiler','renderer']:
            if executable in r:require(sha(Path(r[executable]['path']))==r[executable]['sha256'],'frozen '+executable)
    inp,native,ref,review,listening,cli=receipts
    require(inp['start_ticks']==START and inp['span_ticks']==SPAN and inp['only_magic_and_recipe_phase_changed'] and not inp['source_event_applied'],'incoming format change only')
    require(not native['new_library_compile'] and not native['new_cargo_cache'] and native['lab_stack_bytes']==33554432 and len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120,'frozen library and bounded caller compile')
    require(len(native['profiles'])==2 and not native['replays'] and native['wall_s']<=3300 and all(p['exit_code']==0 and p['wall_s']<=1590 for p in native['profiles']),'bounded campaign')
    require(ref['release_continuation_admitted'] and ref['continued_duration_s']==.008 and ref['joined_duration_s']==.020004 and ref['release_since_source_off_s']==.012 and ref['wall_s']<=600,'continued independent graph/refinement')
    require(len(ref['profiles'])==2 and len(ref['same_clock_refinement'])==28 and all(p['final_decay'] and len(p['grids'])==28 for p in ref['profiles']),'28 full state comparisons')
    require(ref['independent_nonlinear_rows']==1374*sum(p['selected_accepted_count'] for p in ref['profiles']) and ref['independent_candidates']==6*sum(p['selected_accepted_count'] for p in ref['profiles']),'selected original graph coverage')
    require(ref['maximum_active_replay_probes']<=3 and ref['rejected_corruptions']==8 and ref['atomic_rollbacks']==2 and ref['restores']==sum(p['restores'] for p in ref['profiles']) and ref['replayed_accepted_steps']==sum(p['replayed_accepted_steps'] for p in ref['profiles']),'bounded serial replay and rollback')
    require(len(ref['seams'])==2 and all(s['preserved_state_bits']==458 and s['preserved_next_full_ticks']==4096 and not s['source_event_applied'] and s['parent_sha256']==s['source_copy_sha256'] for s in ref['seams']),'own checkpoint seam')
    for p in ref['profiles']:
        for n,h in p['input_sha256'].items():require(private[n]==h,'graph inputs inventory')
        require(len(p['resets'])>=2,'continued oscillator cycles')
        for balance in [p['total_ledger'],*[q['ledger'] for q in p['phases']]]:
            require(len(balance['rows'])==9 and all(Decimal(r['error_c'])<=Decimal(r['gate_c']) for r in balance['rows']),'oriented charge balances')
    require(len(ref['joined_ledgers'])==2 and all(j['duration_s']==(START+SPAN-4423942144)*TICK and len(j['ledger']['rows'])==9 and all(Decimal(r['error_c'])<=Decimal(r['gate_c']) for r in j['ledger']['rows']) for j in ref['joined_ledgers']),'joined physical charge endpoints')
    require(ref['turn_observed'] and ref['latch_observed'] and len(ref['flux_checks'])==2 and not ref['new_source_event'],'state transitions without new source events')
    for p,f in zip(ref['profiles'],ref['flux_checks']):
        require(f['records']==p['fine_steps']+1 and f['selected_independent_endpoints']==15 and f['max_derivative_balance_error_v_per_s']<=2e-6 and f['final_slope_v_per_s']<0,'every exported C2 derivative balance')
        require([e['kind'] for e in f['events']]==['LATCH','TURN'] and all(e['bracket_width_s']<=1e-7 for e in f['events']),'observed transition brackets')
    require(len(ref['transition_refinement'])==2 and all(Decimal(x['difference_s'])<=Decimal('1e-7') for x in ref['transition_refinement']),'event refinement')
    require(not any(review[k] for k in ['topology_changed','audible_constants_changed','numerical_gates_changed','physical_devices_identified']) and review['source_locator_correction']['previous_document_unchanged'],'documentary source review only')
    require(listening['identical_derived_replay'] and listening['native_resolution_max_error_v']<=2e-6 and listening['native_resolution_max_pcm_lsb']<=7 and listening['joined_simulated_window_s']==.020004,'joined native audio resolution')
    require(not any(listening[k] for k in ['repeated','dc_removed','fades','peak_normalization','steady_periodicity_admitted','real_time','physical_fidelity']),'native audio boundaries')
    require(len(listening['files'])==2 and all(f['frames']==960 and f['stretch']==1 and not f['repeated'] and f['full_audio_duration_simulated'] for f in listening['files']),'finite native durations')
    require(cli['integration_checks']==3 and all(cli[k] for k in ['user_cli_wav_identical','sidecar_verified','existing_output_rejected_without_mutation','mismatched_seam_rejected_before_publication']),'joined CLI integration')
    require(not any(ref[k] for k in ['steady_periodicity_admitted','full_contour_from_silence_admitted','physical_fidelity','real_time']),'conditional release scope')
    added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=96*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'newly bound private inventory and reserve')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA')
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{previous}|(set(staged)-{OUT}))}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    r=dict(schema='rf-d/restored-release-current-balance/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,
        protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),new_private_bytes=size,new_private_inventory_bytes=size,new_private_inventory_files=len(added),
        release_continuation_admitted=True,conditioned_own_histories=2,continued_duration_s=.008,joined_duration_s=.020004,release_since_source_off_s=.012,
        independent_nonlinear_rows=ref['independent_nonlinear_rows'],independent_candidates=ref['independent_candidates'],accepted_steps=ref['accepted_steps'],fine_steps=ref['fine_steps'],same_clock_states=28,
        reset_crossings=sum(len(p['resets']) for p in ref['profiles']),replayed_accepted_steps=ref['replayed_accepted_steps'],restores=ref['restores'],maximum_active_replay_probes=ref['maximum_active_replay_probes'],rejected_corruptions=8,atomic_rollbacks=2,
        preserved_state_bits_at_seam=458,preserved_next_full_ticks=4096,new_source_event=False,turn_observed=True,latch_observed=True,source_review_changed_topology=False,
        new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,native_wall_s=native['wall_s'],lab_stack_bytes=33554432,
        inherited_test_count=255,native_test_count=0,covered_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,user_cli_integration_checks=3,
        heap_measured_this_block=False,deadline_measured=False,new_audio=True,new_audio_files=2,cycle_repeated=False,full_audio_duration_simulated=True,
        full_contour_from_silence_admitted=False,steady_periodicity_admitted=False,physical_fidelity=False,real_time=False,
        release_listening='evidence/voice_release_listening01.json',release_reference='evidence/voice_release_reference01.json',release_review='evidence/voice_release_review01.json',local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic']:r[k]=old[k]
    return r

def main():
    try:r=audit()
    except Exception:
        first=traceback.format_exc()
        try:audit();second='unexpected pass'
        except Exception:second=traceback.format_exc()
        r=dict(passed=False,failure=first,replay=second,failed_source_base64=base64.b64encode((ROOT/'tools/validate_release_voice.py').read_bytes()).decode());k=1
        while(ROOT/f'evidence/voice_release_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_release_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('RELEASE_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
