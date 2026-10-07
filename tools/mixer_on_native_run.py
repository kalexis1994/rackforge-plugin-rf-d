"""Capture the targeted native circuit tests, toolchain and resource gate."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from mixer_on_native_vectors import ROOT,sha

SOURCES=('.gitattributes','Cargo.toml','Cargo.lock','crates/rf-d-circuit/Cargo.toml',
         'crates/rf-d-circuit/src/lib.rs','crates/rf-d-circuit/src/mixer_on.rs',
         'crates/rf-d-circuit/tests/mixer_on.rs','crates/rf-d-circuit/tests/mixer_on_no_alloc.rs',
         'tools/mixer_on_native_vectors.py','tools/mixer_on_native_run.py',
         'docs/MEZCLADOR_NATIVO_PROTOCOLO.md','evidence/voice_mixer_on_vectors01.json')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);args=parser.parse_args()
    if not 1<=args.attempt<=99:raise ValueError('attempt 1..99 required')
    output=ROOT/f'evidence/voice_mixer_on_native_attempt{args.attempt:02d}.json'
    target=ROOT/f'tmp/mixer-on-native-build{args.attempt:02d}'
    if output.exists() or target.exists():raise ValueError('preserve native attempt and compiler outputs')
    before={n:sha(ROOT/n) for n in SOURCES}
    toolchain={}
    for name in ('rustc','cargo'):
        path=Path(subprocess.check_output(['rustup','which',name],cwd=ROOT,text=True).strip())
        version=subprocess.check_output([str(path),'--version'],cwd=ROOT,text=True).strip()
        toolchain[name]=dict(path=path.as_posix(),sha256=sha(path),version=version)
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    free=shutil.disk_usage(ROOT).free;estimated=256*1024**2;margin=2*1024**3
    command=[toolchain['cargo']['path'],'test','--offline','--locked','-p','rf-d-circuit',
        '--test','mixer_on','--test','mixer_on_no_alloc','--target-dir',str(target),
        '--','--nocapture','--test-threads=1']
    report=dict(schema='rf-d/mixer-on-native-attempt/v1',attempt=args.attempt,passed=False,command=command,
        cwd=ROOT.as_posix(),source_sha256=before,toolchain=toolchain,
        estimated_build_bytes=estimated,margin_bytes=margin,required_free_bytes=estimated+margin,
        available_free_bytes=free,resource_passed=free>=estimated+margin,estimates_are_not_bounds=True,
        wall_limit_s=900,process_started=False,new_spice_solves=0,new_audio=False)
    def write():output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    write()
    if not report['resource_passed']:print('native mixer compilation resource rejected',flush=True);return
    start=time.perf_counter()
    try:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
        report['process_started']=True
        try:stdout,stderr=process.communicate(timeout=900)
        except subprocess.TimeoutExpired:process.kill();stdout,stderr=process.communicate();report['timeout']=True
        report.update(stdout=stdout,stderr=stderr,exit_code=process.returncode)
    except OSError as exc:report['launch_error']=str(exc)
    report['wall_s']=time.perf_counter()-start
    report['source_sha256_after']={n:sha(ROOT/n) for n in SOURCES}
    report['toolchain_sha256_after']={n:sha(Path(t['path'])) for n,t in toolchain.items()}
    report['passed']=(report.get('exit_code')==0 and not report.get('timeout') and before==report['source_sha256_after']
        and all(t['sha256']==report['toolchain_sha256_after'][n] for n,t in toolchain.items()))
    if not report['passed']:
        report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf-8') for n in SOURCES if n.endswith(('.rs','.py'))}
    write();print(report.get('stdout','')+report.get('stderr',''),flush=True)
    print('native mixer attempt:',report['passed'],'wall:',round(report['wall_s'],2),flush=True)

if __name__=='__main__':main()
