"""Pinned build08, exact temporal patches and preserved long-run receipts."""
import json,os,subprocess,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
import voice_full_note as note
import voice_union_refine_runner as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT;WORK=note.WORK

def run(name):
    WORK.mkdir(parents=True,exist_ok=True)
    paths={suffix:WORK/(name+'.'+suffix) for suffix in ('cir','txt','log','json')}
    if any(p.exists() for p in paths.values()):raise ValueError('preserve prior long run')
    source=prior.frozen('joint',name);s=note.scenes()[name]
    if prior.canonical(source['original_receipt']['scenario'])!=prior.canonical(asdict(note.short.scenes()[name])):raise ValueError('historical short scenario identity')
    deck,patch=note.patch(source['deck'].read_bytes(),name,source['original_export'],paths['txt'].as_posix())
    folder,file,digest=prior.BINARIES['candidate'];runtime_root=ROOT/'references-local/voice-circuit'/folder
    exe=runtime_root/'bin'/file;init=runtime_root/'init02/spinit'
    if vco.sha(exe)!=digest:raise ValueError('pinned build08 executable')
    libraries=[init,runtime_root/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm',
        Path('C:/msys64/ucrt64/bin/libwinpthread-1.dll'),Path('C:/msys64/ucrt64/bin/libstdc++-6.dll'),
        Path('C:/msys64/ucrt64/bin/libgcc_s_seh-1.dll')]
    runtime={(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()):vco.sha(p) for p in libraries}
    helpers=[Path(__file__),Path(note.__file__),Path(prior.__file__),Path(vco.__file__)]
    helper={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    env=os.environ.copy()
    for flag in prior.FLAGS:env.pop(flag,None)
    env['RF_D_LINEAR_REFINE']='1';env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];env['SPICE_SCRIPTS']=init.parent.as_posix()
    paths['cir'].write_bytes(deck)
    r=dict(schema='rf-d/full-note-run/v1',scene=name,scenario=asdict(s),vectors=s.vectors,patch=patch,
        original_deck_path=source['deck'].relative_to(ROOT).as_posix(),original_deck_sha256=vco.sha(source['deck']),
        archive=source['archive'],archive_sha256=source['archive_sha256'],historical_commit=source['original_receipt']['git_commit'],
        historical_source_sha256=source['original_receipt']['source_sha256'],historical_source_modes=source['historical_source_modes'],
        current_source_sha256=source['current_source_sha256'],helper_sha256=helper,runtime_sha256=runtime,
        executable_path=exe.relative_to(ROOT).as_posix(),executable_sha256=digest,deck_sha256=vco.sha(paths['cir']),
        command=[str(exe),'-n','-b',str(paths['cir'])],wall_limit_s=7200,process_started=False,trajectory_complete=False,
        refinement_enabled=True,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        physical_fidelity=False,real_time=False)
    start=time.perf_counter()
    try:
        with paths['log'].open('wb') as log:
            p=subprocess.Popen(r['command'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            r['process_started']=True
            try:r['exit_code']=p.wait(timeout=7200)
            except subprocess.TimeoutExpired:
                p.kill();p.wait();r.update(timeout=True,exit_code_after_timeout=p.returncode)
    except Exception as e:r['launch_error']=str(e)
    finally:
        r.update(wall_s=time.perf_counter()-start,log_sha256=vco.sha(paths['log']),executable_sha256_after=vco.sha(exe),
            current_source_sha256_after={n:vco.sha(ROOT/n) for n in source['current_source_sha256']},
            helper_sha256_after={n:vco.sha(ROOT/n) for n in helper},
            runtime_sha256_after={n:vco.sha(Path(n) if Path(n).is_absolute() else ROOT/n) for n in runtime})
        log=paths['log'].read_text(encoding='utf-8',errors='replace')
        r['solver_failure_reported']=any(x in log.lower() for x in ('aborted','timestep too small','error:','rfrefine,error,'))
        r['refinement_activation_confirmed']='RFREFINE,active,three-corrections,pair-fma,all-real-NI' in log
        if paths['txt'].exists():
            r['raw_export_sha256']=vco.sha(paths['txt']);r['raw_export_bytes']=paths['txt'].stat().st_size
            try:
                raw=np.loadtxt(paths['txt'],skiprows=1,ndmin=2)
                r.update(prior.clock_info(raw,s.vectors,.35,s.oscillator.max_step_s))
            except Exception as e:r['export_error']=str(e)
        r['trajectory_complete']=bool(r.get('endpoint_complete') and r.get('max_step_passed') and
            not r['solver_failure_reported'] and r['refinement_activation_confirmed'] and
            not r.get('timeout') and not r.get('launch_error') and r.get('exit_code')==0)
        paths['json'].write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(name,'complete:',r['trajectory_complete'],'last:',r.get('last_clock_s'),'wall:',round(r['wall_s'],2),flush=True)
    return r
