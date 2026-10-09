"""Bounded serial first-cycle campaign, compact lossless files and local replay."""
import argparse,json,os,re,shutil,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_cycles_native{a.attempt:02d}.json';work=ROOT/f'references-local/joint-cycles{a.attempt:02d}'
    assert not out.exists() and not work.exists()
    compiler=json.loads((ROOT/'evidence/voice_joint_engine_native01.json').read_text())['compiler'];assert sha(Path(compiler['path']))==compiler['sha256']
    sources=['tools/run_joint_cycles.py','tools/joint_cycles_runner.rs','tools/prepare_joint_cycles.py','docs/VOZ_PRIMER_CICLO_PROTOCOLO.md','crates/rf-d-circuit/src/lib.rs','crates/rf-d-circuit/src/joint_currents.rs','crates/rf-d-circuit/src/joint_engine.rs','crates/rf-d-circuit/src/joint_voice.rs','crates/rf-d-circuit/src/joint_vco_fine.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt']
    hashes={n:sha(ROOT/n) for n in sources};free=shutil.disk_usage(ROOT).free
    report=dict(schema='rf-d/joint-cycles-native/v1',passed=False,compiler=compiler,source_sha256=hashes,commands=[],replays=[],profiles=[],outputs=[],available_free_bytes=free,reserve_bytes=1024**3,estimated_output_bytes=48*1024**2,process_budget_s=900,global_budget_s=1800,lab_stack_bytes=33554432)
    def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write();assert free>=report['reserve_bytes']+report['estimated_output_bytes'],'disk preflight'
    work.mkdir();lib=work/'librf_d_circuit.rlib';exe=work/'run.exe'
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432'
    prefix=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432'];started=time.perf_counter()
    build=[prefix+['--crate-type','lib','--crate-name','rf_d_circuit','crates/rf-d-circuit/src/lib.rs','-o',str(lib)],prefix+['tools/joint_cycles_runner.rs','--extern','rf_d_circuit='+str(lib),'-o',str(exe)]]
    failed=False
    for cmd in build:
        r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
        report['commands'].append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));write()
        if r.returncode:
            report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in sources if n.endswith(('.rs','.py'))}
            rr=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
            report['replays'].append(dict(command=cmd,exit_code=rr.returncode,stdout=rr.stdout,stderr=rr.stderr));failed=True;break
    if not failed:
        for maximum,limit in [(65536,32000),(32768,48000)]:
            directory=work/str(maximum);directory.mkdir();cmd=[str(exe),'run',str(maximum),str(directory),str(limit)]
            stderr_path=directory/'stderr.txt';stdout_path=directory/'stdout.txt';start=time.perf_counter();minimum_free=shutil.disk_usage(ROOT).free;administrative=False
            with stdout_path.open('wb') as stdout,stderr_path.open('wb') as stderr:
                process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                while process.poll() is None:
                    space=shutil.disk_usage(ROOT).free;minimum_free=min(minimum_free,space)
                    if space<report['reserve_bytes'] or time.perf_counter()-started>1800 or time.perf_counter()-start>910:
                        (work/'stop.flag').write_text('resource stop\n');administrative=True
                    if time.perf_counter()-start>930:process.terminate();administrative=True
                    time.sleep(.25)
            text=stderr_path.read_text(encoding='utf8');record=dict(maximum_half_ticks=maximum,interval_budget=limit,command=cmd,exit_code=process.returncode,wall_s=time.perf_counter()-start,stderr=text,stdout=stdout_path.read_text(encoding='utf8'),minimum_free_bytes=minimum_free,administrative_stop=administrative)
            report['profiles'].append(record);write();print('PROFILE',maximum,process.returncode,record['wall_s'],text[-1200:],flush=True)
            if process.returncode:
                report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in sources if n.endswith(('.rs','.py'))}
                match=re.search(r'FAILURE,target_ticks=(\d+),reason=ENGINE_REJECT',text)
                if match:
                    replay=[str(exe),'replay',str(directory/'final.ckp'),match[1]]
                    rr=subprocess.run(replay,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
                    report['replays'].append(dict(command=replay,exit_code=rr.returncode,stdout=rr.stdout,stderr=rr.stderr))
                else:report['replay_pending']='Administrative or observation/final gate; inspect existing files before any physics replay.'
                failed=True;break
    report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()]
    report['source_sha256_after']={n:sha(ROOT/n) for n in sources};report['wall_s']=time.perf_counter()-started
    report['passed']=not failed and len(report['profiles'])==2 and all(p['exit_code']==0 and not p['administrative_stop'] and p['minimum_free_bytes']>=report['reserve_bytes'] for p in report['profiles']) and report['wall_s']<=1800 and hashes==report['source_sha256_after']
    write();print('CYCLES_NATIVE',a.attempt,report['passed'],flush=True)
if __name__=='__main__':main()
