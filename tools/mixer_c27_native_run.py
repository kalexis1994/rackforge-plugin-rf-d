"""Small direct-rustc campaign; preserve every source, executable and failure."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from mixer_c27_vectors import ROOT,sha,INPUTS

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',required=True,type=int);args=parser.parse_args()
    if not 1<=args.attempt<=99:raise ValueError('attempt 1..99')
    output=ROOT/f'evidence/voice_mixer_c27_native_attempt{args.attempt:02d}.json'
    work=ROOT/f'references-local/mixer-c27-native{args.attempt:02d}'
    if output.exists() or work.exists():raise ValueError('preserve C27 native campaign')
    names=sorted(set(INPUTS)|{'.gitattributes','tools/mixer_c27_native_run.py',
        'evidence/voice_mixer_c27_vectors01.txt','evidence/voice_mixer_c27_vectors01.json',
        'crates/rf-d-circuit/tests/mixer_c27.rs','crates/rf-d-circuit/tests/mixer_c27_no_alloc.rs'}|
        {p.relative_to(ROOT).as_posix() for p in (ROOT/'crates/rf-d-circuit/src').glob('*.rs')})
    sources={n:sha(ROOT/n) for n in names}
    rustc=Path(subprocess.check_output(['rustup','which','rustc'],text=True,cwd=ROOT).strip())
    toolchain=dict(path=rustc.as_posix(),sha256=sha(rustc),version=subprocess.check_output([str(rustc),'--version'],text=True).strip())
    free=shutil.disk_usage(ROOT).free;estimate=64*1024**2;margin=2*1024**3
    report=dict(schema='rf-d/mixer-c27-native-attempt/v1',attempt=args.attempt,passed=False,source_sha256=sources,
        toolchain=toolchain,estimated_build_bytes=estimate,margin_bytes=margin,available_free_bytes=free,
        resource_passed=free>=estimate+margin,commands=[],new_spice_solves=0,new_audio=False,
        full_ladder_integrated=False,physical_fidelity=False,real_time=False)
    def write():output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write()
    if not report['resource_passed']:print('C27 compilation resource rejected',flush=True);return
    work.mkdir();env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    targets=[('library','crates/rf-d-circuit/src/lib.rs','rf_d_circuit.rlib',False),
             ('ports','crates/rf-d-circuit/tests/mixer_c27.rs','ports.exe',True),
             ('heap','crates/rf-d-circuit/tests/mixer_c27_no_alloc.rs','heap.exe',True)]
    start=time.perf_counter();outputs=[]
    try:
        for label,source,destination,test in targets:
            target=work/destination
            command=[str(rustc),'--edition=2021',*(['--test'] if test else ['--crate-type','lib']),
                '--crate-name',f'rf_d_c27_{label}',source,'-o',str(target)]
            p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
            report['commands'].append(dict(kind='compile',command=command,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
            if p.returncode:raise RuntimeError('C27 rustc rejected '+label)
            outputs.append(dict(path=target.relative_to(ROOT).as_posix(),sha256=sha(target),bytes=target.stat().st_size))
            if test:
                command=[str(target),'--nocapture','--test-threads=1']
                p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
                report['commands'].append(dict(kind='test',command=command,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
                print(p.stdout+p.stderr,flush=True)
                if p.returncode:raise RuntimeError('C27 native test rejected '+label)
        report['passed']=True
    except (OSError,subprocess.TimeoutExpired,RuntimeError) as exc:
        report['error']=str(exc)
        report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py','.md'))}
    report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in names},
        toolchain_sha256_after=sha(rustc),outputs=outputs)
    report['passed']=report['passed'] and sources==report['source_sha256_after'] and toolchain['sha256']==report['toolchain_sha256_after']
    write();print('C27 native attempt',args.attempt,'passed',report['passed'],'wall',round(report['wall_s'],2),flush=True)

if __name__=='__main__':main()
