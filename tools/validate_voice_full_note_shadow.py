"""Audit observer-only source changes and exact rejected-trajectory capture."""
import json,subprocess
from pathlib import Path
import numpy as np
import voice_full_note_shadow_build as build
import voice_full_note_shadow_probe_retry as probe
import voice_full_note_matrix_trace as matrix
import voice_refine_trace as refine
import voice_union_refine_runner as prior
import vco1_circuit_reference as vco
from validate_voice_refine import sources

ROOT=vco.ROOT

def build_identity():
    if sources()!=vco.read(ROOT/'evidence/voice_union_refine_validation01.json')['source_reports']:raise ValueError('original refined-source chain')
    path=ROOT/'evidence/voice_full_note_shadow_build01.json';r=vco.read(path)
    if prior.canonical(r)!=prior.canonical(vco.read(build.WORK/'build.json')) or r['exit_code']!=0:raise ValueError('observer compile receipt')
    failure=vco.read(ROOT/'evidence/voice_full_note_shadow_preparation_rejection01.json')
    old=ROOT/'tools/voice_full_note_shadow_probe.py'
    if vco.sha(old)!=failure['helper_sha256'] or Path(probe.__file__).read_bytes()!=old.read_bytes().replace(b"WORK=build.WORK/'runs'",b"WORK=build.WORK/'runs02'").replace(b'voice_full_note_shadow_runs01.json',b'voice_full_note_shadow_runs02.json'):raise ValueError('preserved preparation failure and exact retry')
    if failure['measured_spice_solves'] or failure['executable_launched']:raise ValueError('preparation failure scope')
    for n,h in failure['preserved_files'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('failed preparation bytes')
    if vco.sha(Path(build.__file__))!=r['helper_sha256'] or r['helper_sha256']!=r['helper_sha256_after'] or vco.sha(ROOT/build.PROTOCOL)!=r['protocol_sha256']:raise ValueError('observer preparation identity')
    original=(build.PRIOR/'ngspice-46'/build.NAME).read_text(encoding='utf-8')
    if (build.TREE/build.NAME).read_bytes()!=build.patched(original).encode():raise ValueError('declared observer patch only')
    a=build.inventory(build.PRIOR/'ngspice-46');b=build.inventory(build.TREE)
    if set(a)!=set(b) or [n for n in a if a[n]!=b[n]]!=[build.NAME] or len(a)!=r['source_files']:raise ValueError('source inventory scope')
    if prior.canonical(vco.read(build.WORK/'source-inventory.json'))!=prior.canonical(dict(before=a,after=b)) or vco.sha(build.WORK/'source-inventory.json')!=r['source_inventory_sha256']:raise ValueError('source inventory receipt')
    if r['patch']['before_sha256']!=a[build.NAME] or r['patch']['after_sha256']!=b[build.NAME]:raise ValueError('patch hashes')
    original_build=vco.read(build.PRIOR/'build.json')
    if vco.sha(build.PRIOR/'build.json')!=r['prior_build_sha256'] or r['compiler_sha256']!=original_build['compiler_sha256'] or r['compiler_sha256_after']!=r['compiler_sha256'] or vco.sha(Path(r['compiler_path']))!=r['compiler_sha256']:raise ValueError('compiler/configuration inheritance')
    if r['available_free_bytes']<r['copy_bytes']+r['estimated_exports_bytes']+r['margin_bytes'] or r['margin_bytes']!=2*1024**3 or r['shadow_corrections']!=6 or r['published_corrections']!=3:raise ValueError('shadow budget/scope')
    if r['cflags']!=original_build['cflags'] or r['ldflags']!=original_build['ldflags'] or r['corrections']!=3 or r['numerical_algorithm_changed'] or r['device_stamps_changed'] or r['state_update_changed']:raise ValueError('arithmetic/physical scope')
    for name,pair in r['relocated_generated_files'].items():
        if vco.sha(build.PRIOR/name)!=pair['before_sha256'] or vco.sha(build.WORK/name)!=pair['after_sha256']:raise ValueError('generated configuration relocation')
    if vco.sha(build.WORK/'build.log')!=r['build_log_sha256'] or vco.sha(build.WORK/'bin/observer.exe')!=r['executable_sha256']:raise ValueError('compiled observer bytes')
    return dict(build_sha256=vco.sha(path),source_files=len(a),changed_source=build.NAME,
        preserved_preflight_rejection_sha256=vco.sha(ROOT/'evidence/voice_full_note_shadow_preparation_rejection01.json'),
        compiler_sha256=r['compiler_sha256'],executable_sha256=r['executable_sha256'],numerical_algorithm_changed=False)

def main():
    output=ROOT/'evidence/voice_full_note_shadow_validation01.json'
    if output.exists():raise ValueError('preserve matrix audit')
    compilation=build_identity();path=ROOT/'evidence/voice_full_note_shadow_runs02.json';bank=vco.read(path)
    if bank['helper_sha256']!=bank['helper_sha256_after'] or bank['helper_sha256']!=vco.sha(Path(probe.__file__)) or bank['build_sha256']!=vco.sha(build.WORK/'build.json') or bank['protocol_sha256']!=vco.sha(ROOT/build.PROTOCOL):raise ValueError('observer bank source scope')
    data={};reference={}
    for label,r in bank['records'].items():
        work=probe.WORK;rp=ROOT/r['reference_receipt_path'];rr=vco.read(rp)
        if vco.sha(rp)!=r['reference_receipt_sha256'] or prior.canonical(vco.read(work/(label+'.json')))!=prior.canonical(r):raise ValueError('run receipts')
        source_deck=rp.with_suffix('.cir');source_export=rp.with_suffix('.txt')
        old=('wrdata '+source_export.as_posix()+' ').encode();new=('wrdata '+(work/(label+'.txt')).as_posix()+' ').encode()
        if vco.sha(source_deck)!=r['reference_deck_sha256'] or source_deck.read_bytes().count(old)!=1 or (work/(label+'.cir')).read_bytes()!=source_deck.read_bytes().replace(old,new,1) or vco.sha(work/(label+'.cir'))!=r['deck_sha256']:raise ValueError('observer export-only deck')
        for key in ('current_source_sha256','helper_sha256','runtime_sha256'):
            if r[key]!=r[key+'_after']:raise ValueError('observer inputs changed')
            for name,digest in r[key].items():
                if vco.sha(Path(name) if Path(name).is_absolute() else ROOT/name)!=digest:raise ValueError('observer input bytes')
        if r['executable_sha256']!=compilation['executable_sha256'] or r['executable_sha256_after']!=r['executable_sha256'] or r['wall_limit_s']!=900:raise ValueError('observer binary/budget')
        logp=work/(label+'.log');log=logp.read_text(encoding='utf-8',errors='replace')
        if vco.sha(logp)!=r['log_sha256']:raise ValueError('observer log')
        active='RFREFINE,active,three-corrections,pair-fma,all-real-NI' in log
        failed=any(s in log.lower() for s in ('aborted','timestep too small','error:','rfrefine,error,'))
        if active!=r['activation_confirmed'] or failed!=r['solver_failure_reported'] or r['failure_lines']!=[line for line in log.splitlines() if 'timestep too small' in line.lower()]:raise ValueError('active solver/failure scope')
        if any(x in log for x in ('RFREFINE,replay,','RFTRACE,','RFLTRACE,','RFKTRACE,','RF741REDUCE,')):raise ValueError('other instrumentation disabled')
        if r['current_source_sha256']!=rr['current_source_sha256'] or r['scenario']!=rr['scenario'] or r['vectors']!=rr['vectors']:raise ValueError('reference inputs and scenario')
        enabled=label=='trap-on'
        if r['shadow_enabled']!=enabled or r['published_corrections']!=3 or r['shadow_final_rows']!=log.count('RFSHADOW,final,') or r['matrix_observation']!=enabled or r['matrix_begins']!=log.count('RFMATRIX,begin,') or r['matrix_ends']!=log.count('RFMATRIX,end'):raise ValueError('observer activation')
        for p,digest in ((work/(label+'.txt'),r['raw_export_sha256']),(source_export,r['reference_raw_sha256'])):
            if vco.sha(p)!=digest:raise ValueError('observer/reference export')
        a=np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2);b=np.loadtxt(source_export,skiprows=1,ndmin=2)
        clock=rr['scenario']['board']['oscillator'];info=prior.clock_info(a,rr['vectors'],clock['duration_s'],clock['max_step_s'])
        for key,value in info.items():
            if r[key]!=value:raise ValueError('observer clock receipt')
        complete=bool(info['endpoint_complete'] and info['max_step_passed'] and active and not failed and not r.get('timeout') and r.get('exit_code')==0)
        if complete!=r['trajectory_complete']:raise ValueError('observer complete trajectory gate')
        data[label]=a;reference[label]=b
    c=bank['records']['control-off'];exact=bool(np.array_equal(data['control-off'],reference['control-off']))
    control=dict(passed=c['trajectory_complete'] and exact and c['matrix_begins']==0 and c['shadow_final_rows']==0,rows=[len(data['control-off']),len(reference['control-off'])],all_exported_values_and_clock_exact=exact)
    if control!=bank['control'] or not control['passed']:raise ValueError('observer-off full control rejected')
    r=bank['records']['trap-on'];exact=bool(np.array_equal(data['trap-on'],reference['trap-on']))
    baseline_log=(ROOT/r['reference_receipt_path']).with_suffix('.log').read_text(encoding='utf-8',errors='replace')
    failure=[line for line in baseline_log.splitlines() if 'timestep too small' in line.lower()]
    observation=dict(passed=exact and failure==r['failure_lines'] and r['solver_failure_reported'] and not r.get('timeout') and 0<r['matrix_begins']<=16 and r['matrix_begins']==r['matrix_ends'] and r['shadow_final_rows']==226*r['matrix_begins'],
        rows=[len(data['trap-on']),len(reference['trap-on'])],all_exported_values_and_clock_exact=exact,same_failure_lines=failure==r['failure_lines'],
        captured_systems=r['matrix_begins'],capture_limit=16,capture_limit_reached=r['matrix_begins']==16)
    if observation!=bank['observation'] or not observation['passed'] or not bank['shadow_observer_admitted_locally']:raise ValueError('captured trajectory identity rejected')
    text=(probe.WORK/'trap-on.log').read_text(encoding='utf-8');snapshots=matrix.parse(text);details=refine.parse(text)
    if len(snapshots)!=len(details) or len(snapshots)!=observation['captured_systems']:raise ValueError('complete CSC/refinement coverage')
    previous=(build.PRIOR/'runs/trap-on.log').read_text(encoding='utf-8')
    def packed(group):return [dict(s,entries=sorted((i,j,v) for (i,j),v in s['entries'].items())) for s in group]
    if prior.canonical(packed(snapshots))!=prior.canonical(packed(matrix.parse(previous))) or prior.canonical(details)!=prior.canonical(refine.parse(previous)):raise ValueError('captured matrices/three corrections changed')
    contexts=[]
    for s,d in zip(snapshots,details):
        if s['n']!=d['n'] or any(s['x'][i]!=d['final'][i] for i in range(s['n'])):raise ValueError('single published refined vector')
        contexts.append({k:s[k] for k in ('time_s','h_s','iteration','order','mode','n','nz','diag_gmin')})
    helpers=[Path(__file__),Path(build.__file__),Path(probe.__file__),Path(matrix.__file__),Path(refine.__file__)]
    report=dict(schema='rf-d/full-note-shadow-validation/v1',passed=True,compilation=compilation,
        bank_sha256=vco.sha(path),control=control,observation=observation,capture_contexts=contexts,
        measured_solves=len(bank['records']),new_solves_during_validation=0,observer_admitted_locally=True,
        captured_systems=len(snapshots),precise_roots_computed=False,numerical_algorithm_changed=False,
        analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        cause_identified=False,long_note_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('observer audit:',len(snapshots),'complete systems; exact partial trajectory',flush=True)

if __name__=='__main__':main()
