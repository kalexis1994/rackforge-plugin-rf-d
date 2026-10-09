"""Compile only the lab caller and run bounded charge conditioning/release."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_charge_seed_native{a.attempt:02d}.json';work=ROOT/f'references-local/joint-charge-seed{a.attempt:02d}'
    assert not out.exists() and not work.exists()
    old=json.loads((ROOT/'evidence/voice_joint_conditioned_cycles_tests01.json').read_text())
    compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text())['compiler'];assert sha(Path(compiler['path']))==compiler['sha256']
    lib='references-local/joint-startup01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib)};assert private[lib]==old['private_input_sha256'][lib]
    names=['tools/run_joint_charge_seed.py','tools/joint_charge_seed_runner.rs','tools/build_joint_charge_seed_caller.py','docs/VOZ_CARGAS_SEMILLA_PROTOCOLO.md','evidence/voice_joint_charge_seed_targets01.txt','evidence/voice_joint_charge_seed_targets01.json','crates/rf-d-circuit/src/joint_voice.rs','crates/rf-d-circuit/src/joint_engine.rs','crates/rf-d-circuit/src/joint_currents.rs','crates/rf-d-circuit/src/chain_charge.rs','crates/rf-d-circuit/src/output_conversion.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt']
    before={n:sha(ROOT/n) for n in names};free=shutil.disk_usage(ROOT).free
    r=dict(schema='rf-d/joint-charge-seed-native/v1',passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,commands=[],replays=[],outputs=[],reserve_bytes=1024**3,estimated_output_bytes=8*1024**2,available_free_bytes=free,process_budget_s=180,global_budget_s=600,lab_stack_bytes=33554432,new_library_compile=False,new_audio=False,new_spice_processes=0)
    def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
    save();assert free>=r['reserve_bytes']+r['estimated_output_bytes'],'resource preflight';work.mkdir()
    exe=work/'run.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432'
    commands=[[compiler['path'],'--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-C','strip=symbols','tools/joint_charge_seed_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],[str(exe)]]
    started=time.perf_counter();minimum=free
    for cmd in commands:
        began=time.perf_counter()
        try:q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=180)
        except subprocess.TimeoutExpired as e:
            r['administrative_failure']='process timeout';r['partial_stdout']=e.stdout.decode('utf8') if isinstance(e.stdout,bytes) else e.stdout;r['partial_stderr']=e.stderr.decode('utf8') if isinstance(e.stderr,bytes) else e.stderr;break
        minimum=min(minimum,shutil.disk_usage(ROOT).free);r['commands'].append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-began));save()
        if q.returncode:
            r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
            replay=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=180);r['replays'].append(dict(command=cmd,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr));break
        if minimum<r['reserve_bytes'] or time.perf_counter()-started>600:r['administrative_failure']='reserve or global elapsed';break
    r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()]
    r['minimum_free_bytes']=minimum;r['wall_s']=time.perf_counter()-started;r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in private}
    r['passed']=len(r['commands'])==2 and all(c['exit_code']==0 for c in r['commands']) and not r['replays'] and not r.get('administrative_failure') and before==r['source_sha256_after'] and private==r['private_used_sha256_after']
    save();print('CHARGE_SEED_NATIVE',r['passed'],r['wall_s'],r['commands'][-1]['stderr'] if r['commands'] else r.get('administrative_failure'),flush=True)
if __name__=='__main__':main()
