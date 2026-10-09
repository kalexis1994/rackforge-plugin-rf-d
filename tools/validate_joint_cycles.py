"""Audit preserved prefix, exact continuation and first loaded-cycle admission."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from decimal import Decimal
from prepare_vco1_portable import ROOT,sha
from prepare_joint_cycles_resume import continuation_source
from validate_mixer_on_native import native_source_identity
from joint_cycles_analysis import require,GOAL,TICK
OUT='evidence/voice_joint_cycles_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_joint_engine_tests01.json';old=read(previous);snapshot=read('evidence/voice_joint_cycles_before01.json')
    require(old['passed'] and sha(ROOT/previous)==snapshot['previous_qa_sha256'],'previous QA')
    saved={n:base64.b64decode(v) for n,v in snapshot['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    lib='crates/rf-d-circuit/src/lib.rs';require((ROOT/lib).read_bytes()==saved[lib]+b'\npub mod joint_currents;\n','additive observer export')
    rules=b'\n/crates/rf-d-circuit/src/joint_currents.rs text eol=lf\n/tools/joint_cycles_runner.rs text eol=lf\n/tools/joint_cycles_resume_runner.rs text eol=lf\n'
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+rules,'exact new Rust bytes')
    extension=read('evidence/voice_joint_cycles_extension01.json');resource=read('evidence/voice_joint_cycles_resource01.json')
    native=read('evidence/voice_joint_cycles_native01.json');paused=read('evidence/voice_joint_cycles_resume01.json');resume=read('evidence/voice_joint_cycles_resume02.json');aggregate=read('evidence/voice_joint_cycles_continuations02.json')
    analysis=read('evidence/voice_joint_cycles_analysis01.json');reference=read('evidence/voice_joint_cycles_reference01.json')
    label=read('evidence/voice_joint_cycles_time_label01.json');require(label['passed'] and label['exact_ticks']==1760362240 and label['correct_ms']=='3.35762451171875' and not label['binary_state_changed'] and not label['numerical_gates_changed'],'document label correction, clock unchanged')
    for n,h in label['source_sha256'].items():require(sha(ROOT/n)==h,'preserved documentary correction input '+n)
    require(not native['passed'] and [p['exit_code'] for p in native['profiles']]==[0,1],'preserved original administrative stop')
    require('ADMINISTRATIVE_BUDGET' in native['profiles'][1]['stderr'] and 'ENGINE_REJECT' not in native['profiles'][1]['stderr'] and not native['replays'],'cooperative stop, no physics rejection')
    require('failed_source_text' in native and 'replay_pending' in native,'failed process evidence preserved')
    require(resource['completed_coarse_stderr_sha256']==sha(ROOT/'references-local/joint-cycles01/65536/stderr.txt') and not resource['physical_or_numerical_gates_changed'],'measured resource decision')
    require(extension['previous_receipt_sha256']==sha(ROOT/'evidence/voice_joint_cycles_native01.json'),'frozen parent receipt')
    require(base64.b64decode(extension['before_base64']['tools/joint_cycles_runner.rs'])==(ROOT/'tools/joint_cycles_runner.rs').read_bytes(),'original caller preserved')
    require((ROOT/'tools/joint_cycles_resume_runner.rs').read_bytes()==continuation_source().encode(),'only declared continuation changes')
    require(extension['aggregate_crossing_gate']==extension['aggregate_restore_gate']==2 and extension['new_process_budget_s']==1800,'aggregate gates and resource amendment')
    require(sha(ROOT/extension['cached_library'])==extension['cached_library_sha256'],'same compiled physical library')
    require(not paused['passed'] and paused['profiles'][0]['exit_code']==1 and paused['profiles'][0]['administrative_stop'] and 'ADMINISTRATIVE_BUDGET' in paused['profiles'][0]['stderr'] and 'ENGINE_REJECT' not in paused['profiles'][0]['stderr'],'preserved disk stop')
    require(paused['profiles'][0]['minimum_free_bytes']<paused['reserve_bytes'],'resource guard detected reserve crossing')
    require(aggregate['passed'] and aggregate['exact_seams'] and aggregate['failed_segments_preserved'] and aggregate['resource_guard_interruptions']==1 and not aggregate['numerical_gates_changed'],'admitted stitched history, administrative failure retained')
    for report in [native,paused,resume,aggregate,analysis,reference]:
        if report is not native and report is not paused:require(report['passed'],'new admission report')
        require(report['source_sha256']==report['source_sha256_after'],'unchanged measured sources')
        for n,h in report['source_sha256'].items():require(sha(ROOT/n)==h,'measured input '+n)
        for n,h in report.get('input_sha256',{}).items():require(sha(ROOT/n)==h,'analysis input '+n)
    for report in [native,paused,resume]:
        require(sha(Path(report['compiler']['path']))==report['compiler']['sha256'],'compiler identity')
        require(all(c['exit_code']==0 for c in report['commands']) and not report['replays'],'native build identity')
        require(report['available_free_bytes']>=report['reserve_bytes']+report['estimated_output_bytes'] and report['wall_s']<=report['global_budget_s'],'resource preflight/elapsed')
        for p in report['profiles']:
            if report is not paused:require(p['minimum_free_bytes']>=report['reserve_bytes'],'completed process or original prefix reserve')
        for o in report['outputs']:require(sha(ROOT/o['path'])==o['sha256'] and (ROOT/o['path']).stat().st_size==o['bytes'],'immutable measured output');private[o['path']]=o['sha256']
    require(paused['preserved_prefix_ticks']==515440640 and paused['preserved_prefix_intervals']==7875 and paused['remaining_interval_budget']==40125,'first exact prefix and remaining interval budget')
    require(resume['preserved_prefix_ticks']==1760362240 and resume['preserved_prefix_intervals']==28242 and resume['remaining_interval_budget']==19758,'second exact prefix and remaining interval budget')
    require(len(resume['profiles'])==1 and resume['profiles'][0]['exit_code']==0 and not resume['profiles'][0]['administrative_stop'],'complete fine continuation')
    require('strip=symbols' in paused['commands'][0]['command'] and extension['strip_only_debug_metadata'],'stripped caller, unchanged physical library')
    require(not resume['commands'] and resume['cached_caller_sha256']==sha(Path(paused['profiles'][0]['command'][0])),'same caller, no new compilation')
    profiles=analysis['profiles'];require(len(profiles)==2 and [p['maximum_half_ticks'] for p in profiles]==[65536,32768],'two temporal resolutions')
    for p in profiles:
        require(p['final_ticks']==GOAL and p['restore_replays']==2 and len(p['measurements']['crossings'])>=2,'cycle, full duration and restore coverage')
        require(p['endpoints']==2*p['intervals'] and p['max_lte']<=1 and p['max_bus_kcl_a']<=1e-12 and p['max_c1_kcl_a']<=1e-12,'local gates')
        require(Decimal(p['integrated_charge_relative'])<=Decimal('.002') and not p['measurements']['steady_periodicity_admitted'],'charge and transient scope')
    require(len(analysis['shared_clock_points'])==21 and max(Decimal(c['max_error_ratio']) for c in analysis['shared_clock_points'])<=1,'all 200 shared-clock coordinates')
    require(analysis['frequency_refinement_cents']<=1 and max(analysis['extrema_refinement_v'].values())<=.005,'frequency and waveform refinement')
    roots=reference['root_checks'];temporal=reference['temporal_checks'];currents=reference['current_checks']
    require(len(roots)==30 and len(temporal)==10 and len(currents)==20,'selected full/mid/end coverage, including both continuation starts')
    require(not reference['coarse_only'] and reference['cached_coarse_receipt']=='evidence/voice_joint_cycles_coarse_reference01.json','same checked coarse results, no duplicate count')
    for c in roots:require(c['rows']==400 and c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent stage equations')
    for c in temporal:require(Decimal(c['error_ratio_decimal'])<=1,'independent selected LTE')
    for c in currents:require(Decimal(c['max_error_a'])<=Decimal.from_float(2e-11),'independent C1 terminal currents')
    require(reference['native_candidate_points_used'] and not reference['independent_root_solve'] and reference['new_spice_processes']==0,'independence scope')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'complete staged release')
    names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-cycles-release/v1',passed=True,base_commit=snapshot['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,
        inherited_test_count=248,native_test_count=0,covered_test_count=248,inherited_tests_reexecuted=False,
        trajectory_profiles=2,accepted_intervals=sum(p['intervals'] for p in profiles),published_half_steps=sum(p['endpoints'] for p in profiles),duplicate_restore_continuations=4,
        simulated_duration_per_profile_s=GOAL*TICK,final_ticks=GOAL,preserved_prefix_ticks=[paused['preserved_prefix_ticks'],resume['preserved_prefix_ticks']],exact_continuation_seams=2,administrative_stops_preserved=2,resource_guard_interruptions=1,physical_solver_failures=0,documentary_clock_label_corrected=True,
        max_local_error_ratio=max(p['max_lte'] for p in profiles),max_bus_kcl_a=max(p['max_bus_kcl_a'] for p in profiles),max_c1_kcl_a=max(p['max_c1_kcl_a'] for p in profiles),max_same_clock_refinement_ratio=str(max(Decimal(c['max_error_ratio']) for c in analysis['shared_clock_points'])),
        frequency_refinement_cents=analysis['frequency_refinement_cents'],extrema_refinement_v=analysis['extrema_refinement_v'],restore_replays=4,
        independent_stage_points=2*len(roots),independent_residual_rows=sum(c['rows'] for c in roots),independent_temporal_comparisons=len(temporal),independent_terminal_current_observations=3*len(currents),independent_roots=0,native_candidate_points_used=True,
        integrated_charge_scope='native Kahan Radau-stage quadrature per segment, independently compared to total compensated C1 charge difference; not an independent reconstruction of every stage current',
        heap_allocations_measured_this_block=False,lab_stack_bytes=33554432,measured_wall_s=sum(p['wall_s'] for p in native['profiles'])+paused['profiles'][0]['wall_s']+resume['profiles'][0]['wall_s'],resource_reserve_crossing_preserved=paused['profiles'][0]['minimum_free_bytes'],
        vco_active_coupling_admitted_locally=True,joint_temporal_engine_admitted_locally=True,joint_trajectory=True,own_joint_startup=False,first_coupled_reset_admitted=True,first_coupled_cycle_admitted=True,full_voice_radau_admitted=False,
        physical_cards_changed=False,physical_fidelity=False,real_time=False,new_audio=False,new_spice_processes=0,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],long_note_admitted_locally=False)

def main():
    try:result=audit()
    except Exception:
        failure=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_cycles.py').read_text())
        try:audit();failure['replay']='unexpected pass'
        except Exception:failure['replay']=traceback.format_exc()
        n=1
        while (ROOT/f'evidence/voice_joint_cycles_qa_failure{n:02d}.json').exists():n+=1
        (ROOT/f'evidence/voice_joint_cycles_qa_failure{n:02d}.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf8',newline='\n')
        raise
    (ROOT/OUT).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('CYCLES_QA',result['passed'],'sources',len(result['source_sha256']),'private',len(result['private_input_sha256']),'rows',result['independent_residual_rows'])
if __name__=='__main__':main()
