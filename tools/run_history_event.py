"""Bounded frozen-library caller. Preserve partial files and failed replay."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write

def main():
    a=argparse.ArgumentParser();a.add_argument('--attempt',type=int,required=True);args=a.parse_args();k=args.attempt
    out=ROOT/f'evidence/voice_history_event_native{k:02d}.json';work=ROOT/f'references-local/history-event{k:02d}';assert not out.exists() and not work.exists()
    old=json.loads((ROOT/'evidence/voice_history_propagation_tests01.json').read_text());inputs=json.loads((ROOT/'evidence/voice_history_event_inputs01.json').read_text());assert old['passed'] and inputs['passed']
    lib='references-local/joint-startup01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),inputs['path']:sha(ROOT/inputs['path']),**inputs['private_used_sha256']};assert private[lib]==old['private_input_sha256'][lib] and private[inputs['path']]==inputs['sha256']
    compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text())['compiler'];assert sha(Path(compiler['path']))==compiler['sha256']
    names=['tools/run_history_event.py','tools/joint_history_tangent.rs','tools/joint_history_propagation.rs','tools/joint_history_event.rs','tools/joint_history_event_runner.rs','docs/VOZ_EVENTO_HISTORIA_PROTOCOLO.md','evidence/voice_history_event_inputs01.json','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','crates/rf-d-circuit/src/joint_voice.rs','crates/rf-d-circuit/src/joint_vco_fine.rs','crates/rf-d-circuit/src/chain_charge.rs']
    names.append('tools/joint_history_propagation.rs');before={n:sha(ROOT/n) for n in names};free=shutil.disk_usage(ROOT).free
    r=dict(schema='rf-d/history-event-native/v1',passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,commands=[],replays=[],outputs=[],reserve_bytes=512*1024**2,estimated_output_bytes=16*1024**2,available_free_bytes=free,lab_stack_bytes=33554432,new_library_compile=False,new_audio=False,new_spice_processes=0)
    def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
    save();assert free>=r['reserve_bytes']+r['estimated_output_bytes'],'resource preflight';work.mkdir();exe=work/'run.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';start=time.perf_counter();minimum=free
    def run(cmd,label,budget):
        nonlocal minimum
        stdout=work/(label+'.stdout');stderr=work/(label+'.stderr');begin=time.perf_counter();administrative=None
        with stdout.open('xb') as so,stderr.open('xb') as se:
            p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
            while p.poll() is None:
                time.sleep(.25);minimum=min(minimum,shutil.disk_usage(ROOT).free)
                if minimum<r['reserve_bytes'] or time.perf_counter()-begin>budget or time.perf_counter()-start>480:
                    administrative='disk or elapsed budget';(work/'stop.flag').write_text(administrative);break
            if administrative:
                try:p.wait(timeout=20)
                except subprocess.TimeoutExpired:p.kill();p.wait()
        return dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-begin,stdout_path=stdout.relative_to(ROOT).as_posix(),stderr_path=stderr.relative_to(ROOT).as_posix(),administrative_stop=administrative)
    commands=[([compiler['path'],'--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-C','strip=symbols','tools/joint_history_event_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],120),([str(exe),str(ROOT/inputs['path']),str(work/'event.bin')],300)]
    for i,(cmd,budget) in enumerate(commands):
        q=run(cmd,f'command{i}',budget);r['commands'].append(q);save()
        if q['exit_code'] or q['administrative_stop']:
            r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
            if not q['administrative_stop']:
                replay=cmd[:] if i==0 else [*cmd[:-1],str(work/'replay.bin')];r['replays'].append(run(replay,'replay',budget))
            break
    r['minimum_free_bytes']=minimum;r['wall_s']=time.perf_counter()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in private}
    r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()]
    r['passed']=len(r['commands'])==2 and all(q['exit_code']==0 and not q['administrative_stop'] for q in r['commands']) and not r['replays'] and r['wall_s']<=480 and before==r['source_sha256_after'] and private==r['private_used_sha256_after'];save();print('EVENT_NATIVE',r['passed'],r['wall_s'],flush=True)
if __name__=='__main__':main()
