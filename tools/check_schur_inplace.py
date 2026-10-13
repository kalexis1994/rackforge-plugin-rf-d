"""Verify exact bank, single confirmation and freshly audited conditional trajectories."""
import base64,hashlib,json,shutil,statistics,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_schur_inplace import solver,kernel,caller,ATTR
from joint_cycles_analysis import require
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_schur_cost_tests01.json';old=read(previous);before=read('evidence/voice_schur_inplace_before01.json');require(old['passed'] and old['numeric_bank_passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'base scope');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'declared attributes')
    for n,s in [('tools/dynamic_schur_inplace_solver.rs',solver()),('tools/joint_schur_inplace_kernel.rs',kernel()),('tools/joint_schur_inplace_runner.rs',caller())]:require((ROOT/n).read_text(encoding='utf8')==s,'declared in-place implementation '+n)
    names=['evidence/voice_schur_refined_'+s+'.json' for s in ['inplacebench01','inplaceconfirm01','inplacebank01','inplacestructure01','inplacestructure02']]+[p.relative_to(ROOT).as_posix() for p in (ROOT/'evidence').glob('voice_schur_inplace*.json') if not any(x in p.name for x in ['_reference','_tests','_qa_failure'])]
    receipts=[read(n) for n in names];historic={}
    for r in receipts:
        for n,v in r.get('failed_source_base64',{}).items():historic[n,hashlib.sha256(base64.b64decode(v)).hexdigest()]=True
    for name,r in zip(names,receipts):
        for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h or (n,h) in historic,'receipt source '+name+' '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable source')
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private receipt '+n);private[n]=h
        for f in r.get('outputs',[]):require(sha(ROOT/f['path'])==f['sha256'],'output '+f['path']);private[f['path']]=f['sha256']
        if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
    first=read('evidence/voice_schur_refined_inplacebench01.json');confirm=read('evidence/voice_schur_refined_inplaceconfirm01.json')
    for r in [first,confirm]:
        require(r['passed'] and r['utility_passed'] and len(r['rounds'])==5 and [x[0] for x in r['rounds']]==list(range(5)),'two five-round scopes');require(statistics.median(x[1]/x[2] for x in r['rounds'])==r['median_paired_speedup']>1,'paired utility')
    require(1<first['median_paired_speedup']<=1.10 and confirm['same_executable'] and not confirm['new_compilation'] and len(confirm['commands'])==1 and first['commands'][1]['command'][:2]==confirm['commands'][0]['command'][:2],'single confirmation rule')
    original_roots=(ROOT/'references-local/schur-refined-bench02/roots.txt').read_bytes()
    for r in [first,confirm]:
        p=next(f['path'] for f in r['outputs'] if f['path'].endswith('roots.txt'));require((ROOT/p).read_bytes()==original_roots,'84 roots by bytes')
    bank=read('evidence/voice_schur_refined_inplacebank01.json');require(bank['passed'] and bank['identical_replay'] and bank['linear_solves']==396 and bank['independent_linear_rows']==0 and bank['inherited_independent_linear_rows']==181368 and not bank['independent_linear_checks_reexecuted'],'exact inherited bank scope');p=next(f['path'] for f in bank['outputs'] if f['path'].endswith('linear.bin'));require((ROOT/p).read_bytes()==(ROOT/'references-local/schur-refined-bank01/linear.bin').read_bytes(),'all J/b/corrections');require(bank['memory_observations']==1680 and bank['terminal_and_ground_currents']==2016 and bank['memory_max_ratio']<=1 and bank['port_current_max_a']<=2e-11,'memories and ports')
    failed=read('evidence/voice_schur_refined_inplacestructure01.json');repair=read('evidence/voice_schur_inplace_driver_repair01.json');require(not failed['passed'] and all('has overflowed its stack' in c['stderr'] for c in failed['commands'][1:]) and failed['commands'][1]['stdout']==failed['commands'][2]['stdout'],'preserved test stack rejection');require(repair['failed_receipt_sha256']==sha(ROOT/'evidence/voice_schur_refined_inplacestructure01.json') and repair['stack_bytes_unchanged']==33554432 and not repair['production_solver_changed'] and not repair['numerical_gates_changed'],'same-budget scratch repair')
    regressions=read('evidence/voice_schur_refined_inplacestructure02.json');require(regressions['passed'] and regressions['identical_replay'] and regressions['regressions']==26 and regressions['workspace_regressions']==5 and regressions['structural_regressions']==12 and regressions['substitution_regressions']==9,'reinitialization regressions')
    native=read('evidence/voice_schur_inplace_native01.json');trajectory=read('evidence/voice_schur_inplace_trajectory01.json');require(native['passed'] and trajectory['passed'] and trajectory['schur_cycle_window_admitted'] and len(native['profiles'])==len(trajectory['profiles'])==4,'fresh native trajectory admission');require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'] and all(p['exit_code']==0 and p['wall_s']<=990 for p in native['profiles']) and native['wall_s']<=4000 and trajectory['wall_s']<=600,'bounded campaign/oracle');require(trajectory['restores']==24 and trajectory['rejected_corruptions']==16 and trajectory['atomic_rollbacks']==8,'replay/rollback gates')
    for p in trajectory['profiles']:
        for n,h in p['input_sha256'].items():require(sha(ROOT/n)==h,'audited profile '+n);private[n]=h
    for p in trajectory['joined_cycles']:
        for n,h in p['input_sha256'].items():require(sha(ROOT/n)==h,'audited seam '+n);private[n]=h
    require(max(q['gate_ratio'] for q in trajectory['original_lu_same_clock_comparison'])<=1 and max(q['gate_ratio'] for q in trajectory['same_clock_refinement'])<=1,'all229 original/refinement comparisons')
    added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'new private/reserve budget')
    return dict(base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),private_input_sha256=private,new_private_bytes=size,lab_collection_verified=True,numeric_bank_passed=True,cost_utility_passed=True,dynamic_schur_admitted=True,schur_cycle_window_admitted=True,full_contour_from_silence_admitted=False,median_paired_speedup=first['median_paired_speedup'],confirmation_median_paired_speedup=confirm['median_paired_speedup'],independent_nonlinear_rows_reexecuted=trajectory['independent_nonlinear_rows'],inherited_independent_linear_rows=181368,solver_regressions=26,memory_observations=1680,terminal_and_ground_currents=2016,accepted_steps=trajectory['accepted_steps'],fine_steps=trajectory['fine_steps'],restores=trajectory['restores'],replayed_accepted_steps=trajectory['replayed_accepted_steps'],rejected_corruptions=16,atomic_rollbacks=8,maximum_original_lu_gate_ratio=max(q['gate_ratio'] for q in trajectory['original_lu_same_clock_comparison']),maximum_refinement_gate_ratio=max(q['gate_ratio'] for q in trajectory['same_clock_refinement']),native_wall_s=native['wall_s'],new_duration_s=0,new_audio=False,new_library_compile=False,new_spice_processes=0,physical_fidelity=False,real_time=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False)
def main():
    r=audit();write('evidence/voice_schur_inplace_reference01.json',dict(passed=True,**r));print('SCHUR_INPLACE_REFERENCE',r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'],'ADMITTED',r['dynamic_schur_admitted'])
if __name__=='__main__':main()
