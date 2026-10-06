"""Pinned local runtimes, exact historical decks, immutable receipts, 900s budget."""
import gzip,json,os,subprocess,time
from pathlib import Path
import numpy as np
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity
import voice_circuit_reference as nominal
import loudness_voice_circuit as joint

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/union-refine01'
BINARIES={
    'original':('newton-build06','observer.exe','0a71b6d811699739330781bb2256e0ad24969a37c31112d28f805e7e1048a5de'),
    'candidate':('newton-build08','candidate.exe','f45c7a3421d480e361b22a66e8feb0e9a4ca91dedaa816afa400ae54765accdd')}
FLAGS=('RF_D_LINEAR_REFINE','RF_D_REFINE_REPLAY','RF_D_MATRIX_TRACE','RF_D_TRACE','RF_D_741_REDUCE')
HISTORICAL_HELPER=('tools/loudness_voice_circuit.py','5adb236c5efc00245967765ab32bbbc358dddf68a3d0cfdaed8f9af8bfcda560','0ac19726aacb8bdae0ec7404600b79f5ec83ef5e9462f915d853187243f4dc12')

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()

def frozen(kind,scene):
    archive=ROOT/'evidence'/('voice_circuit_klu_bank01.json.gz' if kind=='nominal' else 'loudness_voice_screen01.json.gz')
    bank=json.loads(gzip.decompress(archive.read_bytes()));r=bank['cases'][scene]['receipt']
    folder=ROOT/'references-local/voice-circuit'/bank['bank'];deck=folder/(r['label']+'.cir')
    if vco.sha(deck)!=r['deck_sha256'] or canonical(vco.read(folder/(r['label']+'.json')))!=canonical(r):raise ValueError('historical deck/receipt identity')
    vectors=nominal.VECTORS if kind=='nominal' else joint.VECTORS
    lines=[line for line in deck.read_text(encoding='utf-8').splitlines() if line.startswith('wrdata ')]
    if len(lines)!=1 or lines[0].split()[2:]!=vectors:raise ValueError('frozen vector order')
    export=lines[0].split()[1];historical={};current={}
    for name,digest in r['source_sha256'].items():
        actual=vco.sha(ROOT/name);current[name]=actual
        if name.startswith('references-local/'):
            if actual!=digest:raise ValueError('private electrical input changed')
            historical[name]='identified-private-file'
        else:
            blob=subprocess.check_output(['git','show',r['git_commit']+':'+name],cwd=ROOT)
            historical[name]=source_identity(name,digest,blob)
            if actual!=digest and (name,digest,actual)!=HISTORICAL_HELPER:raise ValueError('undeclared historical source divergence')
    return dict(archive=archive.relative_to(ROOT).as_posix(),archive_sha256=vco.sha(archive),original_receipt=r,
        deck=deck,original_export=export,vectors=vectors,current_source_sha256=current,historical_source_modes=historical)

def clock_info(raw,vectors,duration,max_step):
    if raw.ndim!=2 or raw.shape[1]!=len(vectors)+1 or len(raw)<2 or not np.isfinite(raw).all():raise ValueError('finite full vector export required')
    if raw[0,0]!=0 or np.any(np.diff(raw[:,0])<=0):raise ValueError('strict clock from zero')
    dt=float(np.diff(raw[:,0]).max())
    return dict(rows=len(raw),last_clock_s=float(raw[-1,0]),max_step_observed_s=dt,
        endpoint_complete=abs(float(raw[-1,0])-duration)<=1e-14,max_step_passed=dt<=max_step*(1+1e-7))

def run(kind,scene,label,binary,enabled=False):
    WORK.mkdir(parents=True,exist_ok=True)
    paths={suffix:WORK/(label+'.'+suffix) for suffix in ('cir','txt','log','json')}
    if any(p.exists() for p in paths.values()):raise ValueError('preserve previous run')
    source=frozen(kind,scene);folder,file,digest=BINARIES[binary]
    runtime_root=ROOT/'references-local/voice-circuit'/folder;exe=runtime_root/'bin'/file
    if vco.sha(exe)!=digest or (enabled and binary!='candidate'):raise ValueError('pinned executable/flag scope')
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
    helpers=[Path(__file__),ROOT/'tools/vco1_circuit_reference.py',ROOT/'tools/validate_loudness_board4_bank.py']
    helper={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    original=source['original_receipt'];scenario=original['scenario'];clock=scenario['oscillator'] if kind=='nominal' else scenario['board']['oscillator']
    report=dict(schema='rf-d/union-refine-run/v1',label=label,kind=kind,scene=scene,scenario=scenario,vectors=source['vectors'],
        archive=source['archive'],archive_sha256=source['archive_sha256'],original_receipt=original,
        historical_source_modes=source['historical_source_modes'],current_source_sha256=source['current_source_sha256'],
        executable_path=exe.relative_to(ROOT).as_posix(),executable_sha256=digest,refinement_enabled=enabled,
        runtime_sha256=runtime,helper_sha256=helper,deck_sha256=vco.sha(paths['cir']),wall_limit_s=900,
        command=[str(exe),'-n','-b',str(paths['cir'])],trajectory_complete=False,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        physical_fidelity=False,real_time=False)
    start=time.perf_counter()
    try:
        with paths['log'].open('wb') as stream:
            p=subprocess.run(report['command'],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=900)
        report['exit_code']=p.returncode
    except subprocess.TimeoutExpired:report['timeout']=True
    finally:
        report.update(wall_s=time.perf_counter()-start,log_sha256=vco.sha(paths['log']),
            executable_sha256_after=vco.sha(exe),current_source_sha256_after={n:vco.sha(ROOT/n) for n in source['current_source_sha256']},
            helper_sha256_after={n:vco.sha(ROOT/n) for n in helper},runtime_sha256_after={n:vco.sha(Path(n) if Path(n).is_absolute() else ROOT/n) for n in runtime})
        text=paths['log'].read_text(encoding='utf-8',errors='replace')
        report['solver_failure_reported']=any(s in text.lower() for s in ('aborted','timestep too small','error:','rfrefine,error,'))
        report['refinement_activation_confirmed']='RFREFINE,active,three-corrections,pair-fma,all-real-NI' in text
        if paths['txt'].exists():
            report['raw_export_sha256']=vco.sha(paths['txt'])
            try:
                raw=np.loadtxt(paths['txt'],skiprows=1,ndmin=2)
                report.update(clock_info(raw,source['vectors'],clock['duration_s'],clock['max_step_s']))
            except Exception as e:report['export_error']=str(e)
        report['trajectory_complete']=bool(report.get('endpoint_complete') and report.get('max_step_passed') and not report['solver_failure_reported'] and not report.get('timeout') and report.get('exit_code')==0)
        paths['json'].write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(label,'complete:',report['trajectory_complete'],'last:',report.get('last_clock_s'),'wall:',round(report['wall_s'],2),flush=True)
    return report
