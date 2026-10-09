"""Audit four new histories, preserved bytes, selected equations and ledgers."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from decimal import Decimal
from prepare_vco1_portable import ROOT,sha
from prepare_joint_seed_cycles import caller
from joint_cycles_analysis import require,checkpoint
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_joint_seed_cycles_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_joint_charge_seed_tests01.json';old=read(previous);before=read('evidence/voice_joint_seed_cycles_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous release')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    rail_before=read('evidence/voice_joint_seed_cycles_rail_before01.json');rail=read('evidence/voice_joint_seed_cycles_rail_reference01.json')
    saved.update({n:base64.b64decode(v) for n,v in rail_before['mutable_before_base64'].items()})
    require(rail['passed'] and rail['source_sha256']==rail['source_sha256_after'] and rail['physical_charge_checks']==72 and len(rail['native_root_checks'])==4 and rail['notation_only_correction'] and not rail['physical_cards_changed'] and not rail['new_time_integration'],'fixed-rail notation and physical charge checks')
    for n,h in rail['source_sha256'].items():require(sha(ROOT/n)==h,'rail check source '+n)
    name='docs/VOZ_CARGAS_SEMILLA_PROTOCOLO.md';require(hashlib.sha256(saved[name]).hexdigest()==rail_before['original_source_sha256'][name]==read('evidence/voice_joint_charge_seed_native02.json')['source_sha256'][name],'preserved measured protocol before notation repair')
    old_notation=rail_before['original_notation'];new_notation='v=Eᵀx en V, i en A; Q=C·(v−v_fijo) en C, con la referencia\ndel terminal fijo restada en la tensión física. Para riel constante,\nΔQ=C·Δv. [Aclaración y errata](VOZ_CARGAS_RIELES_NOTA.md).\nUna corriente positiva va de a a b.'
    require((ROOT/name).read_bytes()==saved[name].decode('utf8').replace(old_notation,new_notation).encode('utf8'),'only declared charge notation correction')
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_seed_cycles_runner.rs text eol=lf\n','lab Rust bytes rule');require((ROOT/'tools/joint_seed_cycles_runner.rs').read_bytes()==caller().encode(),'eight declared lab caller changes')
    compression=[]
    for n in [f'evidence/voice_joint_seed_cycles_compression{i:02d}.json' for i in range(1,5)]:
        r=read(n);require(r['passed'] and r['source_sha256']==r['source_sha256_after'] and r['deleted_files']==0 and r['moved_files']==0 and not r['logical_bytes_changed'],'transparent maintenance')
        for name,h in r['source_sha256'].items():require(sha(ROOT/name)==h,'maintenance source '+name)
        require(r['files_before'].keys()==r['files_after'].keys(),'maintenance inventory')
        for name,row in r['files_before'].items():require(row['sha256']==private[name]==r['files_after'][name]['sha256'] and row['bytes']==r['files_after'][name]['bytes'],'all old bytes preserved')
        compression.append(r)
    inputs=read('evidence/voice_joint_seed_cycles_inputs01.json');require(inputs['passed'] and len(inputs['outputs'])==4 and inputs['native_seed_sha256']==sha(ROOT/inputs['native_seed_source']),'exact admitted roots')
    for n,h in inputs['source_sha256'].items():require(sha(ROOT/n)==h,'input builder source')
    for r in inputs['outputs']:
        require(sha(ROOT/r['path'])==r['sha256'],'root input');cp=checkpoint((ROOT/r['path']).read_bytes());require(cp['ticks']==0 and cp['maximum']==r['maximum_half_ticks'] and cp['proposal']==2*cp['maximum'],'root clock/proposal');private[r['path']]=r['sha256']
    native=read('evidence/voice_joint_seed_cycles_native01.json');reference=read('evidence/voice_joint_seed_cycles_reference01.json')
    for r in [native,reference]:
        require(r['passed'] and r['source_sha256']==r['source_sha256_after'],'passed unchanged measurement sources')
        for n,h in r['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
    require(native['private_used_sha256']==native['private_used_sha256_after'],'frozen native inputs')
    for n,h in native['private_used_sha256'].items():require(private[n]==h,'admitted library/initial checkpoint '+n)
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'] and not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'build/scope')
    require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'] and native['wall_s']<=7200,'bounded caller build/campaign')
    require(native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and len(native['profiles'])==4,'preflight/four profiles')
    require({(p['seed_id'],p['maximum_half_ticks']) for p in native['profiles']}=={(i,m) for i in [0,1] for m in [65536,32768]},'all histories/resolutions')
    for p in native['profiles']:require(p['exit_code']==0 and p['wall_s']<=1800 and not p['administrative_stop'] and p['minimum_free_bytes']>=native['reserve_bytes'],'profile resource gates')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'new measured output');private[o['path']]=o['sha256']
    for n,h in reference['input_sha256'].items():require(private[n]==h and sha(ROOT/n)==h,'analyzed private input '+n)
    require(len(reference['aggregates'])==2 and len(reference['cycles'])==4 and len(reference['short_prefix_refinement'])==2,'both seed analyses');intervals=0;halves=0
    for r in reference['aggregates']:
        require(len(r['profiles'])==2 and len(r['shared_clock_points'])==21 and r['frequency_refinement_cents']<=1 and max(r['extrema_refinement_v'].values())<=.005,'same-clock frequency/extrema refinement')
        for point in r['shared_clock_points']:require(Decimal(point['max_error_ratio'])<=1,'200-coordinate refinement')
        for p in r['profiles']:
            require(p['final_ticks']==2752512000 and p['restore_replays']==2 and p['segments']==1 and p['endpoints']==2*p['intervals'] and p['intervals']<=(32000 if p['maximum_half_ticks']==65536 else 48000),'cycle clock/counts')
            require(p['max_lte']<=1 and max(p['max_bus_kcl_a'],p['max_c1_kcl_a'])<=1e-12 and Decimal(p['integrated_charge_relative'])<=Decimal('.002'),'global electrical gates');intervals+=p['intervals'];halves+=p['endpoints']
            require(len(p['measurements']['crossings'])==2 and not p['measurements']['steady_periodicity_admitted'],'one observed period')
    for r in reference['short_prefix_refinement']:require(len(r['shared_clock_points'])==1 and r['shared_clock_points'][0]['ticks']==1048576 and Decimal(r['shared_clock_points'][0]['max_error_ratio'])<=1,'2us refinement')
    selected=reference['new_independent'];require(len(selected['root_checks'])==48 and sum(r['rows'] for r in selected['root_checks'])==19200 and len(selected['current_checks'])==32 and len(selected['temporal_checks'])==16,'independent selected coverage')
    for r in selected['root_checks']:require(max(r['residual_gate_ratio'],r['correction_gate_ratio'])<=1,'independent selected equations')
    for r in selected['current_checks']:require(Decimal(r['max_error_a'])<=Decimal.from_float(2e-11),'terminal current comparison')
    for r in selected['temporal_checks']:require(Decimal(r['error_ratio_decimal'])<=1,'selected LTE')
    for r in reference['cycles']:
        require(len(r['events'])==2 and len(r['capacitor_changes'])==18 and len(r['phase_state_difference'])==200 and r['short_prefix_bit_identical'] and Decimal(r['c1_integrated_balance_relative'])<=Decimal('.002'),'cycle charges/C1/short history')
        require(r['phase_interpolation_is_observation'] and not r['steady_periodicity_admitted'],'phase observation scope')
        p=r['nominal_panel'];require(max(p['cursor_kcl_max_a'],p['c27_direction_max_a'],p['thevenin_current_max_error_a'])<=1e-12,'nominal panel endpoint identities')
        for name in ['cycle_radau_mean_ledger','full_radau_mean_ledger']:
            m=r[name];require(Decimal(m['c27_charge_integral_error_c'])<=Decimal(m['c27_charge_integral_gate_c']) and max(Decimal(m['panel_mean_identity_error_v']),Decimal(m['panel_mean_recombination_error_v']))<=Decimal.from_float(1e-9) and m['not_an_independent_all_stage_quadrature'],'mean integral/charge scope')
    require(len(reference['history_contrast'])==2 and all(r['histories_have_same_nominal_scene'] and r['none_admits_steady_periodicity'] for r in reference['history_contrast']),'historical scope');require(reference['own_seed_cycles_admitted'] and not reference['steady_periodicity_admitted'] and not reference['global_settling_bound'] and not reference['independent_root_search'],'admission')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');links=local_links(sorted(n for n in staged if n.endswith('.md')));names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-seed-cycles-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,inherited_test_count=248,native_test_count=0,covered_test_count=248,inherited_tests_reexecuted=False,new_independent_dynamic_rows=19200,new_independent_stage_points=96,new_independent_terminal_currents=96,independent_roots=0,accepted_intervals=intervals,published_half_steps=halves,duration_per_profile_s=.00525,final_ticks=2752512000,seed_histories=2,profiles=4,restore_replays=8,short_release_bit_reproductions=4,observed_cycles=4,chain_capacitors_per_cycle=18,radau_panel_mean_ledgers=8,phase_interpolation_is_observation=True,seed_cycles_admitted=True,steady_periodicity_admitted=False,own_joint_power_on=False,global_settling_bound=False,physical_cards_changed=False,full_voice_radau_admitted=False,physical_fidelity=False,real_time=False,heap_measured_this_block=False,lab_stack_bytes=33554432,new_audio=False,new_spice_processes=0,new_library_compile=False,cache_compression_preserves_all_bytes=True,cache_allocation_reclaimed_bytes=sum(r['allocation_reclaimed_bytes'] for r in compression),local_markdown_links=links,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'])

def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_seed_cycles.py').read_text())
        try:audit();r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_joint_seed_cycles_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_joint_seed_cycles_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('SEED_CYCLES_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),flush=True)
if __name__=='__main__':main()
