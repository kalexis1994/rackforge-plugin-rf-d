"""Protected lineage and admission of one full fixed interval, one FD column."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_return_interval_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_history_event_tests01.json';old=read(previous);before=read('evidence/voice_return_interval_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous admission');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base unchanged');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,d in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==d,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,d in private.items():require(sha(ROOT/n)==d,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_return_interval_runner.rs text eol=lf\n','only new caller LF attribute')
    inputs=read('evidence/voice_return_interval_inputs01.json');require(inputs['passed'] and inputs['steps']==22356 and len(inputs['points'])==15 and sha(ROOT/inputs['path'])==inputs['sha256'],'frozen complete input');private[inputs['path']]=inputs['sha256']
    for n,d in inputs['source_sha256'].items():require(sha(ROOT/n)==d,'preparation source')
    for n,d in inputs['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'protected original input')
    native=read('evidence/voice_return_interval_native01.json');require(native['passed'] and native['source_sha256']==native['source_sha256_after'] and native['private_used_sha256']==native['private_used_sha256_after'],'passed stable native');require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'] and not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'frozen build')
    for n,d in native['source_sha256'].items():require(sha(ROOT/n)==d,'native source')
    for n,d in native['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'native input')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'native output');private[o['path']]=o['sha256']
    require(native['reserve_bytes']==1024**3 and native['estimated_output_bytes']==64*1024**2 and native['minimum_free_bytes']>=native['reserve_bytes'] and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['wall_s']<=2400 and native['lab_stack_bytes']==33554432,'resource bounds');require(sum(o['bytes'] for o in native['outputs'])<=native['estimated_output_bytes'],'compact output bound');require(len(native['commands'])==2 and not native['replays'],'exact commands')
    for k,c in enumerate(native['commands']):require(c['exit_code']==0 and not c['administrative_stop'] and c['wall_s']<=(120 if k==0 else 2300),'command budget')
    ref=read('evidence/voice_return_interval_reference01.json');require(ref['passed'] and ref['source_sha256']==ref['source_sha256_after'] and ref['wall_s']<=300,'passed stable oracle')
    for n,d in ref['source_sha256'].items():require(sha(ROOT/n)==d,'oracle source')
    for n,d in ref['input_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'oracle input')
    counts=dict(baseline_bit_steps=22356,fixture_bit_steps=4,selected_operator_points=15,selected_operator_directions=135,selected_operator_coordinates=54000,independent_nonlinear_rows=6000,perturbed_native_step_solves=89424,own_event_observations=8,native_zero_control_steps=22356,event_zero_controls=2)
    for k,v in counts.items():require(ref[k]==v,'coverage '+k)
    require(ref['native_columns']==[43,5,12,139,199,194,157,117,98] and ref['full_interval_fd_columns']==[139] and ref['full_interval_direction139_admitted'] and ref['independent_roots']==0,'one complete FD column');require(not any(ref[k] for k in ['gain_independent_all_steps','independent_all_step_propagation','charge_root_basis_admitted','period_map_admitted','adaptive_derivative_admitted','continuous_event_derivative_admitted','physical_fidelity','real_time','new_audio']),'scope exclusions')
    require([row['step'] for row in ref['operators']]==inputs['points'],'operator sample coverage')
    for row in ref['operators']:require(len(row['comparisons'])==9 and all(a['max_ratio']<=1 for a in row['comparisons']) and row['nonlinear_candidate']['rows']==400 and row['nonlinear_candidate']['residual_gate_ratio']<=1 and row['nonlinear_candidate']['correction_gate_ratio']<=1,'operator and nonlinear gates')
    require(len(ref['events'])==2 and len(ref['selected_endpoint_response'])==9,'event coverage')
    for event in ref['events']:
        require(0<=event['alpha']<=1 and event['observation']['max_ratio']<=1 and len(event['comparisons'])==9,'base event')
        for a in event['comparisons']:require(all(a[k]['max_ratio']<=1 for k in ['state','time','alpha']),'event independent gates')
    for a in ref['selected_endpoint_response']:require(a['period']['max_ratio']<=1 and a['drift']['max_ratio']<=1,'endpoint response gates')
    require(ref['baseline_drift_observation']['max_ratio']<=1 and len(ref['own_histories'])==4 and len(ref['capacitors'])==18 and [a['scale'] for a in ref['nonlinear_fd']]==[1.,.5],'complete own and capacitor coverage')
    for own in ref['own_histories']:require(len(own['observations'])==2 and all(a['max_ratio']<=1 for a in own['observations']) and len(own['alphas'])==2 and all(0<=a<=1 for a in own['alphas']),'own brackets')
    for a in ref['nonlinear_fd']:require(all(a[k]['max_ratio']<=1 for k in ['first_event','second_event','period','drift','capacitor_drift']),'complete nonlinear gates')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');links=local_links(sorted(n for n in staged if n.endswith('.md')));names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/return-interval-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,full_interval_fd_columns=[139],full_interval_direction139_admitted=True,independent_all_step_propagation=False,charge_root_basis_admitted=False,period_map_admitted=False,adaptive_derivative_admitted=False,continuous_event_derivative_admitted=False,independent_roots=0,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,physical_cards_changed=False,new_library_compile=False,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=links)

def main():
    try:report=audit()
    except Exception:
        report=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_return_interval.py').read_text())
        try:audit();report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_return_interval_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_return_interval_qa_failure{k:02d}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('RETURN_QA',report['passed'],len(report['source_sha256']),len(report['private_input_sha256']),flush=True)
if __name__=='__main__':main()
