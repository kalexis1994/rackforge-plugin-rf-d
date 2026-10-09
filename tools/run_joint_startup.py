"""Bounded native joint conditioned initialization and release, fixed compiler."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_startup_native{a.attempt:02d}.json';work=ROOT/f'references-local/joint-startup{a.attempt:02d}';assert not out.exists() and not work.exists()
    compiler=json.loads((ROOT/'evidence/voice_joint_cycles_native01.json').read_text())['compiler'];assert sha(Path(compiler['path']))==compiler['sha256']
    sources=['tools/run_joint_startup.py','tools/joint_startup_runner.rs','docs/VOZ_INICIALIZACION_PROTOCOLO.md','crates/rf-d-circuit/src/lib.rs','crates/rf-d-circuit/src/joint_startup.rs','crates/rf-d-circuit/src/joint_voice.rs','crates/rf-d-circuit/src/joint_engine.rs','crates/rf-d-circuit/src/joint_currents.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt']
    before={n:sha(ROOT/n) for n in sources};free=shutil.disk_usage(ROOT).free
    r=dict(schema='rf-d/joint-startup-native/v1',passed=False,source_sha256=before,compiler=compiler,commands=[],replays=[],outputs=[],reserve_bytes=1024**3,estimated_output_bytes=12*1024**2,available_free_bytes=free,process_budget_s=180,global_budget_s=600,lab_stack_bytes=33554432)
    def write():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
    write();assert free>=r['reserve_bytes']+r['estimated_output_bytes'],'resource preflight';work.mkdir()
    lib=work/'librf_d_circuit.rlib';exe=work/'run.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432'
    prefix=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432']
    commands=[prefix+['--crate-type','lib','--crate-name','rf_d_circuit','crates/rf-d-circuit/src/lib.rs','-o',str(lib)],prefix+['-C','strip=symbols','tools/joint_startup_runner.rs','--extern','rf_d_circuit='+str(lib),'-o',str(exe)],[str(exe)]]
    started=time.perf_counter();minimum=free
    for cmd in commands:
        began=time.perf_counter();q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=180)
        minimum=min(minimum,shutil.disk_usage(ROOT).free);r['commands'].append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-began));write()
        if q.returncode:
            r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in sources if n.endswith(('.rs','.py'))}
            replay=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=180);r['replays'].append(dict(command=cmd,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr));break
        if minimum<r['reserve_bytes'] or time.perf_counter()-started>600:r['administrative_failure']='reserve or elapsed budget';break
    r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()]
    r['minimum_free_bytes']=minimum;r['wall_s']=time.perf_counter()-started;r['source_sha256_after']={n:sha(ROOT/n) for n in sources}
    r['passed']=len(r['commands'])==3 and all(c['exit_code']==0 for c in r['commands']) and not r['replays'] and not r.get('administrative_failure') and before==r['source_sha256_after']
    write();print('STARTUP_NATIVE',r['passed'],r['wall_s'],r['commands'][-1]['stderr'],flush=True)
if __name__=='__main__':main()
