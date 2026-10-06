"""Pinned local runtimes, exact historical decks, immutable receipts, 900s budget."""
import gzip,json,os,subprocess,time
from pathlib import Path
import numpy as np
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity
import voice_circuit_reference as nominal
import loudness_voice_circuit as joint
import voice_union_refine_runner as prior
import voice_six_build as build

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/active-six-short01'
FLAGS=prior.FLAGS+('RF_D_REFINE_SHADOW',)
ANNOUNCEMENT='RFREFINE,active,six-corrections,pair-fma,all-real-NI'
INSTRUMENTATION=('RFMATRIX,','RFREFINE,replay,','RFTRACE,','RFLTRACE,','RFKTRACE,','RF741REDUCE,','RFSHADOW,')
frozen=prior.frozen;clock_info=prior.clock_info;canonical=prior.canonical

def candidate():
    r=vco.read(build.WORK/'build.json');exe=build.WORK/'bin/candidate.exe'
    if r['exit_code']!=0 or r['published_corrections']!=6 or vco.sha(exe)!=r['executable_sha256'] or vco.sha(Path(build.__file__))!=r['helper_sha256']:raise ValueError('completed compiled six candidate required')
    return r,exe

def log_status(text,enabled):
    announcements=[s for s in text.splitlines() if s.startswith('RFREFINE,active,')]
    active=announcements==[ANNOUNCEMENT]
    unwanted=any(x in text for x in INSTRUMENTATION)
    unexpected=any(s!=ANNOUNCEMENT for s in announcements) or len(announcements)>1
    failed=any(s in text.lower() for s in ('aborted','timestep too small','error:','rfrefine,error,'))
    return dict(solver_failure_reported=failed,refinement_activation_confirmed=active,
        unwanted_instrumentation=unwanted,unexpected_correction_announcement=unexpected,
        activation_gate_passed=active==enabled and not unwanted and not unexpected and not failed)

def run(kind,scene,label,enabled=False):
    WORK.mkdir(parents=True,exist_ok=True)
    paths={suffix:WORK/(label+'.'+suffix) for suffix in ('cir','txt','log','json')}
    if any(p.exists() for p in paths.values()):raise ValueError('preserve previous run')
    source=frozen(kind,scene);compiled,exe=candidate();digest=compiled['executable_sha256']
    runtime_root=build.WORK
    old=source['deck'].read_bytes();marker=('wrdata '+source['original_export']+' ').encode()
    if old.count(marker)!=1:raise ValueError('unique export anchor')
    paths['cir'].write_bytes(old.replace(marker,('wrdata '+paths['txt'].as_posix()+' ').encode(),1))
    init=runtime_root/'init02/spinit';module=runtime_root/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    libraries=[init,module,Path('C:/msys64/ucrt64/bin/libwinpthread-1.dll'),Path('C:/msys64/ucrt64/bin/libstdc++-6.dll'),Path('C:/msys64/ucrt64/bin/libgcc_s_seh-1.dll')]
    runtime={(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()):vco.sha(p) for p in libraries}
    env=os.environ.copy()
    for flag in FLAGS:env.pop(flag,None)
    if enabled:env['RF_D_LINEAR_REFINE']='1'
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];env['SPICE_SCRIPTS']=init.parent.as_posix()
    helpers=[Path(__file__),Path(build.__file__),Path(prior.__file__),ROOT/'tools/vco1_circuit_reference.py',ROOT/'tools/validate_loudness_board4_bank.py']
    helper={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    original=source['original_receipt'];scenario=original['scenario'];clock=scenario['oscillator'] if kind=='nominal' else scenario['board']['oscillator']
    report=dict(schema='rf-d/active-six-short-run/v1',label=label,kind=kind,scene=scene,scenario=scenario,vectors=source['vectors'],
        archive=source['archive'],archive_sha256=source['archive_sha256'],original_receipt=original,
        historical_source_modes=source['historical_source_modes'],current_source_sha256=source['current_source_sha256'],
        executable_path=exe.relative_to(ROOT).as_posix(),executable_sha256=digest,refinement_enabled=enabled,
        runtime_sha256=runtime,helper_sha256=helper,deck_sha256=vco.sha(paths['cir']),wall_limit_s=900,
        command=[str(exe),'-n','-b',str(paths['cir'])],trajectory_complete=False,process_started=False,published_corrections=6,build_sha256=vco.sha(build.WORK/'build.json'),controlled_environment={f:env.get(f) for f in FLAGS},
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        physical_fidelity=False,real_time=False)
    compiled_source={build.NAME:vco.sha(build.TREE/build.NAME)}
    report['compiled_source_sha256']=compiled_source
    start=time.perf_counter()
    try:
        with paths['log'].open('wb') as stream:
            p=subprocess.Popen(report['command'],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            report['process_started']=True
            try:report['exit_code']=p.wait(timeout=900)
            except subprocess.TimeoutExpired:
                p.kill();report['exit_code']=p.wait();report['timeout']=True
    except OSError as e:report['launch_error']=str(e)
    finally:
        report.update(wall_s=time.perf_counter()-start,log_sha256=vco.sha(paths['log']),
            executable_sha256_after=vco.sha(exe),current_source_sha256_after={n:vco.sha(ROOT/n) for n in source['current_source_sha256']},
            helper_sha256_after={n:vco.sha(ROOT/n) for n in helper},runtime_sha256_after={n:vco.sha(Path(n) if Path(n).is_absolute() else ROOT/n) for n in runtime})
        report['compiled_source_sha256_after']={n:vco.sha(build.TREE/n) for n in compiled_source}
        text=paths['log'].read_text(encoding='utf-8',errors='replace')
        report.update(log_status(text,enabled))
        if paths['txt'].exists():
            report['raw_export_sha256']=vco.sha(paths['txt']);report['raw_export_bytes']=paths['txt'].stat().st_size
            try:
                raw=np.loadtxt(paths['txt'],skiprows=1,ndmin=2)
                report.update(clock_info(raw,source['vectors'],clock['duration_s'],clock['max_step_s']))
            except Exception as e:report['export_error']=str(e)
        report['trajectory_complete']=bool(report.get('endpoint_complete') and report.get('max_step_passed') and not report['solver_failure_reported'] and not report.get('timeout') and not report.get('launch_error') and not report['unwanted_instrumentation'] and not report['unexpected_correction_announcement'] and report['refinement_activation_confirmed']==enabled and report.get('exit_code')==0)
        paths['json'].write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(label,'complete:',report['trajectory_complete'],'last:',report.get('last_clock_s'),'wall:',round(report['wall_s'],2),flush=True)
    return report
