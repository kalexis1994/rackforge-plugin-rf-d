"""Release identities and bounded scope for modal diagnostics/cache compression."""
import base64,hashlib,json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from validate_mixer_on_native import native_source_identity
from joint_cycles_analysis import require
OUT='evidence/voice_joint_modes_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_joint_startup_tests01.json';old=read(previous);before=read('evidence/voice_joint_modes_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    for n,h in old['private_input_sha256'].items():require(sha(ROOT/n)==h,'protected private '+n)
    report=read('evidence/voice_joint_modes_reference01.json');cache=read('evidence/voice_joint_cache_compression01.json')
    for r in [report,cache]:
        require(r['passed'] and r['source_sha256']==r['source_sha256_after'],'passed unchanged sources')
        for n,h in r['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
    require(report['new_native_processes']==report['new_spice_processes']==0 and not report['new_audio'] and not report['temporal_campaign_launched'],'no temporal campaign')
    require(report['charge_modes']==len(report['modes'])==18 and report['algebraic_coordinates']==50 and len(report['capacitors'])==18,'full modal/capacitor coverage')
    require(report['inverse_relative_residual']<=1e-10 and report['modal_vector_condition_2']>=1,'reported inverse conditioning')
    for m in report['modes']:
        require(m['reduced_residual']<=1e-8 and m['exterior_residual']<=1e-8,'eigenvector gates')
        require(len(m['capacitor_energy_fraction'])==18 and abs(sum(m['capacitor_energy_fraction'])-1)<=1e-12 and min(m['capacitor_energy_fraction'])>=0,'charge energy partition')
    require(len(report['ac'])==27 and report['ac'][0]['frequency_hz']==0 and report['ac'][-1]['frequency_hz']==1e6,'DC and wide AC')
    for x in report['ac']:require(max(x['reconstruction_gate_ratio'],x['weights_gate_ratio'],x['independent_gate_ratio'])<=1,'nodal complex transfer gates')
    require([x['time_s'] for x in report['step']]==[0.,1e-6,.001,.00525,.02,.1,.265,1.3],'analytic step times')
    for x in report['step']:require(x['max_physical_residual_a']<=1e-10 and x['bus_error_v']<=1e-12 and x['max_imaginary_v']<=1e-10,'step equation gates')
    require(report['step'][0]['max_incremental_sqrt_f_v']<=1e-10,'zero incremental charge at 0+')
    bound=report['local_envelope'];require(bound['linear_local_only'] and bound['formal_step_v']==.001 and bound['output_threshold_v']==1e-6 and bound['gain_threshold_v_per_v']==.001 and bound['envelope_v_per_v']<=.001,'explicit local threshold')
    require(not report['global_settling_bound'] and not report['initialized_cycle_admitted'] and not report['independent_root_search'] and not report['physical_cards_changed'],'local scope')
    require(cache['directories']==['tmp/vco1-portable-build01','tmp/vco1-portable-build02','tmp/vco1-portable-build03'] and len(cache['commands'])==3 and all(c['exit_code']==0 for c in cache['commands']),'exact maintenance scope')
    require(cache['deleted_files']==cache['moved_files']==0 and not cache['logical_bytes_changed'],'preserved evidence')
    require(cache['files_before'].keys()==cache['files_after'].keys(),'cache inventory')
    for n,a in cache['files_before'].items():
        b=cache['files_after'][n];require(a['sha256']==b['sha256']==old['private_input_sha256'][n] and a['bytes']==b['bytes'],'lossless compression '+n)
    require(cache['allocation_reclaimed_bytes']==cache['allocated_before_bytes']-cache['allocated_after_bytes'],'allocated-space accounting')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged output')
    names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-modes-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=old['private_input_sha256'],inherited_test_count=248,native_test_count=0,covered_test_count=248,inherited_tests_reexecuted=False,charge_modes=18,algebraic_coordinates=50,complex_ac_points=27,analytic_step_points=8,independent_roots=0,modal_vector_condition_2=report['modal_vector_condition_2'],local_linear_envelope_s=bound['time_s'],global_settling_bound=False,initialized_cycle_admitted=False,previous_loaded_cycle_admitted_under_original_history=True,joint_conditioned_dc_admitted_locally=True,physical_cards_changed=False,full_voice_radau_admitted=False,physical_fidelity=False,real_time=False,new_audio=False,new_spice_processes=0,new_native_processes=0,compressed_cache_files=len(cache['files_before']),cache_allocation_reclaimed_bytes=cache['allocation_reclaimed_bytes'],previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'])
def main():
    try:r=audit()
    except Exception:
        failure=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_modes.py').read_text())
        try:audit();failure['replay']='unexpected pass'
        except Exception:failure['replay']=traceback.format_exc()
        n=1
        while (ROOT/f'evidence/voice_joint_modes_qa_failure{n:02d}.json').exists():n+=1
        (ROOT/f'evidence/voice_joint_modes_qa_failure{n:02d}.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('MODES_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),flush=True)
if __name__=='__main__':main()
