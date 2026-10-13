"""Verify the finite Schur laboratory scope, preserving its rejected admission."""
import base64,hashlib,json,shutil,statistics,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_dynamic_schur import maps,kernel,caller,ATTR
from prepare_dynamic_schur_fast import solver as fast_solver,kernel as fast_kernel,caller as fast_caller,ATTR as FAST_ATTR
from joint_cycles_analysis import require

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_lu_extent_tests01.json';old=read(previous);before=read('evidence/voice_dynamic_schur_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'base QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base commit');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR+FAST_ATTR,'declared attributes')
    for n,expected in [('tools/joint_dynamic_schur_kernel.rs',kernel()),('tools/joint_dynamic_schur_runner.rs',caller()),('tools/dynamic_schur_fast_solver.rs',fast_solver()),('tools/joint_dynamic_schur_fast_kernel.rs',fast_kernel()),('tools/joint_dynamic_schur_fast_runner.rs',fast_caller())]:require((ROOT/n).read_text(encoding='utf8')==expected,'recipe '+n)
    inside,ports,exterior,raw=maps();inp=read('evidence/voice_dynamic_schur_inputs03.json');require(inp['interiors']==inside and inp['ports']==ports and inp['external']==exterior and inp['original_opamp_maps']==raw and inp['selected_pairs']==84,'documented partition')
    evidence=sorted(p for p in (ROOT/'evidence').glob('voice_dynamic_schur*.json') if not any(t in p.name for t in ['_reference','_tests','_qa_failure']))
    receipts={p.name:read(p.relative_to(ROOT)) for p in evidence};historic={}
    for r in receipts.values():
        snapshots=r.get('failed_source_base64',{})
        if isinstance(snapshots,str):snapshots={'tools/check_dynamic_schur_roots.py':snapshots}
        for n,s in snapshots.items():historic[n,hashlib.sha256(base64.b64decode(s)).hexdigest()]=True
    for name,r in receipts.items():
        for n,h in r.get('source_sha256',{}).items():require(sha(ROOT/n)==h or (n,h) in historic,'source or preserved failed snapshot '+name+' '+n)
        if 'source_sha256_after' in r:require(r['source_sha256']==r['source_sha256_after'],'stable receipt sources '+name)
        if 'private_used_sha256_after' in r:require(r['private_used_sha256']==r['private_used_sha256_after'],'stable receipt private '+name)
        for n,h in r.get('private_used_sha256',{}).items():require(sha(ROOT/n)==h,'receipt private '+n);private[n]=h
        for f in r.get('outputs',[]):require(sha(ROOT/f['path'])==f['sha256'],'receipt output '+f['path']);private[f['path']]=f['sha256']
    first=read('evidence/voice_dynamic_schur_bench_native01.json');require(not first['passed'] and len(first['commands'])==2 and first['commands'][0]['stderr']==first['commands'][1]['stderr'],'preserved compile replay')
    benchmarks=[]
    for attempt in [2,3]:
        r=read(f'evidence/voice_dynamic_schur_bench_native{attempt:02d}.json');require(r['passed'] and len(r['commands'])==2 and all(c['exit_code']==0 for c in r['commands']),'measured benchmark')
        lines=r['commands'][1]['stdout'].splitlines();cases=[x.split(',') for x in lines if x.startswith('CASE,')];rounds=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('ROUND,')];require(len(cases)==84 and [int(x[1]) for x in cases]==list(range(84)) and len(rounds)==5 and [x[0] for x in rounds]==list(range(5)) and lines[-1]=='PASSED,84,5,reconstructed_candidate_gates','paired bank scope');require(max(float(x[-1]) for x in cases)<=1,'candidates');require(r['commands'][0]['wall_s']<=120 and r['commands'][1]['wall_s']<=600,'benchmark budget');benchmarks.append(dict(attempt=attempt,speedups=[x[1]/x[2] for x in rounds],median=statistics.median(x[1]/x[2] for x in rounds),max_candidate_gate_ratio=max(float(x[-1]) for x in cases)))
    require(benchmarks[0]['median']<1<benchmarks[1]['median'],'measured lookup utility')
    require((ROOT/'references-local/dynamic-schur-bench02/roots.txt').read_bytes()==(ROOT/'references-local/dynamic-schur-bench03/roots.txt').read_bytes(),'index-only roots identical')
    roots=read('evidence/voice_dynamic_schur_roots02.json');require(roots['passed'] and len(roots['roots'])==84 and roots['independent_stages']==168 and roots['independent_nonlinear_rows']==38472 and not roots['full_trajectory_admitted'] and roots['wall_s']<=600,'fresh independent roots')
    for attempt in [1,2]:
        r=read(f'evidence/voice_dynamic_schur_diagnostic{attempt:02d}.json');require(not r['passed'] and len(r['commands'])==3 and r['commands'][0]['exit_code']==0 and all(c['exit_code']!=0 for c in r['commands'][1:]),'preserved diagnostic rejection')
    observations=read('evidence/voice_dynamic_schur_observations01.json');require(not observations['passed'] and observations['collection_passed'] and observations['identical_replay'] and not observations['full_trajectory_admitted'],'rejected observation scope');lines=observations['commands'][1]['stdout'].splitlines();linear=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('LINEAR,')];port=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('PORT,')];require(len(linear)==396 and len(port)==336 and observations['memory_observations']==1680 and observations['terminal_and_ground_currents']==2016,'observation coverage')
    require(max(x[0] for x in linear)<=1 and max(x[2] for x in port)<=1 and max(x[3] for x in port)<=2e-11,'correction/memory/current gates')
    require(sum(x[2]>1e-11 for x in linear)==20 and sum(x[6]>1e-11 for x in linear)==24 and observations['metrics']['schur_mixed_max']==max(x[2] for x in linear),'failed mixed gate remains visible')
    inspection=read('evidence/voice_dynamic_schur_scaled_inspection01.json');require(not inspection['passed'] and inspection['inspection_passed'] and inspection['exact_matrix_replay'] and inspection['identical_canonical_replay'] and inspection['precision']==100 and not inspection['numerical_gates_changed'],'reproducible exact rejection')
    structure=read('evidence/voice_dynamic_schur_structure01.json');require(structure['passed'] and structure['regressions']==9 and not structure['full_trajectory_admitted'],'finite rejection regressions')
    added=set(private)-set(old['private_input_sha256']);size=sum((ROOT/n).stat().st_size for n in added);require(size<=64*1024**2 and shutil.disk_usage(ROOT).free>=1024**3,'private/reserve budget')
    return dict(base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),private_input_sha256=private,new_private_bytes=size,benchmarks=benchmarks,selected_pairs=84,independent_nonlinear_rows_reexecuted=38472,linear_solves=396,observations=observations['metrics'],memory_observations=1680,terminal_and_ground_currents=2016,solver_regressions=9,lab_collection_verified=True,dynamic_schur_admitted=False,full_trajectory_admitted=False,rejected_gate='scaled backward <=1e-11',new_duration_s=0,new_audio=False,new_library_compile=False,new_spice_processes=0,physical_fidelity=False,real_time=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False)

def main():
    r=audit();write('evidence/voice_dynamic_schur_reference01.json',dict(passed=True,**r));print('SCHUR_LAB_REFERENCE',r['protected_public_sources'],len(r['private_input_sha256']),r['new_private_bytes'],'ADMITTED',r['dynamic_schur_admitted'])

if __name__=='__main__':main()
