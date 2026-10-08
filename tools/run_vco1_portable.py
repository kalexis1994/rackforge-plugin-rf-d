"""Serial pinned native API tests with immutable attempt receipts."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha

SOURCES=['Cargo.toml','Cargo.lock','crates/rf-d-circuit/Cargo.toml',
 'crates/rf-d-circuit/src/lib.rs','crates/rf-d-circuit/src/vco1_radau_fine.rs',
 'crates/rf-d-circuit/src/vco1_radau.rs','crates/rf-d-circuit/src/vco1_engine.rs',
 'crates/rf-d-circuit/tests/vco1_engine.rs','evidence/voice_vco1_portable_vectors01.json',
 'docs/VCO1_PORTABLE_PROTOCOLO.md','tools/run_vco1_portable.py']
def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',type=int,required=True);args=p.parse_args()
    output=ROOT/f'evidence/voice_vco1_portable_native{args.attempt:02d}.json'
    target=ROOT/f'tmp/vco1-portable-build{args.attempt:02d}'
    assert not output.exists() and not target.exists(),'preserve attempt'
    compiler=json.loads((ROOT/'evidence/voice_vco1_radau_cycles04.json').read_text())['compiler']
    rustc=Path(compiler['path']);cargo=rustc.with_name('cargo.exe')
    assert sha(rustc)==compiler['sha256']
    env=os.environ.copy();env['RUSTC']=str(rustc);env['RUST_MIN_STACK']='8388608'
    env['RUSTFLAGS']='-C opt-level=2 -C link-arg=-Wl,--stack,8388608'
    env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    cmd=[str(cargo),'test','--offline','--locked','-p','rf-d-circuit','--test','vco1_engine',
         '--target-dir',str(target),'--','--nocapture','--test-threads=1']
    before={n:sha(ROOT/n) for n in SOURCES};free=shutil.disk_usage(ROOT).free
    report=dict(schema='rf-d/portable-native/v1',passed=False,compiler=compiler,
        cargo_sha256=sha(cargo),source_sha256=before,command=cmd,
        cwd=ROOT.as_posix(),env={n:env[n] for n in ['RUSTC','RUST_MIN_STACK','RUSTFLAGS']},
        available_free_bytes=free,reserve_bytes=1024**3,estimated_build_bytes=128*1024**2,
        process_budget_s=900,commands=[],replays=[],new_independent_solves=0,new_full_campaigns=0,
        test_thread_stack_bytes=8388608,main_stack_reserve_bytes=8388608)
    def write():output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write()
    if free<1024**3+128*1024**2:raise RuntimeError('disk preflight rejected')
    def run():
        start=time.perf_counter()
        try:
            r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
            return dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start)
        except subprocess.TimeoutExpired as e:
            return dict(exit_code=None,stdout=str(e.stdout),stderr=str(e.stderr),timeout=True,wall_s=time.perf_counter()-start)
    report['commands'].append(run());write()
    report['source_sha256_after']={n:sha(ROOT/n) for n in SOURCES}
    report['compiler_sha256_after']=sha(rustc)
    report['passed']=report['commands'][0]['exit_code']==0 and before==report['source_sha256_after'] and report['compiler_sha256_after']==compiler['sha256']
    if not report['passed']:
        report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in SOURCES if n.endswith(('.rs','.py','.md'))}
        report['replays'].append(run())
    report['target_build_bytes']=sum(p.stat().st_size for p in target.rglob('*') if p.is_file())
    write()
    print(report['commands'][0]['stdout']+report['commands'][0]['stderr'],flush=True)
    print('PORTABLE_ATTEMPT',args.attempt,report['passed'],flush=True)
if __name__=='__main__': main()
