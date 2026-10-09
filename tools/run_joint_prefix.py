"""Two bounded serial conditioned release profiles, with durable failure evidence."""
import argparse,json,os,re,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args();out=ROOT/f'evidence/voice_joint_prefix_native{a.attempt:02d}.json';work=ROOT/f'references-local/joint-prefix{a.attempt:02d}'
    require(not out.exists() and not work.exists(),'new attempt paths')
    names=['tools/run_joint_prefix.py','tools/prepare_joint_prefix.py','tools/joint_conditioned_prefix_runner.rs','tools/joint_cycles_runner.rs','docs/VOZ_PREFIJO_CONDICIONADO_PROTOCOLO.md','evidence/voice_joint_startup_native01.json','crates/rf-d-circuit/src/lib.rs','crates/rf-d-circuit/src/joint_startup.rs','crates/rf-d-circuit/src/joint_engine.rs','crates/rf-d-circuit/src/joint_currents.rs','crates/rf-d-circuit/src/joint_voice.rs','crates/rf-d-circuit/src/joint_vco_fine.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt']
    hashes={n:sha(ROOT/n) for n in names};previous=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text());compiler=previous['compiler'];library=next(p for p in previous['outputs'] if p['path'].endswith('.rlib'))
    require(sha(Path(compiler['path']))==compiler['sha256'] and sha(ROOT/library['path'])==library['sha256'],'cached native identity')
    r=dict(schema='rf-d/joint-prefix-native/v1',passed=False,source_sha256=hashes,compiler=compiler,cached_library=library,commands=[],profiles=[],replays=[],outputs=[],available_free_bytes=shutil.disk_usage(ROOT).free,reserve_bytes=1073741824,estimated_output_bytes=16777216,profile_budget_s=300,global_budget_s=700,interval_budget_per_profile=10000,goal_ticks=262144000,lab_stack_bytes=33554432,new_audio=False,new_spice_processes=0)
    def write():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
    start=time.perf_counter();write();env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432'
    try:
        require(r['available_free_bytes']>=r['reserve_bytes']+r['estimated_output_bytes'],'disk preflight');work.mkdir();exe=work/'run.exe'
        cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_conditioned_prefix_runner.rs','--extern','rf_d_circuit='+str(ROOT/library['path']),'-o',str(exe)]
        t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);r['commands'].append(dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr));write()
        if p.returncode:
            replay=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);r['replays'].append(dict(command=cmd,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr));require(False,'caller compile')
        for maximum in [65536,32768]:
            directory=work/str(maximum);directory.mkdir();cmd=[str(exe),'run',str(maximum),str(directory),'10000'];t=time.perf_counter();minimum=shutil.disk_usage(ROOT).free;stop_at=None;reason=None
            with (directory/'stdout.txt').open('wb') as stdout,(directory/'stderr.txt').open('wb') as stderr:
                process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                while process.poll() is None:
                    now=time.perf_counter();space=shutil.disk_usage(ROOT).free;minimum=min(minimum,space)
                    if stop_at is None and (space<r['reserve_bytes'] or now-t>300 or now-start>700):
                        reason='disk reserve' if space<r['reserve_bytes'] else 'CPU budget';stop_at=now;(work/'stop.flag').write_text(reason+'\n',encoding='utf8')
                    if stop_at is not None and now-stop_at>20:process.terminate()
                    time.sleep(.25)
            text=(directory/'stderr.txt').read_text(encoding='utf8');r['profiles'].append(dict(maximum_half_ticks=maximum,command=cmd,exit_code=process.returncode,wall_s=time.perf_counter()-t,minimum_free_bytes=minimum,administrative_stop=stop_at is not None,stop_reason=reason,stdout=(directory/'stdout.txt').read_text(encoding='utf8'),stderr=text));write();print('PREFIX_PROFILE',maximum,process.returncode,r['profiles'][-1]['wall_s'],text[-1200:],flush=True)
            if process.returncode:
                match=re.search(r'FAILURE,target_ticks=(\d+),reason=ENGINE_REJECT',text)
                if match:
                    cmd=[str(exe),'replay',str(directory/'final.ckp'),match[1]];p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);r['replays'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
                else:r['replay_pending']='Administrative/observation failure; preserve checkpoint before deciding an electrical replay.'
                require(False,'profile did not complete')
        require(time.perf_counter()-start<=700 and all(not p['administrative_stop'] and p['minimum_free_bytes']>=r['reserve_bytes'] for p in r['profiles']),'resource gates');r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
    r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()] if work.exists() else []
    r['wall_s']=time.perf_counter()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(r['source_sha256_after']==hashes,'unchanged campaign sources');write();print('JOINT_PREFIX',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
