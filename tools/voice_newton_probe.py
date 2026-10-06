"""Private instrumented SPICE runs with immutable receipts and exact trace gates."""
import gzip,json,os,subprocess,time
from pathlib import Path
import numpy as np
import voice_newton_instrument as instrument
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=instrument.WORK
OFFICIAL=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
BANK=ROOT/'evidence/voice_port_behavioral01.json.gz'


def original(kind):
    if kind not in ('constant','returned'):raise ValueError('frozen scenario required')
    bank=json.loads(gzip.decompress(BANK.read_bytes()))
    index=0 if kind=='constant' else 2
    receipt=bank['cases']['fixed-contour-control']['iterations'][index]['vco_receipt']
    folder=ROOT/'references-local/voice-circuit'/bank['bank']
    deck=folder/(receipt['label']+'.cir');raw=folder/(receipt['label']+'.txt')
    if vco.sha(deck)!=receipt['deck_sha256'] or vco.sha(raw)!=receipt.get('raw_export_sha256',receipt.get('partial_export_sha256')):
        raise ValueError('frozen circuit and observation identity')
    return deck,raw,receipt


def exact(a,b):
    if a.ndim!=2 or b.ndim!=2 or len(a)<2 or len(b)<2 or a.shape[1]!=7 or b.shape[1]!=7 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('finite time and six observations required')
    if a[0,0]!=0 or b[0,0]!=0 or np.any(np.diff(a[:,0])<=0) or np.any(np.diff(b[:,0])<=0):
        raise ValueError('strictly increasing clock from zero required')
    return dict(passed=a.shape==b.shape and bool(np.array_equal(a,b)),rows=[len(a),len(b)],
                last_clock_s=[float(a[-1,0]),float(b[-1,0])])


def run(exe,kind,label,trace=False):
    # This runner is diagnostic only: the production runner keeps its official EXE gate.
    folder=WORK/'runs';folder.mkdir(exist_ok=True)
    deck=folder/(label+'.cir');export=folder/(label+'.txt');log=folder/(label+'.log');receipt=folder/(label+'.json')
    if any(p.exists() for p in (deck,export,log,receipt)):raise ValueError('preserve previous probe')
    old,oldraw,r=original(kind);text=old.read_text(encoding='utf-8')
    marker='wrdata '+oldraw.as_posix()+' '
    if text.count(marker)!=1:raise ValueError('unique export anchor required')
    deck.write_text(text.replace(marker,'wrdata '+export.as_posix()+' ',1),encoding='utf-8',newline='\n')
    inputs={name:vco.sha(ROOT/name) for name in r['source_sha256']}
    if inputs!=r['source_sha256']:raise ValueError('original circuit source changed')
    helpers={Path(__file__).relative_to(ROOT).as_posix():vco.sha(Path(__file__)),
             Path(instrument.__file__).relative_to(ROOT).as_posix():vco.sha(Path(instrument.__file__))}
    env=os.environ.copy();env.pop('RF_D_TRACE',None)
    if trace:env['RF_D_TRACE']='1'
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    # The TI 741 POLY source is translated through this locally compiled module.
    init=WORK/'init/spinit';module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    if not init.exists() or not module.exists():raise ValueError('local XSPICE poly initialization required')
    env['SPICE_SCRIPTS']=init.parent.as_posix()
    libraries=(init,module,Path('C:/msys64/ucrt64/bin/libwinpthread-1.dll'),
               Path('C:/msys64/ucrt64/bin/libstdc++-6.dll'),Path('C:/msys64/ucrt64/bin/libgcc_s_seh-1.dll'))
    runtime={(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()):vco.sha(p) for p in libraries}
    report=dict(label=label,scenario=kind,original_receipt=r,exe_path=exe.relative_to(ROOT).as_posix(),
                exe_sha256=vco.sha(exe),deck_sha256=vco.sha(deck),source_sha256=inputs,
                helper_sha256=helpers,runtime_sha256=runtime,trace_enabled=trace,diagnostic_only=True,
                git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    start=time.perf_counter()
    try:
        with log.open('wb') as stream:
            p=subprocess.run([str(exe),'-n','-b',str(deck)],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120)
        report['exit_code']=p.returncode
    except subprocess.TimeoutExpired:
        report['timeout']=True
    finally:
        report.update(wall_s=time.perf_counter()-start,log_sha256=vco.sha(log),
                      source_sha256_after={name:vco.sha(ROOT/name) for name in inputs},
                      exe_sha256_after=vco.sha(exe),helper_sha256_after={name:vco.sha(ROOT/name) for name in helpers})
        report['runtime_sha256_after']={name:vco.sha(ROOT/name) for name in runtime}
        if export.exists():
            raw=np.loadtxt(export,skiprows=1,ndmin=2)
            exact(raw,raw)
            report.update(raw_export_sha256=vco.sha(export),rows=len(raw),last_clock_s=float(raw[-1,0]),
                          exact_official_trace=exact(raw,np.loadtxt(oldraw,skiprows=1,ndmin=2)))
        text=log.read_text(encoding='utf-8',errors='replace')
        report['trajectory_complete']=export.exists() and not any(s in text.lower() for s in ('aborted','timestep too small','error:')) and abs(report['last_clock_s']-.04)<1e-14 and report.get('exit_code')==0
        report['reset_failure_reported']='Timestep too small' in text
        receipt.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(label,report['trajectory_complete'],report.get('last_clock_s'),report.get('exact_official_trace',{}).get('passed'),flush=True)
    return report


def main(stage):
    if stage=='baseline-xspice02':
        exe=WORK/'bin/baseline-xspice.exe'
        for kind in ('constant','returned'):run(exe,kind,'baseline-xspice02-'+kind)
    elif stage=='instrumented':
        exe=WORK/'bin/instrumented.exe'
        for kind in ('constant','returned'):
            run(exe,kind,'instrumented-off-'+kind)
            run(exe,kind,'instrumented-on-'+kind,True)
    else:raise ValueError('explicit stage required')


if __name__=='__main__':
    import sys
    main(sys.argv[1])
