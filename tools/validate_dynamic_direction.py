"""Release gates for a tested direction and one measured candidate, not a full map."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from prepare_dynamic_direction import ATTR
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links

OUT='evidence/voice_dynamic_direction_tests01.json'
COUNTS=dict(augmented_root_count=6,augmented_rows=1308,own_native_step_solves=212720,serial_prefix_step_solves=320,serial_prefix_bit_coordinates=640000,independent_nonlinear_rows=40000,independent_nonlinear_points=100,selected_points_per_history=20,stored_points_per_history=81,own_event_observations=10)

def read(name):return json.loads((ROOT/name).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_conditioned_return_utf8_tests01.json';old=read(previous);before=read('evidence/voice_dynamic_direction_before01.json');require(old['passed'] and sha(ROOT/previous)==before['previous_qa_sha256'],'previous release');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base unchanged');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for name,digest in old['source_sha256'].items():require(hashlib.sha256(saved[name] if name in saved else (ROOT/name).read_bytes()).hexdigest()==digest,'protected source '+name)
    private=dict(old['private_input_sha256'])
    for name,digest in private.items():require(sha(ROOT/name)==digest,'protected private '+name)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'only new caller attributes');header=(ROOT/'tools/joint_charge_corrected_runner.rs').read_text(encoding='utf8').split('fn run()->Result<(),String>')[0];require((ROOT/'tools/joint_dynamic_direction_runner.rs').read_bytes()==(header+(ROOT/'tools/dynamic_direction_tail.rs').read_text(encoding='utf8')).encode(),'frozen conditioner prefix')
    inputs=read('evidence/voice_dynamic_direction_inputs01.json');require(inputs['passed'] and inputs['steps']==42544 and len(inputs['points'])==20 and sha(ROOT/inputs['path'])==inputs['sha256'],'frozen direction input');private[inputs['path']]=inputs['sha256']
    for name,digest in inputs['source_sha256'].items():require(sha(ROOT/name)==digest,'preparation source')
    for name,digest in inputs['private_used_sha256'].items():require(private[name]==digest and sha(ROOT/name)==digest,'original base input')
    native=read('evidence/voice_dynamic_direction_native01.json');require(native['passed'] and native['source_sha256']==native['source_sha256_after'] and native['private_used_sha256']==native['private_used_sha256_after'],'stable native');require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'] and not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'frozen compiler/library')
    for name,digest in native['source_sha256'].items():require(sha(ROOT/name)==digest,'native source')
    for name,digest in native['private_used_sha256'].items():require(private[name]==digest and sha(ROOT/name)==digest,'native input')
    for output in native['outputs']:require(sha(ROOT/output['path'])==output['sha256'],'native output');private[output['path']]=output['sha256']
    require(native['workers']==4 and native['worker_stack_bytes']==native['lab_stack_bytes']==33554432 and native['serial_prefix_steps']==64 and native['processor_count']>=4 and native['initial_available_memory_bytes']>=1024**3,'worker resources');require(native['reserve_bytes']==1024**3 and native['estimated_output_bytes']==64*1024**2 and native['minimum_free_bytes']>=native['reserve_bytes'] and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['wall_s']<=3560 and sum(o['bytes'] for o in native['outputs'])<=native['estimated_output_bytes'],'bounded resources');require(len(native['commands'])==2 and not native['replays'],'successful exact commands')
    for k,c in enumerate(native['commands']):require(c['exit_code']==0 and not c['administrative_stop'] and c['wall_s']<=(120 if k==0 else 3400),'command budget')
    ref=read('evidence/voice_dynamic_direction_reference01.json');require(ref['passed'] and ref['source_sha256']==ref['source_sha256_after'] and ref['wall_s']<=300,'stable reference')
    for name,digest in ref['source_sha256'].items():require(sha(ROOT/name)==digest,'reference source')
    for name,digest in ref['input_sha256'].items():require(private[name]==digest and sha(ROOT/name)==digest,'reference input')
    for k,v in COUNTS.items():require(ref[k]==v,'coverage '+k)
    require(ref['full_direction_fd_admitted'] and not any(ref[k] for k in ['all_target_fd_admitted','independent_all_step_propagation','period_map_admitted','steady_periodicity_admitted','adaptive_derivative_admitted','physical_fidelity','real_time','new_audio']) and ref['independent_roots']==0,'direction scope')
    algebra=ref['algebra'];require(algebra['rank']==16 and algebra['reconstruction_error']<=1e-12 and algebra['orthogonality_error']<=1e-12 and algebra['independent_direction_error_v']<=1e-10 and float(algebra['normal_equation_error_v'])<=1e-12 and float(algebra['null_direction_projection_v'])<=1e-12,'independent algebra')
    roots=[ref['base_root'],*[h['root_report'] for h in ref['histories']]];require(len(roots)==6 and len(ref['histories'])==5,'roots/history coverage')
    for root in roots:require(root['rows']==218 and float(root['residual_gate_ratio'])<=1 and root['correction_gate_ratio']<=1 and float(root['max_charge_voltage_error_v'])<=1e-11 and float(root['phase_error_v'])<=1e-11,'augmented root gates')
    for history in ref['histories']:
        require(len(history['equations'])==20 and [r['step'] for r in history['equations']]==inputs['points'] and len(history['events'])==2 and history['drift_observation']['max_ratio']<=1,'history coverage')
        for row in history['equations']:require(row['rows']==400 and row['residual_gate_ratio']<=1 and row['correction_gate_ratio']<=1,'independent nonlinear gate')
        for event in history['events']:require(0<=event['alpha']<=1 and event['observation']['max_ratio']<=1,'own observer')
    require([row['scale'] for row in ref['nonlinear_fd']]==[1.,.5],'two FD sizes')
    for row in ref['nonlinear_fd']:
        require(all(row[k]['max_ratio']<=1 for k in ['root','period','drift','capacitors']) and len(row['stage_reports'])==20 and len(row['events'])==2,'direction FD')
        for stage in row['stage_reports']:require(stage['old']['max_ratio']<=1 and stage['stages']['max_ratio']<=1,'own full stages')
        for event in row['events']:require(event['state']['max_ratio']<=1 and event['time']['max_ratio']<=1,'own event FD')
    candidate=ref['candidate'];b=np.array(candidate['baseline_capacitor_drift_v']);c=np.array(candidate['capacitor_drift_v']);l2=float(np.linalg.norm(c)/np.linalg.norm(b));maximum=float(np.max(abs(c))/np.max(abs(b)));require(l2==candidate['l2_ratio'] and maximum==candidate['maximum_ratio'],'measured candidate metrics');improved=l2<=.5 and maximum<=.5 and abs(candidate['j7_drift_v'])<=abs(candidate['j7_baseline_drift_v']);require(improved==candidate['improvement_admitted'],'conditional improvement claim')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged release');names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={name:sha(ROOT/name) for name in sorted(names)}
    for name in staged:
        if name!=OUT:native_source_identity(name,sources[name],subprocess.check_output(['git','show',':'+name],cwd=ROOT))
    return dict(schema='rf-d/dynamic-direction-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**COUNTS,full_direction_fd_admitted=True,candidate_improvement_admitted=improved,all_target_fd_admitted=False,independent_roots=0,independent_all_step_propagation=False,period_map_admitted=False,steady_periodicity_admitted=False,adaptive_derivative_admitted=False,physical_fidelity=False,real_time=False,new_audio=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,new_library_compile=False,new_spice_processes=0,physical_cards_changed=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=local_links([name for name in staged if name.endswith('.md')]))

def main():
    try:report=audit()
    except Exception:
        report=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_dynamic_direction.py').read_text(encoding='utf8'))
        try:audit();report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_dynamic_direction_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_dynamic_direction_qa_failure{k:02d}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('DIRECTION_QA',report['passed'],report['candidate_improvement_admitted'],len(report['source_sha256']),len(report['private_input_sha256']))
if __name__=='__main__':main()
