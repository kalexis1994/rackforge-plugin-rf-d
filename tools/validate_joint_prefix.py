"""Release the conditioned 500-us prefix without admitting complete cycles."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from decimal import Decimal
from prepare_vco1_portable import ROOT,sha
from prepare_joint_prefix import caller
from validate_mixer_on_native import native_source_identity
from joint_cycles_analysis import require
OUT='evidence/voice_joint_prefix_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_joint_modes_tests01.json';old=read(previous);before=read('evidence/voice_joint_prefix_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous release')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_conditioned_prefix_runner.rs text eol=lf\n','exact Rust bytes rule')
    require((ROOT/'tools/joint_conditioned_prefix_runner.rs').read_bytes()==caller().encode(),'only three declared caller changes')
    native=read('evidence/voice_joint_prefix_native01.json');reference=read('evidence/voice_joint_prefix_reference01.json')
    for report in [native,reference]:
        require(report['passed'] and report['source_sha256']==report['source_sha256_after'],'passed unchanged measured inputs')
        for n,h in report['source_sha256'].items():require(sha(ROOT/n)==h,'measured input '+n)
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler identity');cached=native['cached_library'];require(private[cached['path']]==cached['sha256'],'frozen physical library')
    require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'],'caller compile without new library')
    require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['wall_s']<=700 and native['goal_ticks']==262144000,'campaign preflight and duration')
    require([p['maximum_half_ticks'] for p in native['profiles']]==[65536,32768],'two declared profiles')
    for p in native['profiles']:require(p['exit_code']==0 and p['wall_s']<=300 and not p['administrative_stop'] and p['minimum_free_bytes']>=native['reserve_bytes'],'completed profile/resources')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'new private output');private[o['path']]=o['sha256']
    for n,h in reference['input_sha256'].items():require(sha(ROOT/n)==h,'independent trace input '+n)
    require(reference['initial_root_bit_identical'] and len(reference['same_clock'])==2,'initial identity and shared clocks')
    for p in reference['same_clock']:require(Decimal(p['max_error_ratio'])<=1,'same-clock refinement')
    require(len(reference['profiles'])==2 and len(reference['root_checks'])==12 and sum(c['rows'] for c in reference['root_checks'])==4800 and len(reference['temporal_checks'])==4 and len(reference['current_checks'])==8,'selected independent coverage')
    for p in reference['profiles']:require(p['accepted_intervals']<=10000 and p['published_half_steps']==2*p['accepted_intervals'] and p['restore_replays']==1 and len(p['capacitor_change'])==18 and Decimal(p['c1_balance_relative'])<=Decimal('.002') and p['maximum_lte']<=1 and max(p['max_bus_kcl_a'],p['max_c1_kcl_a'])<=1e-12,'profile gates')
    for c in reference['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent stage equations')
    for c in reference['temporal_checks']:require(Decimal(c['error_ratio_decimal'])<=1,'independent selected LTE')
    for c in reference['current_checks']:require(Decimal(c['max_error_a'])<=Decimal.from_float(2e-11),'independent terminal currents')
    require(not reference['initialized_cycle_admitted'] and not reference['steady_periodicity_admitted'] and not reference['global_settling_bound'] and not reference['independent_root_search'],'scope')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged output');names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-prefix-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,inherited_test_count=248,native_test_count=0,covered_test_count=248,inherited_tests_reexecuted=False,independent_dynamic_rows=4800,independent_stage_points=24,independent_terminal_currents=24,independent_roots=0,accepted_intervals=sum(p['accepted_intervals'] for p in reference['profiles']),published_half_steps=sum(p['published_half_steps'] for p in reference['profiles']),duration_per_profile_s=.0005,final_ticks=262144000,restore_replays=2,conditioned_initial_root_bit_identical=True,conditioned_prefix_admitted=True,initialized_cycle_admitted=False,steady_periodicity_admitted=False,previous_loaded_cycle_admitted_under_original_history=True,joint_conditioned_dc_admitted_locally=True,own_joint_power_on=False,global_settling_bound=False,physical_cards_changed=False,full_voice_radau_admitted=False,physical_fidelity=False,real_time=False,heap_measured_this_block=False,lab_stack_bytes=33554432,new_audio=False,new_spice_processes=0,new_library_compile=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'])
def main():
    try:r=audit()
    except Exception:
        failure=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_prefix.py').read_text())
        try:audit();failure['replay']='unexpected pass'
        except Exception:failure['replay']=traceback.format_exc()
        n=1
        while (ROOT/f'evidence/voice_joint_prefix_qa_failure{n:02d}.json').exists():n+=1
        (ROOT/f'evidence/voice_joint_prefix_qa_failure{n:02d}.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('PREFIX_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),flush=True)
if __name__=='__main__':main()
