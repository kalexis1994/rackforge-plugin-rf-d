"""Audit the profile and all rejected utility attempts with exact inherited data."""
import base64,hashlib,json,shutil,statistics,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_schur_inline import solver as inline_solver,kernel as inline_kernel,caller as inline_caller,ATTR as INLINE_ATTR
from prepare_schur_support import solver as support_solver,kernel as support_kernel,caller as support_caller,ATTR as SUPPORT_ATTR
from prepare_schur_rhs import solver as rhs_solver,kernel as rhs_kernel,caller as rhs_caller,ATTR as RHS_ATTR
from joint_cycles_analysis import require
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_schur_refined_tests01.json';old=read(previous);before=read('evidence/voice_schur_cost_before01.json');require(old['passed'] and old['numeric_bank_passed'] and not old['cost_utility_passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'base scope');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+INLINE_ATTR+SUPPORT_ATTR+RHS_ATTR,'declared attributes')
    for prefix,solver,kernel,caller in [('inline',inline_solver,inline_kernel,inline_caller),('support',support_solver,support_kernel,support_caller),('rhs',rhs_solver,rhs_kernel,rhs_caller)]:
        for n,s in [(f'tools/dynamic_schur_{prefix}_solver.rs',solver()),(f'tools/joint_schur_{prefix}_kernel.rs',kernel()),(f'tools/joint_schur_{prefix}_runner.rs',caller())]:require((ROOT/n).read_text(encoding='utf8')==s,'declared candidate '+n)
    names=['evidence/voice_schur_refined_'+s+'.json' for s in ['profile01','inlinebench01','supportbench01','supportbench02','supportbank01','rhsbench01','rhsbank01','rhsstructure01']]+[p.relative_to(ROOT).as_posix() for p in (ROOT/'evidence').glob('voice_schur_cost*.json') if not any(x in p.name for x in ['_tests','_reference','_qa_failure'])]
    receipts=[read(n) for n in names];historic={}
    for r in receipts:
        for key in ['failed_source_base64','before_source_base64']:
            for n,v in r.get(key,{}).items():historic[n,hashlib.sha256(base64.b64decode(v)).hexdigest()]=True
    for name,r in zip(names,receipts):
        for key in ['source_sha256','previous_source_sha256','rejected_source_sha256']:
            for n,h in r.get(key,{}).items():require(sha(ROOT/n)==h or (n,h) in historic,'receipt source '+name+' '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable measured source')
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private receipt '+n);private[n]=h
        for f in r.get('outputs',[]):require(sha(ROOT/f['path'])==f['sha256'],'output '+f['path']);private[f['path']]=f['sha256']
    profile=read('evidence/voice_schur_refined_profile01.json');require(profile['passed'] and profile['selected_pairs']==84 and profile['exact_bit_fields_per_pair']==1834 and profile['timing_is_nested'] and not profile['benchmark_utility_claim'],'profile identity scope');require([p['calls'] for p in profile['phases']]==[396,792,396,396,8752,416,416,416,396],'factor/reuse accounting')
    failed=read('evidence/voice_schur_refined_supportbench01.json');require(not failed['passed'] and len(failed['commands'])==2 and all(c['exit_code']!=0 for c in failed['commands']) and failed['commands'][0]['stderr']==failed['commands'][1]['stderr'],'same compile rejection');repair=read('evidence/voice_schur_cost_type_repair01.json');require(repair['failed_bench_sha256']==sha(ROOT/'evidence/voice_schur_refined_supportbench01.json') and not repair['numerical_gates_changed'],'preserved type-only repair')
    benchmarks=[];original_roots=(ROOT/'references-local/schur-refined-bench02/roots.txt').read_bytes()
    for tag in ['inlinebench01','supportbench02','rhsbench01']:
        r=read('evidence/voice_schur_refined_'+tag+'.json');require(r['passed'] and not r['utility_passed'] and r['selected_pairs']==84 and len(r['rounds'])==5 and [x[0] for x in r['rounds']]==list(range(5)),'bounded paired scope');speed=statistics.median(x[1]/x[2] for x in r['rounds']);require(speed==r['median_paired_speedup'] and speed<1 and r['max_candidate_gate_ratio']<=1,'rejected utility/candidate scope');require(r['commands'][0]['wall_s']<=120 and r['commands'][1]['wall_s']<=600,'benchmark budget');p=next(f['path'] for f in r['outputs'] if f['path'].endswith('roots.txt'));require((ROOT/p).read_bytes()==original_roots,'complete root bytes');benchmarks.append(dict(variant=tag,median_paired_speedup=speed,speedups=r['speedups'],utility_passed=False))
    baseline=read('evidence/voice_schur_refined_bank02.json');original_trace=(ROOT/'references-local/schur-refined-bank01/linear.bin').read_bytes()
    for tag in ['supportbank01','rhsbank01']:
        r=read('evidence/voice_schur_refined_'+tag+'.json');require(r['passed'] and r['identical_replay'] and r['linear_solves']==396 and r['inherited_independent_linear_rows']==181368 and r['independent_linear_rows']==0 and not r['independent_linear_checks_reexecuted'],'inherited linear scope');require(r['exact_linear_checks']==baseline['exact_linear_checks'],'frozen exact auditor rows');p=next(f['path'] for f in r['outputs'] if f['path'].endswith('linear.bin'));require((ROOT/p).read_bytes()==original_trace,'all J/b/corrections');require(r['memory_observations']==1680 and r['terminal_and_ground_currents']==2016 and r['memory_max_ratio']<=1 and r['port_current_max_a']<=2e-11,'storage/current gates')
    regression=read('evidence/voice_schur_refined_rhsstructure01.json');require(regression['passed'] and regression['identical_replay'] and regression['regressions']==21 and regression['structural_regressions']==12 and regression['substitution_regressions']==9,'finite-row/IEEE regressions');require(not any((ROOT/('references-local/schur-refined-'+s)).exists() for s in ['inlinebank01','inlinestructure01']),'do not credit unexecuted helper scopes')
    added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'private/reserve budget')
    return dict(base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),private_input_sha256=private,new_private_bytes=size,profile=profile['phases'],benchmarks=benchmarks,lab_collection_verified=True,numeric_bank_passed=True,cost_utility_passed=False,dynamic_schur_admitted=False,full_trajectory_admitted=False,selected_pairs=84,inherited_independent_linear_rows=181368,inherited_independent_nonlinear_rows=38472,independent_equations_reexecuted=False,solver_regressions=21,memory_observations=1680,terminal_and_ground_currents=2016,new_duration_s=0,new_audio=False,new_library_compile=False,new_spice_processes=0,physical_fidelity=False,real_time=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False)
def main():
    r=audit();write('evidence/voice_schur_cost_reference01.json',dict(passed=True,**r));print('SCHUR_COST_REFERENCE',r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'],'UTILITY',r['cost_utility_passed'])
if __name__=='__main__':main()
