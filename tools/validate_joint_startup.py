"""Release identity and measured gates for constrained joint initialization."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from decimal import Decimal
from prepare_vco1_portable import ROOT,sha
from validate_mixer_on_native import native_source_identity
from joint_cycles_analysis import require
OUT='evidence/voice_joint_startup_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_joint_cycles_tests01.json';old=read(previous);before=read('evidence/voice_joint_startup_before01.json')
    require(old['passed'] and sha(ROOT/previous)==before['previous_qa_sha256'],'previous release')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==saved['crates/rf-d-circuit/src/lib.rs']+b'\npub mod joint_startup;\n','additive export')
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/crates/rf-d-circuit/src/joint_startup.rs text eol=lf\n/tools/joint_startup_runner.rs text eol=lf\n','new exact Rust bytes')
    native=read('evidence/voice_joint_startup_native01.json');reference=read('evidence/voice_joint_startup_reference01.json')
    for report in [native,reference]:
        require(report['passed'] and report['source_sha256']==report['source_sha256_after'],'passed unchanged measured inputs')
        for n,h in report['source_sha256'].items():require(sha(ROOT/n)==h,'measured input '+n)
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler identity')
    require(len(native['commands'])==3 and all(c['exit_code']==0 and c['wall_s']<=180 for c in native['commands']) and not native['replays'],'native execution')
    require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['minimum_free_bytes']>=native['reserve_bytes'] and native['wall_s']<=600,'sampled resource contract')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'new private output');private[o['path']]=o['sha256']
    # Same scene as the previous cycle caller, rather than a hidden parameter fit.
    extract=lambda n:(ROOT/n).read_text().split('fn scene()')[1].split('\nfn ')[0]
    require(extract('tools/joint_startup_runner.rs')==extract('tools/joint_cycles_runner.rs'),'nominal builder unchanged')
    require('INPUT_REJECTIONS,invalid_budgets=2,invalid_seed=1' in native['commands'][-1]['stdout'],'rejected invalid inputs')
    require(len(reference['dc_checks'])==2 and sum(c['rows'] for c in reference['dc_checks'])==400,'two conditioned DC points')
    for c in reference['dc_checks']:require(Decimal(c['residual_gate_ratio'])<=1 and c['correction_gate_ratio']<=1,'independent DC')
    require(reference['chain_g_gate_ratio']<=1 and reference['chain_c_gate_ratio']<=1 and len(reference['ac'])==5,'matrix and AC coverage')
    require([x['frequency_hz'] for x in reference['ac']]==[10.,100.,410.80175922051075,1000.,10000.],'declared frequency bank')
    for x in reference['ac']:require(x['reference_error_ratio']<=1 and x['max_residual_a']<=1e-10 and x['bus_error_v']<=1e-12,'independent AC gates')
    require(len(reference['local_modes'])==18 and reference['algebraic_coordinate_count']==50,'all finite charge modes, no algebraic pole count')
    for m in reference['local_modes']:require(m['reduced_residual']<=1e-8 and m['exterior_residual']<=1e-8,'mode reconstruction')
    require(len(reference['capacitor_initialization'])==18,'all initialized linear capacitors')
    require(len(reference['release_profiles'])==2 and [int(p[0]) for p in reference['release_profiles']]==[65536,32768],'short release at two resolutions')
    for p in reference['release_profiles']:require(int(p[1])<=256 and p[2]<=1 and p[3]<=1e-12 and p[4]<=1e-12,'native release gates')
    require(len(reference['release_stage_checks'])==12 and sum(c['rows'] for c in reference['release_stage_checks'])==4800 and len(reference['release_lte_decimal'])==4,'first/last selected stages')
    for c in reference['release_stage_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent released equations')
    require(all(Decimal(v)<=1 for v in reference['release_lte_decimal']) and Decimal(reference['release_final_error_ratio'])<=1,'independent temporal comparisons')
    require(reference['native_candidate_points_used'] and not reference['independent_root_solve'] and not reference['global_settling_bound'],'scope')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged output')
    names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-startup-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,
        inherited_test_count=248,native_test_count=0,covered_test_count=248,inherited_tests_reexecuted=False,conditioned_dc_points=2,independent_dc_rows=400,independent_stage_points=24,independent_dynamic_rows=4800,independent_roots=0,
        accepted_release_intervals=sum(int(p[1]) for p in reference['release_profiles']),published_release_half_steps=2*sum(int(p[1]) for p in reference['release_profiles']),release_duration_per_profile_s=2e-6,release_final_ticks=1048576,
        ac_frequencies=5,charge_modes=18,algebraic_coordinates=50,capacitors_initialized=18,joint_conditioned_dc_admitted_locally=True,joint_analytic_seed=False,free_joint_dc=False,constraint_removed_in_dynamic_engine=True,
        initialized_cycle_admitted=False,previous_loaded_cycle_admitted_under_original_history=True,own_joint_power_on=False,global_settling_bound=False,physical_cards_changed=False,full_voice_radau_admitted=False,physical_fidelity=False,real_time=False,
        resource_free_space_sampling='before and after each bounded subprocess, not continuous monitoring',heap_measured_this_block=False,lab_stack_bytes=33554432,new_audio=False,new_spice_processes=0,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'])
def main():
    try:r=audit()
    except Exception:
        failure=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_startup.py').read_text())
        try:audit();failure['replay']='unexpected pass'
        except Exception:failure['replay']=traceback.format_exc()
        n=1
        while (ROOT/f'evidence/voice_joint_startup_qa_failure{n:02d}.json').exists():n+=1
        (ROOT/f'evidence/voice_joint_startup_qa_failure{n:02d}.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('STARTUP_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),flush=True)
if __name__=='__main__':main()
