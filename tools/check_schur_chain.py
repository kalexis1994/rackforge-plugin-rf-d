"""Verify the four-block Schur implementation and its loaded conditional cycle."""
import base64,hashlib,json,shutil,statistics,subprocess
from decimal import Decimal
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_schur_chain import solver,kernel,caller,bench,ATTR,INNER,PORTS,EXTERNAL
from prepare_schur_contour import INNER as CONTOUR
from prepare_dynamic_schur import maps
from joint_cycles_analysis import require

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_schur_contour_tests01.json';old=read(previous);before=read('evidence/voice_schur_chain_before01.json')
    require(old['passed'] and old['contour_schur_admitted'] and before['previous_qa_sha256']==sha(ROOT/previous),'admitted base identity')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR,'declared attributes')
    for n,s in [('tools/dynamic_schur_chain_solver.rs',solver()),('tools/joint_schur_chain_kernel.rs',kernel()),('tools/joint_schur_chain_runner.rs',caller()),('tools/schur_chain_bench.rs',bench())]:require((ROOT/n).read_text(encoding='utf8')==s,'declared partition '+n)
    inp=read('evidence/voice_schur_chain_inputs01.json');require(inp['chain_interiors']==INNER and inp['chain_ports']==PORTS and inp['external']==EXTERNAL,'documented chain frontier')
    parts=maps()[0]+[CONTOUR,INNER,EXTERNAL];require(len(EXTERNAL)==140 and sum(map(len,parts))==458 and sorted(sum(parts,[]))==list(range(458)) and set(PORTS)<=set(EXTERNAL),'disjoint complete reconstruction')
    names=['evidence/voice_schur_refined_'+s+'.json' for s in ['chainbench01','chainconfirm01','chainbank01','chainstructure01','chainstructure02']]+['evidence/voice_schur_chain_'+s+'01.json' for s in ['inputs','roots','native','trajectory','driver_repair']]+['evidence/voice_schur_refined_chainprofile01.json','evidence/voice_schur_refined_chainprofile02.json','evidence/voice_schur_chain_profile_replay01.json']
    receipts=[read(n) for n in names];historic={}
    for r in receipts:
        for n,v in r.get('failed_source_base64',{}).items():historic[n,hashlib.sha256(base64.b64decode(v)).hexdigest()]=True
    for name,r in zip(names,receipts):
        require(r['passed'] or name in ['evidence/voice_schur_refined_chainstructure01.json','evidence/voice_schur_refined_chainprofile01.json'],'receipt '+name)
        for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h or (n,h) in historic,'receipt source '+name+' '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable source')
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable private')
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'private receipt '+n);private[n]=h
        for f in r.get('outputs',[]):require(sha(ROOT/f['path'])==f['sha256'],'output '+f['path']);private[f['path']]=f['sha256']
        if 'compiler' in r:require(sha(Path(r['compiler']['path']))==r['compiler']['sha256'],'compiler')
    first,confirm,bank,failed,regressions,_,roots,native,trajectory,repair,profile_failed,profile,profile_replay=receipts
    for r in [first,confirm,bank,regressions]:
        require(all(c['exit_code']==0 and c['wall_s']<=600 for c in r['commands']),'bounded accepted bank commands')
        if 'compiler' in r:require(r['commands'][0]['wall_s']<=120,'compile budget')
    for r in [first,confirm]:
        require(r['utility_passed'] and len(r['rounds'])==5 and [x[0] for x in r['rounds']]==list(range(5)),'two five-round scopes')
        require(statistics.median(x[1]/x[2] for x in r['rounds'])==r['median_paired_speedup']>1,'paired utility')
    require(1<first['median_paired_speedup']<=1.10 and confirm['same_executable'] and not confirm['new_compilation'] and len(confirm['commands'])==1 and first['commands'][1]['command'][:2]==confirm['commands'][0]['command'][:2],'single confirmation')
    require((ROOT/'references-local/schur-refined-chainbench01/roots.txt').read_bytes()==(ROOT/'references-local/schur-refined-chainconfirm01/roots.txt').read_bytes(),'confirmed roots')
    require(bank['identical_replay'] and bank['linear_solves']==396 and bank['independent_linear_rows']==181368 and bank['inherited_independent_linear_rows']==0 and bank['independent_linear_checks_reexecuted'] and bank['decimal_precision']==100,'fresh exact linear scope')
    require(len(bank['exact_linear_checks'])==396,'all linear traces')
    for q in bank['exact_linear_checks']:require(Decimal(q['schur_mixed_max'])<=Decimal('1e-11') and Decimal(q['full_refined_mixed_max'])<=Decimal('1e-11') and Decimal(q['correction_max_ratio'])<=1,'independent exact rows')
    require(bank['memory_observations']==1680 and bank['terminal_and_ground_currents']==2016 and bank['memory_max_ratio']<=1 and bank['port_current_max_a']<=2e-11,'LM741 storage and ports')
    require(roots['independent_nonlinear_rows']==38472 and len(roots['roots'])==84 and roots['wall_s']<=600 and not roots['full_trajectory_admitted'],'fresh nonlinear roots')
    require(not failed['passed'] and len(failed['commands'])==3 and failed['commands'][1]['exit_code']==failed['commands'][2]['exit_code']==3221225725 and failed['commands'][1]['stdout']==failed['commands'][2]['stdout'] and all('has overflowed its stack' in c['stderr'] for c in failed['commands'][1:]),'preserved test driver stack failure')
    require(repair['failed_receipt_sha256']==sha(ROOT/'evidence/voice_schur_refined_chainstructure01.json') and repair['repaired_driver_sha256']==sha(ROOT/'tools/check_schur_chain_regressions.py') and repair['stack_bytes_unchanged']==33554432 and repair['same_cases_and_inputs'] and not repair['production_solver_changed'] and not repair['numerical_gates_changed'],'driver frame repair')
    for n,h in repair['protected_source_sha256'].items():require(sha(ROOT/n)==h,'unchanged solver during repair')
    require(regressions['identical_replay'] and regressions['regressions']==45 and regressions['workspace_regressions']==11 and regressions['structural_regressions']==25 and regressions['substitution_regressions']==9 and regressions['zero_budget_variant_is_test_only'],'shared ports and rejection regressions')
    require(not profile_failed['passed'] and profile_failed['commands'][-1]['exit_code']==0 and 'exact profile calls' in profile_failed['failure'] and profile_replay['identical_call_counts'] and profile_replay['exact_root_fields_preserved'] and profile_replay['failed_receipt_sha256']==sha(ROOT/'evidence/voice_schur_refined_chainprofile01.json') and not profile_replay['numerical_gates_changed'],'preserved profile observer rejection')
    require(profile['selected_pairs']==84 and profile['exact_bit_fields_per_pair']==1834 and profile['iterations_and_trials_identical'] and profile['timing_is_nested'] and not profile['benchmark_utility_claim'],'private profile identity and scope')
    phase=profile['phases'];require([q['calls'] for q in phase]==[84,460,856,396,396,396,792,396,396,396,8752,1208,2000,416,416,416] and profile['first_stage_rejections']==64 and profile['second_stage_rejections']==0,'short-circuit phase accounting')
    require(profile['linearize_fraction_of_step']==phase[1]['time_ns']/phase[0]['time_ns'] and profile['solve_fraction_of_step']==phase[3]['time_ns']/phase[0]['time_ns'] and profile['prepare_fraction_of_solve']==phase[4]['time_ns']/phase[3]['time_ns'],'nested profile fractions')
    require(trajectory['chain_schur_cycle_window_admitted'] and len(native['profiles'])==len(trajectory['profiles'])==4,'fresh temporal admission')
    require(len(native['commands'])==1 and native['commands'][0]['exit_code']==0 and native['commands'][0]['wall_s']<=120 and not native['replays'] and all(p['exit_code']==0 and p['wall_s']<=990 for p in native['profiles']) and native['wall_s']<=4000 and trajectory['wall_s']<=600,'bounded campaign/oracle')
    require(trajectory['independent_nonlinear_rows']==38472 and trajectory['restores']==24 and trajectory['rejected_corruptions']==16 and trajectory['atomic_rollbacks']==8,'fresh graph and replay gates')
    for p in trajectory['profiles']+trajectory['joined_cycles']:
        for n,h in p['input_sha256'].items():require(sha(ROOT/n)==h,'audited profile '+n);private[n]=h
    comparisons=['original_lu_same_clock_comparison','admitted_schur_same_clock_comparison','same_clock_refinement']
    for label in comparisons:require(max(q['gate_ratio'] for q in trajectory[label])<=1,'all229 '+label)
    added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'new private/reserve budget')
    return dict(base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),private_input_sha256=private,new_private_bytes=size,lab_collection_verified=True,numeric_bank_passed=True,cost_utility_passed=True,dynamic_schur_admitted=True,contour_schur_admitted=True,chain_schur_admitted=True,schur_cycle_window_admitted=True,full_contour_from_silence_admitted=False,median_paired_speedup=first['median_paired_speedup'],confirmation_median_paired_speedup=confirm['median_paired_speedup'],exterior_corrections=140,condensed_chain_corrections=132,physical_states=229,reconstructed_corrections=458,independent_linear_rows_reexecuted=181368,independent_bank_nonlinear_rows_reexecuted=38472,independent_temporal_nonlinear_rows_reexecuted=trajectory['independent_nonlinear_rows'],inherited_independent_linear_rows=0,max_decimal_backward=str(max(Decimal(q['schur_mixed_max']) for q in bank['exact_linear_checks'])),refinement_histogram=bank['refinement_histogram'],solver_regressions=45,memory_observations=1680,terminal_and_ground_currents=2016,accepted_steps=trajectory['accepted_steps'],fine_steps=trajectory['fine_steps'],restores=trajectory['restores'],replayed_accepted_steps=trajectory['replayed_accepted_steps'],rejected_corruptions=16,atomic_rollbacks=8,maximum_original_lu_gate_ratio=max(q['gate_ratio'] for q in trajectory['original_lu_same_clock_comparison']),maximum_admitted_schur_gate_ratio=max(q['gate_ratio'] for q in trajectory['admitted_schur_same_clock_comparison']),maximum_refinement_gate_ratio=max(q['gate_ratio'] for q in trajectory['same_clock_refinement']),native_wall_s=native['wall_s'],new_duration_s=0,new_audio=False,new_library_compile=False,new_spice_processes=0,physical_fidelity=False,real_time=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False)

def main():
    r=audit();write('evidence/voice_schur_chain_reference01.json',dict(passed=True,**r));print('SCHUR_CHAIN_REFERENCE',r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'],'ADMITTED',r['chain_schur_admitted'])
if __name__=='__main__':main()
