"""Release audit for static response, preserved rejections and corrected seeds."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_joint_charge_response import caller
from prepare_joint_charge_response_fine import derive,fine_checker,fine_runner
from build_joint_charge_corrected import caller as corrected_caller,checker as corrected_checker,runner as corrected_runner
from validate_joint_charge_seed import local_links
from validate_mixer_on_native import native_source_identity
from joint_cycles_analysis import require
OUT='evidence/voice_joint_charge_response_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def measured(r):
    require(r['passed'] and r['source_sha256']==r['source_sha256_after'],'unchanged measurement')
    for n,h in r['source_sha256'].items():require(sha(ROOT/n)==h,'measurement source '+n)

def audit():
    previous='evidence/voice_joint_seed_cycles_tests01.json';old=read(previous);before=read('evidence/voice_joint_charge_response_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous release')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    suffix=b'\n/tools/joint_charge_response_runner.rs text eol=lf\n\n/tools/joint_charge_response_fine_runner.rs text eol=lf\n\n/tools/joint_charge_corrected_runner.rs text eol=lf\n\n/evidence/voice_joint_charge_response_targets01.txt text eol=lf\n';require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+suffix,'only declared Rust/target attributes')
    generated={'tools/joint_charge_response_runner.rs':caller(),'tools/joint_charge_response_fine_runner.rs':derive(),'tools/run_joint_charge_response_fine.py':fine_runner(),'tools/check_joint_charge_response_fine.py':fine_checker().replace('voice_joint_charge_response_fine_native01.json','voice_joint_charge_response_fine_native03.json'),'tools/joint_charge_corrected_runner.rs':corrected_caller(),'tools/check_joint_charge_corrected.py':corrected_checker(),'tools/run_joint_charge_corrected.py':corrected_runner()}
    for n,text in generated.items():require((ROOT/n).read_bytes()==text.encode('utf8'),'declared generated source '+n)
    coarse=read('evidence/voice_joint_charge_response_native01.json');fine=read('evidence/voice_joint_charge_response_fine_native03.json');corrected=read('evidence/voice_joint_charge_corrected_native01.json')
    for r in [coarse,fine,corrected]:
        measured(r);require(r['private_used_sha256']==r['private_used_sha256_after'],'unchanged library')
        for n,h in r['private_used_sha256'].items():require(private[n]==h,'frozen library identity')
        require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'] and not r['new_library_compile'] and not r['new_audio'] and r['new_spice_processes']==0,'compiler and scope')
        require(len(r['commands'])==2 and all(c['exit_code']==0 and c['wall_s']<=180 for c in r['commands']) and not r['replays'] and r['wall_s']<=600,'bounded processes')
        require(r['available_free_bytes']>=r['reserve_bytes']+r['estimated_output_bytes'] and r['minimum_free_bytes']>=r['reserve_bytes'],'resource gates')
        for o in r['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'measured output');private[o['path']]=o['sha256']
    stops=[read(f'evidence/voice_joint_charge_response_fine_native{k:02d}.json') for k in [1,2]]
    for r in stops:
        require(not r['passed'] and not r['commands'] and not r['outputs'] and r['available_free_bytes']<r['reserve_bytes']+r['estimated_output_bytes'],'preserved repeated disk preflight rejection')
        for n,h in r['source_sha256'].items():require(sha(ROOT/n)==h,'preflight source '+n)
    for k in [1,2]:
        r=read(f'evidence/voice_joint_charge_response_compression{k:02d}.json');measured(r);require(r['deleted_files']==0 and r['moved_files']==0 and not r['logical_bytes_changed'] and r['files_before'].keys()==r['files_after'].keys(),'transparent compression')
        for n,row in r['files_before'].items():
            require(row['sha256']==r['files_after'][n]['sha256']==sha(ROOT/n) and row['bytes']==r['files_after'][n]['bytes'],'retained bytes')
            if n in private:require(row['sha256']==private[n],'previous protected identity')
            else:require(k==2 and not r['file_in_previous_private_manifest'] and r['compression_does_not_admit_export_electrical_results'],'capture identity only, no electrical admission');private[n]=row['sha256']
    rejected=read('evidence/voice_joint_charge_response_reference01.json');require(not rejected['passed'] and rejected['failure'].splitlines()[-1]==rejected['replay'].splitlines()[-1] and '7.170713215418341' in rejected['failure'],'preserved coarse gate rejection and replay')
    require(hashlib.sha256(rejected['failed_source_text'].encode()).hexdigest()==rejected['source_sha256']['tools/check_joint_charge_response.py']==sha(ROOT/'tools/check_joint_charge_response.py'),'original failed checker unchanged')
    codec=read('evidence/voice_joint_charge_response_refinement01.json');require(not codec['passed'] and codec['failure'].splitlines()[-1]==codec['replay'].splitlines()[-1] and 'both central perturbations' in codec['failure'],'preserved codec rejection and replay')
    require(hashlib.sha256(codec['failed_source_text'].encode()).hexdigest()==codec['source_sha256']['tools/check_joint_charge_response_refinement.py'],'failed codec source')
    text=codec['failed_source_text'].replace('from check_joint_charge_response import bank,D\n','from check_joint_charge_response import bank,D\nfrom check_joint_charge_response_fine import bank as fine_bank\n').replace("banks=[bank(json.loads((ROOT/n).read_text())) for n in names]","banks=[decoder(json.loads((ROOT/n).read_text())) for decoder,n in zip([bank,fine_bank],names)]").replace('voice_joint_charge_response_refinement01.json','voice_joint_charge_response_refinement02.json').replace("'tools/check_joint_charge_response.py','tools/check_joint_charge_seed.py'","'tools/check_joint_charge_response.py','tools/check_joint_charge_response_fine.py','tools/check_joint_charge_seed.py'")
    require((ROOT/'tools/check_joint_charge_response_refinement.py').read_text(encoding='utf8')==text,'only declared decoder repair')
    build=read('evidence/voice_joint_charge_corrected_build_failure01.json');require(not build['passed'] and build['replay_exit_code']!=0 and 'ModuleNotFoundError' in build['replay_stderr'],'preserved export import rejection and replay');require(hashlib.sha256(build['failed_source_text'].encode()).hexdigest()==build['source_sha256'],'failed exporter source')
    text=build['failed_source_text'].replace('from vco1_increment_solver import two_sum\n','').replace('from joint_cycles_analysis import require\n','from joint_cycles_analysis import require\n\ndef two_sum(a,b):\n    s=a+b;v=s-a\n    return s,(a-(s-v))+(b-v)\n')
    require((ROOT/'tools/build_joint_charge_corrected.py').read_text(encoding='utf8')==text,'only declared missing helper repair')
    adapter=read('evidence/voice_joint_charge_response_qa_failure01.json');require(not adapter['passed'] and adapter['failure'].splitlines()[-1]==adapter['replay'].splitlines()[-1] and "rejected['failure']==rejected['replay']" in adapter['failed_source_text'],'preserved traceback comparison defect and replay')
    ref=read('evidence/voice_joint_charge_response_fine_reference01.json');refinement=read('evidence/voice_joint_charge_response_refinement02.json');targets=read('evidence/voice_joint_charge_response_targets01.json');release=read('evidence/voice_joint_charge_corrected_reference01.json')
    for r in [ref,refinement,release]:measured(r)
    require(targets['passed'] and targets['target_file_sha256']==sha(ROOT/'evidence/voice_joint_charge_response_targets01.txt'),'export target identity')
    for n,h in targets['source_sha256'].items():require(sha(ROOT/n)==h,'target derivation source')
    require(len(ref['root_checks'])==146 and ref['augmented_rows']==31828 and ref['base_bit_reproductions']==2 and ref['response_columns']==36 and ref['response_entries']==7848 and ref['charge_incidence_rank']==18,'static response coverage')
    for x in ref['root_checks']:require(max(float(x['residual_gate_ratio']),float(x['correction_gate_ratio']))<=1,'independent augmented roots')
    for r in ref['records']:
        require(r['rank']==18 and r['condition']<=1e10 and len(r['singular_values_a_per_v'])==18 and r['independent_response_gate']['max_gate_ratio']<=1 and all(g['max_gate_ratio']<=1 for g in r['central_response_gates']),'response and inversion gates')
        p=r['predictor'];require(p['admitted'] and p['solve_residual_a']<=1e-12 and max(map(abs,p['applied_delta_target_v']))<=.1 and p['not_a_periodic_root'] and p['own_cycles_pending'],'static predictor scope')
    require(len(refinement['records'])==8 and refinement['analytic_tangents_bit_identical'] and not refinement['coarse_response_admitted'] and refinement['fine_response_gates_passed'],'same tangent refinement')
    for r in refinement['records']:require(r['gate_passed']==(r['half_perturbation_v']<=.000125),'unchanged coarse/fine gates')
    require(len(release['augmented_root_checks'])==4 and sum(x['rows'] for x in release['augmented_root_checks'])==872 and release['jointly_corrected_targets']==2,'nonlinear closure coverage')
    require(len(release['release_stage_checks'])==24 and sum(x['rows'] for x in release['release_stage_checks'])==9600 and len(release['release_lte'])==8 and len(release['release_profiles'])==4 and release['restore_replays']==4 and len(release['guess_comparisons'])==2 and len(release['release_refinement'])==2,'short release coverage')
    for x in [*release['augmented_root_checks'],*release['release_stage_checks']]:require(max(float(x['residual_gate_ratio']),float(x['correction_gate_ratio']))<=1,'independent closure and stage gates')
    require(release['duration_per_profile_s']==2e-6 and release['final_ticks']==1048576 and release['input_rejections']==2 and not release['steady_periodicity_admitted'] and not release['physical_cards_changed'],'short scope')
    for x in release['release_profiles']:require(x['intervals']<=512 and x['max_lte']<=1 and max(x['bus_kcl_a'],x['c1_kcl_a'])<=1e-12 and x['restore_exact'],'short trajectory gates')
    for r in [ref,release]:require(not r['independent_root_search'] and not r['steady_periodicity_admitted'] and not r['physical_cards_changed'] and not r['new_audio'] and r['new_spice_processes']==0,'scope')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');links=local_links(sorted(n for n in staged if n.endswith('.md')));names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-charge-response-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,inherited_test_count=248,inherited_tests_reexecuted=False,native_test_count=0,new_independent_initial_rows=32700,new_independent_dynamic_rows=9600,new_independent_stage_points=48,response_columns=36,response_entries=7848,finite_difference_steps_v=[.001,.0005,.000125,.0000625],coarse_derivative_rejection_preserved=True,decoder_failure_preserved=True,export_helper_failure_preserved=True,preflight_rejections=2,base_bit_reproductions=2,static_predictors=2,corrected_initial_roots=4,corrected_initialization_lab_admitted=True,short_release_admitted=True,accepted_intervals=release['accepted_intervals'],published_half_steps=2*release['accepted_intervals'],duration_per_profile_s=2e-6,final_ticks=1048576,restore_replays=4,static_response_is_not_period_map_jacobian=True,predicted_periodic_drift_improvement_unmeasured=True,steady_periodicity_admitted=False,physical_cards_changed=False,new_library_compile=False,own_joint_power_on=False,full_voice_radau_admitted=False,physical_fidelity=False,real_time=False,new_audio=False,new_spice_processes=0,lab_stack_bytes=33554432,compression_preserves_all_bytes=True,retained_export_electrical_results_not_admitted=True,local_markdown_links=links,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'])

def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_charge_response.py').read_text())
        try:audit();r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_joint_charge_response_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_joint_charge_response_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CHARGE_RESPONSE_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),flush=True)

if __name__=='__main__':main()
