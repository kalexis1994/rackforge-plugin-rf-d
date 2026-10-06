"""Exact observer-off control, then identical rejected trajectory with matrices."""
import json,os,subprocess,time
from pathlib import Path
import numpy as np
import voice_full_note_shadow_build as build
import voice_union_refine_runner as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT;WORK=build.WORK/'runs02'

def run(label,folder,name,trace):
    WORK.mkdir(parents=True,exist_ok=True);source=vco.read(folder/(name+'.json'))
    original=folder/(name+'.cir');export=folder/(name+'.txt')
    if vco.sha(original)!=source['deck_sha256'] or vco.sha(export)!=source['raw_export_sha256']:raise ValueError('reference deck/export identity')
    paths={x:WORK/(label+'.'+x) for x in ('cir','txt','log','json')}
    if any(p.exists() for p in paths.values()):raise ValueError('preserve observer run')
    old=('wrdata '+export.as_posix()+' ').encode();new=('wrdata '+paths['txt'].as_posix()+' ').encode()
    deck=original.read_bytes()
    if deck.count(old)!=1:raise ValueError('unique observer export anchor')
    paths['cir'].write_bytes(deck.replace(old,new,1))
    compiled=vco.read(build.WORK/'build.json');exe=build.WORK/'bin/observer.exe'
    if compiled['exit_code']!=0 or vco.sha(exe)!=compiled['executable_sha256']:raise ValueError('compiled observer identity')
    init=build.WORK/'init02/spinit';module=build.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    libs=[init,module,Path('C:/msys64/ucrt64/bin/libwinpthread-1.dll'),Path('C:/msys64/ucrt64/bin/libstdc++-6.dll'),Path('C:/msys64/ucrt64/bin/libgcc_s_seh-1.dll')]
    runtime={(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()):vco.sha(p) for p in libs}
    helpers={p.relative_to(ROOT).as_posix():vco.sha(p) for p in (Path(__file__),Path(build.__file__),Path(prior.__file__),Path(vco.__file__))}
    inputs=source['current_source_sha256'];env=os.environ.copy()
    for key in prior.FLAGS:env.pop(key,None)
    env.pop('RF_D_REFINE_SHADOW',None)
    env['RF_D_LINEAR_REFINE']='1'
    if trace:
        env['RF_D_MATRIX_TRACE']='1';env['RF_D_REFINE_SHADOW']='1'
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];env['SPICE_SCRIPTS']=init.parent.as_posix()
    r=dict(schema='rf-d/full-note-shadow-run/v1',label=label,reference_receipt_path=(folder/(name+'.json')).relative_to(ROOT).as_posix(),
        reference_receipt_sha256=vco.sha(folder/(name+'.json')),reference_deck_sha256=source['deck_sha256'],reference_raw_sha256=source['raw_export_sha256'],
        scenario=source['scenario'],vectors=source['vectors'],executable_sha256=vco.sha(exe),build_sha256=vco.sha(build.WORK/'build.json'),
        current_source_sha256=inputs,helper_sha256=helpers,runtime_sha256=runtime,deck_sha256=vco.sha(paths['cir']),
        command=[str(exe),'-n','-b',str(paths['cir'])],wall_limit_s=900,matrix_observation=trace,linear_refinement=True,shadow_enabled=trace,published_corrections=3,trajectory_complete=False)
    start=time.perf_counter()
    try:
        with paths['log'].open('wb') as log:
            p=subprocess.run(r['command'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        r['exit_code']=p.returncode
    except subprocess.TimeoutExpired:r['timeout']=True
    finally:
        r.update(wall_s=time.perf_counter()-start,log_sha256=vco.sha(paths['log']),executable_sha256_after=vco.sha(exe),
            current_source_sha256_after={n:vco.sha(ROOT/n) for n in inputs},helper_sha256_after={n:vco.sha(ROOT/n) for n in helpers},
            runtime_sha256_after={n:vco.sha(Path(n) if Path(n).is_absolute() else ROOT/n) for n in runtime})
        log=paths['log'].read_text(encoding='utf-8',errors='replace')
        r['activation_confirmed']='RFREFINE,active,three-corrections,pair-fma,all-real-NI' in log
        r['solver_failure_reported']=any(s in log.lower() for s in ('aborted','timestep too small','error:','rfrefine,error,'))
        r['matrix_begins']=log.count('RFMATRIX,begin,');r['matrix_ends']=log.count('RFMATRIX,end');r['shadow_final_rows']=log.count('RFSHADOW,final,')
        r['failure_lines']=[line for line in log.splitlines() if 'timestep too small' in line.lower()]
        if paths['txt'].exists():
            r['raw_export_sha256']=vco.sha(paths['txt'])
            try:
                a=np.loadtxt(paths['txt'],skiprows=1,ndmin=2);clock=source['scenario']['board']['oscillator']
                r.update(prior.clock_info(a,source['vectors'],clock['duration_s'],clock['max_step_s']))
            except Exception as e:r['export_error']=str(e)
        r['trajectory_complete']=bool(r.get('endpoint_complete') and r.get('max_step_passed') and r['activation_confirmed'] and not r['solver_failure_reported'] and not r.get('timeout') and r.get('exit_code')==0)
        paths['json'].write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(label,'complete:',r['trajectory_complete'],'last:',r.get('last_clock_s'),'captures:',r['matrix_begins'],flush=True)
    return r

def main():
    output=ROOT/'evidence/voice_full_note_shadow_runs02.json'
    if output.exists() or WORK.exists():raise ValueError('preserve observer bank')
    audit=vco.read(ROOT/'evidence/voice_union_refine_validation01.json')
    if not audit['passed'] or not audit['joint_admitted_locally']:raise ValueError('short control admission')
    before=vco.sha(Path(__file__));records={};control=None;observed=None
    try:
        r=run('control-off',prior.WORK,'joint-nominal500',False);records['control-off']=r
        a=np.loadtxt(WORK/'control-off.txt',skiprows=1,ndmin=2);b=np.loadtxt(prior.WORK/'joint-nominal500.txt',skiprows=1,ndmin=2)
        control=dict(passed=r['trajectory_complete'] and np.array_equal(a,b) and r['matrix_begins']==0 and r['shadow_final_rows']==0,
            rows=[len(a),len(b)],all_exported_values_and_clock_exact=bool(np.array_equal(a,b)))
        if not control['passed']:return
        folder=ROOT/'references-local/voice-circuit/full-note01';r=run('trap-on',folder,'nominal-trap125',True);records['trap-on']=r
        a=np.loadtxt(WORK/'trap-on.txt',skiprows=1,ndmin=2);b=np.loadtxt(folder/'nominal-trap125.txt',skiprows=1,ndmin=2)
        baseline_log=(folder/'nominal-trap125.log').read_text(encoding='utf-8',errors='replace')
        failure=[line for line in baseline_log.splitlines() if 'timestep too small' in line.lower()]
        exact=bool(np.array_equal(a,b));same_failure=failure==r['failure_lines']
        observed=dict(passed=exact and same_failure and r['solver_failure_reported'] and not r.get('timeout') and 0<r['matrix_begins']<=16 and r['matrix_begins']==r['matrix_ends'] and r['shadow_final_rows']==226*r['matrix_begins'],
            rows=[len(a),len(b)],all_exported_values_and_clock_exact=exact,same_failure_lines=same_failure,
            captured_systems=r['matrix_begins'],capture_limit=16,capture_limit_reached=r['matrix_begins']==16)
    finally:
        report=dict(schema='rf-d/full-note-shadow-bank/v1',records=records,control=control,observation=observed,
            shadow_observer_admitted_locally=bool(control and control['passed'] and observed and observed['passed']),
            helper_sha256=before,helper_sha256_after=vco.sha(Path(__file__)),protocol_sha256=vco.sha(ROOT/build.PROTOCOL),
            build_sha256=vco.sha(build.WORK/'build.json'),measured_solves=len(records),cause_identified=False,long_note_admitted=False,new_audio=False)
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('long-note matrix observer admitted:',report['shadow_observer_admitted_locally'],flush=True)

if __name__=='__main__':main()
