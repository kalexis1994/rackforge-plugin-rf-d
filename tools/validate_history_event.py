"""Immutable lineage and admission of only the local interpolated observer."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_history_event_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_history_propagation_tests01.json';old=read(previous);before=read('evidence/voice_history_event_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous admission');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base unchanged')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,d in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==d,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,d in private.items():require(sha(ROOT/n)==d,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_history_event.rs text eol=lf\n/tools/joint_history_event_runner.rs text eol=lf\n/tools/clean_rackforge_build_cache.ps1 text eol=lf\n/evidence/storage_cleanup01.json text eol=lf\n','only laboratory and cleanup LF attributes')
    inputs=read('evidence/voice_history_event_inputs01.json');require(inputs['passed'] and len(inputs['events'])==8 and sha(ROOT/inputs['path'])==inputs['sha256'],'frozen inputs');private[inputs['path']]=inputs['sha256']
    for n,d in inputs['source_sha256'].items():require(sha(ROOT/n)==d,'preparation identity')
    for n,d in inputs['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'protected source input')
    native=read('evidence/voice_history_event_native01.json');require(native['passed'] and native['source_sha256']==native['source_sha256_after'] and native['private_used_sha256']==native['private_used_sha256_after'],'passed stable native')
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'] and not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'frozen build')
    for n,d in native['source_sha256'].items():require(sha(ROOT/n)==d,'measured native source')
    for n,d in native['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'native input')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'native output');private[o['path']]=o['sha256']
    require(native['reserve_bytes']==512*1024**2 and native['estimated_output_bytes']==16*1024**2 and native['minimum_free_bytes']>=native['reserve_bytes'] and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['wall_s']<=480,'compact resource preflight')
    require(len(native['commands'])==2 and not native['replays'],'exact two commands')
    for k,c in enumerate(native['commands']):require(c['exit_code']==0 and not c['administrative_stop'] and c['wall_s']<=(120 if k==0 else 300),'command resources')
    ref=read('evidence/voice_history_event_reference01.json');require(ref['passed'] and ref['source_sha256']==ref['source_sha256_after'] and ref['wall_s']<=300,'passed stable oracle')
    for n,d in ref['source_sha256'].items():require(sha(ROOT/n)==d,'measured oracle source')
    for n,d in ref['input_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'oracle input')
    cleanup=read('evidence/storage_cleanup01.json');require(cleanup['passed'] and cleanup['source_sha256']['tools/clean_rackforge_build_cache.ps1']==sha(ROOT/'tools/clean_rackforge_build_cache.ps1'),'cleanup source')
    cn=cleanup['private_receipt'];require(sha(ROOT/cn)==cleanup['private_receipt_sha256'],'cleanup receipt identity');operation=read(cn);private[cn]=cleanup['private_receipt_sha256'];canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':')).encode('utf8')
    require(operation['passed'] and not operation['errors'] and canonical(operation['runtime_before'])==canonical(operation['runtime_after']) and canonical(operation['git_status_before'])==canonical(operation['git_status_after']),'preserved runtime and host source')
    cache=Path(operation['cache_root']).resolve();host=Path(operation['host_root']).resolve();require(cache==host/'target/release/deps' and cache.is_relative_to(host),'bounded cache path')
    require(len(operation['deleted'])==cleanup['deleted_files']==5346 and int(operation['deleted_logical_bytes'])==cleanup['deleted_logical_bytes']==sum(a['bytes'] for a in operation['deleted']),'cleanup coverage')
    require(operation['allowed_extensions']==cleanup['allowed_extensions']==['.rlib','.rmeta','.pdb','.o','.d'],'regenerable extensions only')
    for a in operation['deleted']:
        p=Path(a['path']).resolve();require(p.parent==cache and p.suffix in operation['allowed_extensions'],'bounded deleted file')
    require(canonical(operation['planned'])==canonical(operation['deleted']) and len(operation['runtime_before'])==cleanup['runtime_files_preserved']==166 and not any(cleanup[k] for k in ['measurements_deleted','executables_deleted','packages_deleted','host_source_changes']),'complete cleanup plan')
    preliminary='references-local/storage-cleanup01/qa-preliminary.json';pqa=read(preliminary);require(pqa['passed'] and pqa['base_commit']==before['base_commit'],'preserved preliminary release audit')
    for original,copy in [('tools/validate_history_event.py','qa-preliminary.py'),('.gitattributes','qa-preliminary.gitattributes')]:
        name='references-local/storage-cleanup01/'+copy;require(sha(ROOT/name)==pqa['source_sha256'][original],'preserved pre-LF source');private[name]=sha(ROOT/name)
    private[preliminary]=sha(ROOT/preliminary)
    for n,d in pqa['source_sha256'].items():
        if n not in ['tools/validate_history_event.py','.gitattributes']:require(sha(ROOT/n)==d,'unchanged preliminarily audited source')
    counts=dict(baseline_bit_reproductions=16,baseline_sensitivity_bit_coordinates=57600,event_directions=72,event_state_coordinates=14400,perturbed_native_step_solves=576,own_event_observations=288,negative_controls=8,positive_controls=8)
    for k,v in counts.items():require(ref[k]==v,'coverage '+k)
    require(len(ref['records'])==8,'eight checked events')
    for event,row in zip(inputs['events'],ref['records']):
        require(event['id']==row['id'] and 0<=row['alpha']<=1 and len(row['responses'])==9 and abs(row['omitted_time_term_ramp_change_v'])>1e-8,'positive control and coverage')
        require(len(row['stage_checks'])==2 and all(len(stage)==9 and all(a['max_ratio']<=1 for a in stage) for stage in row['stage_checks']),'independent stage coverage')
        for a in row['responses']:
            require(all(a[k]['max_ratio']<=1 for k in ['state_independent','time_independent','alpha_independent']) and len(a['nonlinear_fd'])==2 and all(b['state']['max_ratio']<=1 and b['time']['max_ratio']<=1 for b in a['nonlinear_fd']),'phase gates')
            require(len(a['own_state_observations'])==2 and all(len(pair)==2 and all(b['max_ratio']<=1 for b in pair) for pair in a['own_state_observations']),'own complete observation coverage')
    require(ref['local_interpolated_event_derivative_admitted'] and not any(ref[k] for k in ['continuous_event_derivative_admitted','adaptive_derivative_admitted','period_map_admitted','physical_fidelity','real_time']) and ref['independent_roots']==0,'local observer scope')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');links=local_links(sorted(n for n in staged if n.endswith('.md')));names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/history-event-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,local_interpolated_event_derivative_admitted=True,continuous_event_derivative_admitted=False,adaptive_derivative_admitted=False,period_map_admitted=False,independent_roots=0,physical_cards_changed=False,new_library_compile=False,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,storage_cleanup_summary_sha256=sha(ROOT/'evidence/storage_cleanup01.json'),deleted_build_cache_files=cleanup['deleted_files'],deleted_build_cache_logical_bytes=cleanup['deleted_logical_bytes'],previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=links)
def main():
    try:report=audit()
    except Exception:
        report=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_history_event.py').read_text())
        try:audit();report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_history_event_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_history_event_qa_failure{k:02d}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('EVENT_QA',report['passed'],len(report['source_sha256']),len(report['private_input_sha256']),flush=True)
if __name__=='__main__':main()
