"""Audit immutable lineage, failed replays and selected fixed-step sensitivity."""
import base64,hashlib,json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_history_tangent_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_joint_corrected_cycles_tests01.json';old=read(previous);before=read('evidence/voice_history_tangent_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous admission')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,d in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==d,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,d in private.items():require(sha(ROOT/n)==d,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_history_tangent.rs text eol=lf\n/tools/joint_history_tangent_runner.rs text eol=lf\n','only laboratory attributes')
    helper=(ROOT/'tools/joint_history_tangent.rs').read_text(encoding='utf8');seed=(ROOT/'tools/joint_charge_response_fine_runner.rs').read_text(encoding='utf8');expected=seed[seed.index('fn solve<const M: usize>'):seed.index('const K:usize=18;')].strip();require(helper[helper.index('fn solve<const M: usize>'):].strip()==expected,'identical admitted lab solver')
    inputs=read('evidence/voice_history_tangent_inputs01.json');require(inputs['passed'] and len(inputs['selected_sha256'])==4 and sha(ROOT/inputs['path'])==inputs['sha256'],'selected four profiles');private[inputs['path']]=inputs['sha256']
    for n,d in inputs['source_sha256'].items():require(sha(ROOT/n)==d,'input preparation source')
    for n,d in inputs['selected_sha256'].items():require(private[n]==d,'already admitted selected stages')
    attempts=[]
    for k in [1,2,3,4,5]:
        name=f'evidence/voice_history_tangent_native{k:02d}.json';r=read(name);require(r['source_sha256']==r['source_sha256_after'] and r['private_used_sha256']==r['private_used_sha256_after'],'unchanged attempt '+str(k))
        require(sha(__import__('pathlib').Path(r['compiler']['path']))==r['compiler']['sha256'] and not r['new_library_compile'] and not r['new_audio'] and r['new_spice_processes']==0,'frozen build')
        for n,d in r['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'frozen native input')
        for o in r['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'preserved native output');private[o['path']]=o['sha256']
        require(r['minimum_free_bytes']>=r['reserve_bytes'] and r['available_free_bytes']>=r['reserve_bytes']+r['estimated_output_bytes'] and r['wall_s']<=900,'resource gates')
        for i,c in enumerate(r['commands']):require(not c['administrative_stop'] and c['wall_s']<=(120 if i==0 else 600),'command resources')
        if k<5:
            require(not r['passed'] and len(r['replays'])==1 and r['commands'][-1]['exit_code']!=0 and r['replays'][0]['exit_code']!=0,'failed attempt and replay')
            marker=['E0603','E0433','ERROR,STEP_PLUS,9,117,NoDecrease','ERROR,STEP_PLUS,10,117,IterationBudget'][k-1]
            for c in [r['commands'][-1],r['replays'][0]]:require(marker in (ROOT/c['stderr_path']).read_text(),'same terminal failure')
            for n in ['tools/joint_history_tangent.rs','tools/run_history_tangent.py']:require(hashlib.sha256(r['failed_source_text'][n].encode()).hexdigest()==r['source_sha256'][n],'failed source retained')
        else:
            require(r['passed'] and len(r['commands'])==2 and not r['replays'],'passed native')
            for n,d in r['source_sha256'].items():require(sha(ROOT/n)==d,'measured native source')
        attempts.append(r)
    ref=read('evidence/voice_history_tangent_reference01.json');require(ref['passed'] and ref['source_sha256']==ref['source_sha256_after'],'passed independent comparison')
    for n,d in ref['source_sha256'].items():require(sha(ROOT/n)==d,'measured reference source')
    for n,d in ref['input_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'reference inputs')
    require(len(ref['records'])==48 and ref['history_columns']==9600 and ref['response_directions']==432 and ref['baseline_bit_reproductions']==48 and ref['negative_controls']==48 and ref['fixed_step_response_admitted'] and not ref['adaptive_derivative_admitted'] and not ref['period_map_admitted'] and ref['independent_roots']==0,'coverage and scope')
    for r in ref['records']:
        require(r['absolute_candidate_leak_per_epsilon']<=1e-18 and r['history']['max_ratio']<=1 and all(c['max_ratio']<=1 for c in r['history_fd']) and len(r['responses'])==9,'all history coverage')
        for c in r['responses']:require(c['independent']['max_ratio']<=1 and all(f['max_ratio']<=1 for f in c['nonlinear_fd']),'all response gates')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');links=local_links(sorted(n for n in staged if n.endswith('.md')));names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/history-tangent-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,history_columns=9600,history_entries=3840000,history_fd_entries=7680000,response_directions=432,response_stage_coordinates=172800,perturbed_native_step_solves=1728,baseline_bit_reproductions=48,negative_controls=48,preserved_failed_attempts=4,fixed_step_response_admitted=True,adaptive_derivative_admitted=False,period_map_admitted=False,independent_roots=0,physical_cards_changed=False,new_library_compile=False,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=links)
def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_history_tangent.py').read_text())
        try:audit();r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_history_tangent_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_history_tangent_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('HISTORY_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),flush=True)
if __name__=='__main__':main()
