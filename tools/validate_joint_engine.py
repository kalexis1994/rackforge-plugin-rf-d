"""Audit temporal publication, measured checks and immutable electrical lineage."""
import base64,hashlib,json,re,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from validate_mixer_on_native import native_source_identity
OUT='evidence/voice_joint_engine_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
    if not ok:raise ValueError(msg)
def audit():
    previous='evidence/voice_joint_tests01.json';old=read(previous);snapshot=read('evidence/voice_joint_engine_before01.json')
    require(old['passed'] and sha(ROOT/previous)==snapshot['previous_qa_sha256'],'previous QA')
    saved={n:base64.b64decode(v) for n,v in snapshot['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    lib='crates/rf-d-circuit/src/lib.rs';require((ROOT/lib).read_bytes()==saved[lib]+b'\npub mod joint_engine;\n','additive engine export')
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/crates/rf-d-circuit/src/joint_engine.rs text eol=lf\n/crates/rf-d-circuit/tests/joint_engine.rs text eol=lf\n','exact new Rust bytes')
    native=read('evidence/voice_joint_engine_native01.json');reference=read('evidence/voice_joint_engine_reference01.json')
    for report in [native,reference]:
        require(report['passed'] and report['source_sha256']==report['source_sha256_after'],'passed unchanged sources')
        for n,h in report['source_sha256'].items():require(sha(ROOT/n)==h,'measured input '+n)
    require(not native['replays'] and len(native['commands'])==3 and all(c['exit_code']==0 for c in native['commands']),'native processes')
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler identity')
    require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_build_bytes'] and native['wall_s']<=native['process_budget_s'],'resource contract')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'measured output');private[o['path']]=o['sha256']
    stdout=native['commands'][-1]['stdout']
    for marker in ['3 passed; 0 failed','invalid_targets=2,invalid_checkpoints=6,budget_rollback=1','accepted_allocations=0,invalid_target_allocations=0','restore_replays=4,target_ticks=1048576','AttemptLimit(LocalError(17397.135739361005))']:require(marker in stdout,'marker '+marker)
    profiles=re.findall(r'ENGINE_PROFILE,mask=(\d),half_max=(\d+),pairs=(\d+),retries=(\d+),ticks=(\d+)',stdout)
    require(len(profiles)==4 and [(int(m),int(h),int(n),int(t)) for m,h,n,r,t in profiles]==[(0,65536,17,1048576),(0,32768,23,1048576),(1,65536,17,1048576),(1,32768,23,1048576)],'four exact-clock profiles')
    metrics=re.search(r'ENGINE_TRAJECTORY,profiles=4,accepted_pairs=80,max_lte=([^,]+),max_bus_a=([^,]+),max_global_ratio=([^,]+),',stdout);require(metrics is not None,'metrics')
    lte,bus,global_error=map(float,metrics.groups());require(lte<=1 and bus<=1e-12 and global_error<=1,'measured temporal/refinement/balance gates')
    require(reference['native_candidate_points_used'] and not reference['independent_root_solve'],'independence scope')
    require(len(reference['root_checks'])==12 and sum(c['rows'] for c in reference['root_checks'])==4800 and len(reference['temporal_checks'])==4,'selected stage coverage')
    for c in reference['root_checks']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'independent physical equations')
    from decimal import Decimal
    for c in reference['temporal_checks']:require(Decimal(c['error_ratio_decimal'])<=1,'independent temporal difference')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'complete staged release')
    names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-engine-release/v1',passed=True,base_commit=snapshot['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,
        inherited_test_count=245,native_test_count=3,covered_test_count=248,inherited_tests_reexecuted=False,
        trajectory_profiles=4,accepted_intervals=80,published_half_steps=160,duplicate_restore_continuations=4,simulated_duration_per_profile_s=1048576*(125e-9/65536),final_ticks=1048576,
        max_local_error_ratio=lte,max_bus_kcl_a=bus,max_same_clock_refinement_ratio=global_error,restore_replays=4,
        invalid_targets=2,invalid_checkpoints=6,temporal_budget_rollback_cases=1,
        independent_stage_points=24,independent_residual_rows=4800,independent_temporal_comparisons=4,independent_roots=0,native_candidate_points_used=True,
        heap_allocations_measured=0,heap_measurement_scope='one minimum-step acceptance and one invalid-target rejection',lab_stack_bytes=33554432,
        vco_active_coupling_admitted_locally=True,joint_temporal_engine_admitted_locally=True,joint_trajectory=True,own_joint_startup=False,first_coupled_reset_admitted=False,full_voice_radau_admitted=False,
        physical_cards_changed=False,physical_fidelity=False,real_time=False,new_audio=False,new_spice_processes=0,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],long_note_admitted_locally=False)
def main():
    result=audit();(ROOT/OUT).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('ENGINE_QA',result['passed'],'sources',len(result['source_sha256']),'private',len(result['private_input_sha256']),'covered',result['covered_test_count'])
if __name__=='__main__':main()
