"""Audit own-history binding, standalone render, WAV adaptation and frozen lineage."""
import base64,hashlib,json,shutil,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_conditioned_recipe import generated_seed,ATTR,EXPORT
from extend_conditioned_recipe import fine_seed,FINE,HIST_ATTR
from joint_cycles_analysis import require
from run_conditioned_recipe import compare

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_conditioned_portable_tests01.json';old=read(previous)
    before=read('evidence/voice_conditioned_recipe_before01.json')
    require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'admitted base')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base HEAD')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR+HIST_ATTR,'declared Rust byte rules')
    require((ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==saved['crates/rf-d-circuit/src/lib.rs']+EXPORT,'additive recipe export')
    for n in ['docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:require((ROOT/n).read_bytes().startswith(saved[n]),'historical documentation prefix')
    require((ROOT/'README.md').read_bytes().startswith(saved['README.md'].replace(b'voice_conditioned_portable_tests01.json',b'voice_conditioned_recipe_tests01.json')),'README declared QA replacement and prefix')
    extra,records=fine_seed();require((ROOT/'crates/rf-d-circuit/src/conditioned_recipe_seed.rs').read_text(encoding='utf8')==generated_seed()+extra and (ROOT/FINE).read_text(encoding='utf8')==extra,'four own histories from published states')
    names=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'evidence').glob('voice_conditioned_recipe_*.json') if p.name not in ['voice_conditioned_recipe_before01.json','voice_conditioned_recipe_reference01.json','voice_conditioned_recipe_tests01.json'])
    receipts={n:read(n) for n in names};historic=set()
    for r in receipts.values():
        for key in ['failed_source_base64','before_source_base64']:
            for n,v in r.get(key,{}).items():historic.add((n,hashlib.sha256(base64.b64decode(v)).hexdigest()))
    failures={'evidence/voice_conditioned_recipe_conditioned_recipetests01.json','evidence/voice_conditioned_recipe_conditioned_recipetests02.json','evidence/voice_conditioned_recipe_native01.json'}
    def current_or_saved(n,h):require(sha(ROOT/n)==h or (n,h) in historic,'measured/historical source '+n)
    for name,r in receipts.items():
        require(r.get('passed') is (name not in failures),'expected receipt outcome '+name)
        for n,h in r.get('source_sha256',{}).items():current_or_saved(n,h)
        for n,h in r.get('repaired_source_sha256',{}).items():current_or_saved(n,h)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable measured sources')
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable measured private')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private use '+n);private[n]=h
        for output in r.get('outputs',[])+r.get('files',[]):
            n,h=output['path'],output['sha256'];require(sha(ROOT/n)==h,'new output '+n);private[n]=h
        if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
    failed=read('evidence/voice_conditioned_recipe_conditioned_recipetests01.json')
    require(len(failed['commands'])==2 and failed['commands'][0]['stderr']==failed['commands'][1]['stderr'] and 'error[E0277]' in failed['commands'][0]['stderr'],'preserved Debug compile failure/replay')
    failed=read('evidence/voice_conditioned_recipe_conditioned_recipetests02.json');a,b=failed['commands'][1:]
    require(a['exit_code']==b['exit_code']==3221225725 and a['stdout']==b['stdout'] and all('overflowed its stack' in c['stderr'] for c in [a,b]),'preserved test-worker stack failure/replay')
    stack=read('evidence/voice_conditioned_recipe_stack_repair01.json')
    require(not stack['declared_budget_increased'] and stack['lab_stack_bytes']==33554432 and not stack['library_changed'] and not stack['numerical_gates_changed'],'activate existing worker budget only')
    failed=read('evidence/voice_conditioned_recipe_native01.json')
    replay=read('evidence/voice_conditioned_recipe_rejection_replay01.json')
    require(len(failed['profiles'])==2 and failed['profiles'][0]['all_exported_bits_identical'] and 'full exported bits j7.bin' in failed['failure'] and 'full exported bits j7.bin' in failed['adapter_replay'],'rejected cross-resolution history')
    require(replay['identical_native_replay'] and 'full exported bits j7.bin' in replay['repeated_adapter_failure'],'unchanged wrong-history native replay')
    for name in ['j7.bin','steps.bin','grids.bin','events.txt']:
        require((ROOT/f'references-local/conditioned-recipe-render01/1-524288/{name}').read_bytes()==(ROOT/f'references-local/conditioned-recipe-render01/rejected-replay-1-524288/{name}').read_bytes(),'preserved wrong-history output '+name)
    repair=read('evidence/voice_conditioned_recipe_history_repair01.json')
    require(repair['initial_histories']==4 and repair['resolution_specific_histories'] and repair['previous_seed_prefix_preserved'] and not repair['numerical_gates_changed'] and not repair['solver_or_topology_changed'] and repair['new_temporal_duration_s']==0,'history binding repair')
    for i in [1,2]:
        library=read(f'evidence/voice_conditioned_recipe_library{i:02d}.json')
        require(library['new_library_compile'] and not library['new_cargo_cache'] and len(library['commands'])==1 and library['commands'][0]['exit_code']==0 and library['commands'][0]['wall_s']<=120,'bounded own library build')
    for name,count in [('conditioned_recipe',3),('conditioned_portable',4)]:
        r=read(f'evidence/voice_conditioned_recipe_{name}tests04.json')
        require(r['native_test_count']==count and r['identical_replay'] and len(r['commands'])==3 and all(c['exit_code']==0 and c['wall_s']<=600 for c in r['commands']),'final native tests/replay')
        require(all(f'test result: ok. {count} passed; 0 failed;' in c['stdout'] for c in r['commands'][1:]),'executed final tests')
        if count==4:
            require(all('allocations=0' in c['stdout'] and 'workspace=3378208,engine=4800,checkpoint=4800' in c['stdout'] for c in r['commands'][1:]),'remeasured heap/storage')
    native=read('evidence/voice_conditioned_recipe_native02.json')
    require(native['identical_replay'] and len(native['profiles'])==4 and len(native['replays'])==1 and native['replays'][0]['exit_code']==0 and native['wall_s']<=4000 and not native['independent_graph_reexecuted'],'finite final native campaign')
    require(native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and all(p['exit_code']==0 and p['wall_s']<=990 for p in native['profiles']),'compile and profile gates')
    require([p['accepted_steps'] for p in native['profiles']]==[3020,3704,2987,3674],'final accepted calendar')
    for p in native['profiles']:
        tag=p['tag'];expected=compare(ROOT/f'references-local/conditioned-recipe-render02/{tag}',ROOT/f'references-local/conditioned-portable-cycle01/{tag}')
        require(all(p[k]==v for k,v in expected.items()),'reaudit complete exported bits')
    for name in ['j7.bin','steps.bin','grids.bin','events.txt']:
        require((ROOT/f'references-local/conditioned-recipe-render02/1-524288/{name}').read_bytes()==(ROOT/f'references-local/conditioned-recipe-render02/replay-1-524288/{name}').read_bytes(),'final native exact replay '+name)
    listening=read('evidence/voice_conditioned_recipe_listening01.json');cli=read('evidence/voice_conditioned_recipe_cli01.json')
    require(listening['identical_derived_replay'] and len(listening['files'])==4 and not any(listening[k] for k in ['dc_removed','peak_normalization','fades','repetition','real_time','physical_fidelity']),'scoped finite WAVs')
    require(listening['sample_rate_hz']==48000 and listening['cutoff_hz']==18000 and listening['volts_per_full_scale']==.01 and listening['constant_extension_only_in_filter'] and listening['simulated_window_s']==.003004 and listening['new_extended_duration_s']==0,'fixed adaptation boundary')
    for f in listening['files']:
        require(f['stretch'] in [1,100] and f['frames']==(144 if f['stretch']==1 else 14419) and f['quadrature_max_error_v']<=.25*.01/32767 and 0<f['peak_fs']<1 and not f['repeated'] and f['new_circuit_duration_s']==0,'audio duration/quadrature/level gates')
    require(cli['native_python_test_count']==2 and cli['user_cli_wav_identical'] and cli['existing_output_rejected_without_mutation'],'user CLI and adapter tests')
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']))
    require(size<=32*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'all failed and accepted outputs within budget/reserve')
    return dict(passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),
        protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),
        private_input_sha256=private,new_private_bytes=size,lab_collection_verified=True,
        public_conditioned_recipe_admitted=True,standalone_offline_render_admitted=True,
        resolution_specific_own_histories=4,simulated_window_s=.003004,new_extended_duration_s=0,
        accepted_steps=13385,fine_endpoints=26770,grid_states_compared=48,
        compared_state_bit_fields=48*458,compared_observable_bit_fields=5*(26770+4),
        replayed_accepted_steps=3704,independent_equations_reexecuted=0,
        independent_graph_reexecuted=False,new_library_compiles=2,new_cargo_cache=False,
        native_wall_s=native['wall_s'],native_test_count=7,new_native_test_definitions=3,
        previously_defined_tests_reexecuted=4,inherited_test_count=248,covered_test_count=255,
        all_inherited_tests_reexecuted=False,native_python_test_count=2,
        heap_remeasured=True,processing_allocations=0,workspace_bytes=3378208,
        engine_bytes=4800,checkpoint_bytes=4800,lab_stack_bytes=33554432,
        deadline_measured=False,new_audio=True,new_audio_files=4,
        raw_observation_node='J7/global194',time_stretch_is_inspection=True,
        public_wav_cli_admitted=True,preserved_failures=3,numerical_gates_changed=False,
        full_contour_from_silence_admitted=False,new_spice_processes=0,
        periodicity_admitted=False,physical_fidelity=False,real_time=False)

def main():
    r=audit();write('evidence/voice_conditioned_recipe_reference01.json',r)
    print('RECIPE_REFERENCE',r['passed'],r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
