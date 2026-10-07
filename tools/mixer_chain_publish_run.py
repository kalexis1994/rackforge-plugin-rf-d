"""Verify the public module export using direct production-root builds and tests."""
import json,os,shutil,subprocess,time
from pathlib import Path
from mixer_on_native_vectors import ROOT,sha

def main():
    out=ROOT/'evidence/voice_mixer_chain_production01.json';work=ROOT/'references-local/mixer-chain-production01'
    if out.exists() or work.exists():raise ValueError('preserve production chain run')
    old=json.loads((ROOT/'evidence/voice_mixer_chain_native_attempt01.json').read_text(encoding='utf8'))
    names=sorted(set(old['source_sha256'])|{'.gitattributes','tools/mixer_chain_publish_run.py',
        'crates/rf-d-circuit/tests/mixer_chain_no_alloc.rs','evidence/voice_mixer_chain_native_attempt01.json'})
    before={n:sha(ROOT/n) for n in names};compiler=old['compiler'];rustc=Path(compiler['path'])
    if sha(rustc)!=compiler['sha256']:raise ValueError('chain rustc changed')
    free=shutil.disk_usage(ROOT).free;estimate=64*1024**2;margin=2*1024**3
    report=dict(schema='rf-d/mixer-chain-production/v1',passed=False,source_sha256=before,compiler=compiler,
        available_free_bytes=free,estimated_build_bytes=estimate,margin_bytes=margin,resource_passed=free>=estimate+margin,
        estimates_are_not_bounds=True,commands=[],outputs=[],new_spice_solves=0,new_audio=False)
    def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write()
    if not report['resource_passed']:print('chain production resource rejected',flush=True);return
    work.mkdir();library=work/'librf_d_circuit.rlib';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    commands=[('compile',[str(rustc),'--edition=2021','--crate-type','lib','--crate-name','rf_d_circuit','crates/rf-d-circuit/src/lib.rs','-o',str(library)])]
    for name in ('mixer_chain66','mixer_chain_no_alloc'):
        target=work/(name+'.exe')
        commands.append(('compile',[str(rustc),'--edition=2021','--test','--crate-name',name,f'crates/rf-d-circuit/tests/{name}.rs',
            '--extern','rf_d_circuit='+str(library),'-o',str(target)]))
        commands.append(('test',[str(target),'--nocapture','--test-threads=1']))
    start=time.perf_counter()
    try:
        for kind,command in commands:
            p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
            report['commands'].append(dict(kind=kind,command=command,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
            if kind=='test' or p.returncode:print(p.stdout+p.stderr,flush=True)
            if p.returncode:raise RuntimeError('public chain '+kind+' rejected')
        report['passed']=True
    except (OSError,RuntimeError,subprocess.TimeoutExpired) as exc:
        report['error']=str(exc);report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py','.md'))}
    report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in names},compiler_sha256_after=sha(rustc))
    report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.glob('*') if p.is_file()]
    report['passed']=report['passed'] and before==report['source_sha256_after'] and compiler['sha256']==report['compiler_sha256_after']
    write();print('production chain tests',report['passed'],flush=True)

if __name__=='__main__':main()
