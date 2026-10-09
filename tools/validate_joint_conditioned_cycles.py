"""Audit conditioned cycle coverage, preserved history and observed drift scope."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from decimal import Decimal
from prepare_vco1_portable import ROOT,sha
from prepare_joint_conditioned_cycles import caller
from validate_mixer_on_native import native_source_identity
from joint_cycles_analysis import require
OUT='evidence/voice_joint_conditioned_cycles_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_joint_prefix_tests01.json';old=read(previous);before=read('evidence/voice_joint_conditioned_cycles_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous release')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_conditioned_cycles_runner.rs text eol=lf\n','exact new Rust bytes rule')
    require((ROOT/'tools/joint_conditioned_cycles_runner.rs').read_bytes()==caller().encode(),'four declared laboratory caller changes')
    native=read('evidence/voice_joint_conditioned_cycles_native01.json');reference=read('evidence/voice_joint_conditioned_cycles_reference01.json');history=read('evidence/voice_joint_history_cycles_reference01.json')
    for r in [native,reference,history]:
        require(r['passed'] and r['source_sha256']==r['source_sha256_after'],'passed unchanged measurement sources')
        for n,h in r['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
    require(history['private_input_sha256']==history['private_input_sha256_after'] and len(history['histories'])==2 and history['new_roots']==0 and not history['new_time_integration'],'retrospective scope')
    for n,h in history['private_input_sha256'].items():require(private[n]==h,'admitted historical input '+n)
    for p in history['histories']:require(len(p['events'])==2 and len(p['capacitor_changes'])==18 and not p['c1_quadrature_between_events_available'] and not p['steady_periodicity_admitted'],'retrospective phase and missing ledger scope')
    require(native['private_used_sha256']==native['private_used_sha256_after'],'frozen restore/library inputs')
    for n,h in native['private_used_sha256'].items():require(private[n]==h,'admitted private input '+n)
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler identity');require(not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'no new physical build/audio/SPICE')
    require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'],'caller build')
    require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['wall_s']<=3600 and native['goal_ticks']==2752512000,'campaign resources')
    require(native['remaining_interval_budgets']=={'65536':29991,'32768':43994} and [p['maximum_half_ticks'] for p in native['profiles']]==[65536,32768],'declared profiles and remaining budgets')
    for p in native['profiles']:require(p['exit_code']==0 and p['wall_s']<=1800 and not p['administrative_stop'] and p['minimum_free_bytes']>=native['reserve_bytes'],'completed profile/resource gates')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'new private output');private[o['path']]=o['sha256']
    for n,h in reference['input_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'analyzed private input '+n)
    aggregate=reference['aggregate'];require(len(aggregate['profiles'])==2 and len(aggregate['shared_clock_points'])==21,'two complete profiles and shared anchors')
    require(aggregate['frequency_refinement_cents']<=1 and max(aggregate['extrema_refinement_v'].values())<=.005,'frequency/extrema refinement')
    for p in aggregate['profiles']:
        require(p['segments']==2 and p['final_ticks']==2752512000 and p['restore_replays']==2 and p['endpoints']==2*p['intervals'] and p['intervals']<=(32000 if p['maximum_half_ticks']==65536 else 48000),'aggregate counts and coverage')
        require(p['max_lte']<=1 and max(p['max_bus_kcl_a'],p['max_c1_kcl_a'])<=1e-12 and Decimal(p['integrated_charge_relative'])<=Decimal('.002'),'aggregate electrical gates')
        require(len(p['measurements']['crossings'])==2 and not p['measurements']['steady_periodicity_admitted'],'two measured crossings, no settling claim')
    for p in aggregate['shared_clock_points']:require(Decimal(p['max_error_ratio'])<=1,'200-coordinate refinement')
    independent=reference['new_independent'];require(len(independent['root_checks'])==24 and sum(x['rows'] for x in independent['root_checks'])==9600 and len(independent['temporal_checks'])==8 and len(independent['current_checks'])==16,'independent new selected coverage')
    for x in independent['root_checks']:require(max(x['residual_gate_ratio'],x['correction_gate_ratio'])<=1,'independent roots as points')
    for x in independent['temporal_checks']:require(Decimal(x['error_ratio_decimal'])<=1,'selected LTE')
    for x in independent['current_checks']:require(Decimal(x['max_error_a'])<=Decimal.from_float(2e-11),'terminal current gate')
    require(len(reference['cycles'])==2 and reference['inherited_prefix_stage_rows']==4800,'observed cycle bank and cached prefix')
    for p in reference['cycles']:
        require(len(p['events'])==2 and len(p['capacitor_changes'])==18 and len(p['phase_state_difference'])==200 and Decimal(p['c1_integrated_balance_relative'])<=Decimal('.002'),'event/capacitor and C1 cycle coverage')
        require(p['phase_interpolation_is_observation'] and not p['steady_periodicity_admitted'],'phase diagnostic scope')
    for p in [*reference['cycles'],*history['histories']]:
        metric=p.get('nominal_panel',p.get('panel'));require(max(metric['cursor_kcl_max_a'],metric['c27_direction_max_a'],metric['thevenin_current_max_error_a'])<=1e-12 and metric['panel_thevenin_ohm']==39250. and metric['conditional_rc_time_s']==.3925 and not metric['conditional_rc_is_whole_voice_pole'],'nominal mean identity and conditional RC scope')
    require(len(reference['history_contrast'])==2 and all(p['histories_have_same_nominal_scene'] and p['neither_history_admits_settled_periodicity'] for p in reference['history_contrast']),'histories compared without promotion')
    require(reference['own_conditioned_cycles_admitted'] and not reference['steady_periodicity_admitted'] and not reference['global_settling_bound'] and not reference['independent_root_search'],'admission scope')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged output');names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-conditioned-cycles-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,inherited_test_count=248,native_test_count=0,covered_test_count=248,inherited_tests_reexecuted=False,new_independent_dynamic_rows=9600,new_independent_stage_points=48,new_independent_terminal_currents=48,inherited_prefix_dynamic_rows=4800,independent_roots=0,accepted_intervals=sum(p['intervals'] for p in aggregate['profiles']),published_half_steps=sum(p['endpoints'] for p in aggregate['profiles']),duration_per_profile_s=.00525,final_ticks=2752512000,checkpoint_seams=2,restore_replays=4,observed_cycles=2,chain_capacitors_per_observed_cycle=18,phase_interpolation_is_observation=True,retrospective_histories=2,nominal_panel_mean_identity_checked=True,conditional_rc_is_whole_voice_pole=False,conditioned_initial_root_bit_identical=True,conditioned_prefix_admitted=True,initialized_cycle_admitted=True,steady_periodicity_admitted=False,previous_loaded_cycle_admitted_under_original_history=True,own_joint_power_on=False,global_settling_bound=False,physical_cards_changed=False,full_voice_radau_admitted=False,physical_fidelity=False,real_time=False,heap_measured_this_block=False,lab_stack_bytes=33554432,new_audio=False,new_spice_processes=0,new_library_compile=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'])
def main():
    try:r=audit()
    except Exception:
        failure=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_conditioned_cycles.py').read_text())
        try:audit();failure['replay']='unexpected pass'
        except Exception:failure['replay']=traceback.format_exc()
        n=1
        while (ROOT/f'evidence/voice_joint_conditioned_cycles_qa_failure{n:02d}.json').exists():n+=1
        (ROOT/f'evidence/voice_joint_conditioned_cycles_qa_failure{n:02d}.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CONDITIONED_CYCLES_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),flush=True)
if __name__=='__main__':main()
