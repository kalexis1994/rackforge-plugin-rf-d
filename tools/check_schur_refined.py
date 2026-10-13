"""Verify numerical bank admission separately from failed timing utility."""
import base64,hashlib,json,shutil,statistics,subprocess
from decimal import Decimal
from prepare_vco1_portable import ROOT,sha,write
from prepare_schur_refined import kernel,caller,ATTR
from prepare_schur_refined_sparse import solver as sparse_solver,kernel as sparse_kernel,caller as sparse_caller,ATTR as SPARSE_ATTR
from joint_cycles_analysis import require
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_dynamic_schur_tests01.json';old=read(previous);before=read('evidence/voice_schur_refined_before01.json');require(old['passed'] and not old['dynamic_schur_admitted'] and before['previous_qa_sha256']==sha(ROOT/previous),'base rejected scope');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR+SPARSE_ATTR,'declared attributes')
    for n,s in [('tools/joint_schur_refined_kernel.rs',kernel()),('tools/joint_schur_refined_runner.rs',caller()),('tools/dynamic_schur_refined_sparse_solver.rs',sparse_solver()),('tools/joint_schur_refined_sparse_kernel.rs',sparse_kernel()),('tools/joint_schur_refined_sparse_runner.rs',sparse_caller())]:require((ROOT/n).read_text(encoding='utf8')==s,'recipe '+n)
    mapping=lambda n:[s for s in (ROOT/n).read_text(encoding='utf8').splitlines() if s.startswith(('const INNER','const PORTS','const EXTERNAL'))];require(mapping('tools/dynamic_schur_fast_solver.rs')==mapping('tools/dynamic_schur_refined_solver.rs'),'frozen maps')
    receipts=sorted(p for p in (ROOT/'evidence').glob('voice_schur_refined*.json') if not any(x in p.name for x in ['_reference','_tests','_qa_failure']))
    for p in receipts:
        r=read(p.relative_to(ROOT));require(r.get('passed',True),'collection receipt '+p.name)
        for key in ['source_sha256','dense_source_sha256']:
            for n,h in r.get(key,{}).items():require(sha(ROOT/n)==h,'receipt source '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable source measurement')
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private measurement')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'receipt private '+n);private[n]=h
        for f in r.get('outputs',[]):require(sha(ROOT/f['path'])==f['sha256'],'receipt output '+f['path']);private[f['path']]=f['sha256']
        if 'compiler' in r:require(sha(__import__('pathlib').Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
        if 'commands' in r:require(all(c['exit_code']==0 and c.get('wall_s',0)<=600 for c in r['commands']) and r['commands'][0].get('wall_s',0)<=120,'bounded command acceptance')
    target=read('evidence/voice_schur_refined_saved01.json');require(target['identical_replay'] and target['refinements']==1 and Decimal(target['decimal_mixed_backward_max'])<=Decimal('1e-11') and target['independent_linear_rows']==458,'saved exact failure repaired')
    dense=read('evidence/voice_schur_refined_bank01.json');bank=read('evidence/voice_schur_refined_bank02.json');require(dense['identical_replay'] and bank['identical_replay'] and dense['linear_solves']==bank['linear_solves']==396 and dense['exact_linear_checks']==bank['exact_linear_checks'],'same audited linear data');require((ROOT/'references-local/schur-refined-bank01/linear.bin').read_bytes()==(ROOT/'references-local/schur-refined-bank02/linear.bin').read_bytes(),'complete exact trace identity')
    for obj in [dense,bank]:
        require(obj['independent_linear_rows']==181368 and obj['decimal_precision']==100 and obj['refinement_histogram']=={'0':376,'1':20,'2':0,'3':0} and obj['full_refinement_histogram']=={'0':374,'1':22,'2':0,'3':0},'bounded bank refinements')
        for q in obj['exact_linear_checks']:require(Decimal(q['schur_mixed_max'])<=Decimal('1e-11') and Decimal(q['full_refined_mixed_max'])<=Decimal('1e-11') and Decimal(q['correction_max_ratio'])<=1,'exact row/correction gates')
        require(obj['memory_observations']==1680 and obj['terminal_and_ground_currents']==2016 and obj['memory_max_ratio']<=1 and obj['port_current_max_a']<=2e-11,'storage and terminal gates')
    require(sum(q['full_raw_failed_rows']>0 for q in bank['exact_linear_checks'])==22,'raw reference rejection visible')
    benchmarks=[]
    for attempt in [1,2]:
        r=read(f'evidence/voice_schur_refined_bench{attempt:02d}.json');rounds=r['rounds'];require(len(rounds)==5 and [q[0] for q in rounds]==list(range(5)) and r['selected_pairs']==84 and r['max_candidate_gate_ratio']<=1,'five paired rounds');speed=statistics.median(q[1]/q[2] for q in rounds);require(speed==r['median_paired_speedup'] and speed<1 and not r['utility_passed'],'failed utility retained');benchmarks.append(dict(attempt=attempt,median_paired_speedup=speed,speedups=r['speedups']))
    require((ROOT/'references-local/schur-refined-bench01/roots.txt').read_bytes()==(ROOT/'references-local/schur-refined-bench02/roots.txt').read_bytes(),'exact-support roots')
    roots=read('evidence/voice_schur_refined_roots01.json');require(roots['passed'] and roots['independent_nonlinear_rows']==38472 and len(roots['roots'])==84 and roots['wall_s']<=600 and not roots['full_trajectory_admitted'],'new independent roots')
    structure=read('evidence/voice_schur_refined_structure01.json');require(structure['regressions']==12 and structure['identical_replay'] and structure['zero_budget_variant_is_test_only'],'structural rejection domain')
    added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'new private/reserve budget')
    return dict(base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),private_input_sha256=private,new_private_bytes=size,benchmarks=benchmarks,lab_collection_verified=True,numeric_bank_passed=True,cost_utility_passed=False,dynamic_schur_admitted=False,full_trajectory_admitted=False,independent_linear_rows_unique=181368,independent_nonlinear_rows_reexecuted=38472,linear_solves=396,refinement_histogram=bank['refinement_histogram'],max_decimal_backward=str(max(Decimal(q['schur_mixed_max']) for q in bank['exact_linear_checks'])),memory_observations=1680,terminal_and_ground_currents=2016,solver_regressions=12,new_duration_s=0,new_audio=False,new_library_compile=False,new_spice_processes=0,physical_fidelity=False,real_time=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False)
def main():
    r=audit();write('evidence/voice_schur_refined_reference01.json',dict(passed=True,**r));print('SCHUR_REFINED_REFERENCE',r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'],'NUMERIC',r['numeric_bank_passed'],'UTILITY',r['cost_utility_passed'])
if __name__=='__main__':main()
