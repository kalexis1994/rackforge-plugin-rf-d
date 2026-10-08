"""Bounded native joint solver run; preserve any failure and exact replay."""
import argparse,json,os,shutil,subprocess,time
from prepare_vco1_portable import ROOT,sha
def main():
    a=argparse.ArgumentParser();a.add_argument('--attempt',type=int,required=True);attempt=a.parse_args().attempt
    out=ROOT/f'evidence/voice_joint_native{attempt:02d}.json';work=ROOT/f'references-local/joint-native{attempt:02d}'
    assert not out.exists() and not work.exists()
    compiler=json.loads((ROOT/'evidence/voice_chain_charge_native04.json').read_text())['compiler']
    assert sha(__import__('pathlib').Path(compiler['path']))==compiler['sha256']
    sources=['tools/run_joint_voice.py','tools/prepare_joint_voice.py','docs/VOZ_BUS_CONJUNTO_PROTOCOLO.md','crates/rf-d-circuit/src/lib.rs','crates/rf-d-circuit/src/joint_vco_fine.rs','crates/rf-d-circuit/src/joint_voice.rs','crates/rf-d-circuit/tests/joint_voice.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt']
    before={n:sha(ROOT/n) for n in sources};free=shutil.disk_usage(ROOT).free
    # Previous identical direct-rustc runner produced ~10 MiB; 32 MiB declared.
    report=dict(schema='rf-d/joint-native/v1',passed=False,compiler=compiler,source_sha256=before,commands=[],replays=[],outputs=[],available_free_bytes=free,reserve_bytes=1024**3,estimated_build_bytes=32*1024**2,process_budget_s=900,lab_stack_bytes=33554432)
    def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write();assert free>=report['reserve_bytes']+report['estimated_build_bytes'],'disk preflight'
    work.mkdir();lib=work/'librf_d_circuit.rlib';exe=work/'tests.exe'
    prefix=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432']
    commands=[prefix+['--crate-type','lib','--crate-name','rf_d_circuit','crates/rf-d-circuit/src/lib.rs','-o',str(lib)],prefix+['--test','crates/rf-d-circuit/tests/joint_voice.rs','--extern','rf_d_circuit='+str(lib),'-o',str(exe)],[str(exe),'--nocapture','--test-threads=1']]
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';start=time.perf_counter()
    for cmd in commands:
        r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=max(1,900-(time.perf_counter()-start)))
        report['commands'].append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));write()
        if r.returncode:
            report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in sources if n.endswith(('.rs','.py'))}
            rr=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
            report['replays'].append(dict(command=cmd,exit_code=rr.returncode,stdout=rr.stdout,stderr=rr.stderr));break
    report['source_sha256_after']={n:sha(ROOT/n) for n in sources};report['wall_s']=time.perf_counter()-start
    report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]
    report['passed']=len(report['commands'])==3 and all(c['exit_code']==0 for c in report['commands']) and before==report['source_sha256_after']
    write();print(report['commands'][-1]['stdout'][-2000:]+report['commands'][-1]['stderr']);print('JOINT_NATIVE',attempt,report['passed'])
if __name__=='__main__':main()
