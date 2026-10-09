"""Bounded serial continuation of both admitted conditioned checkpoints."""
import argparse,json,os,re,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,checkpoint
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args();out=ROOT/f'evidence/voice_joint_conditioned_cycles_native{a.attempt:02d}.json';work=ROOT/f'references-local/joint-conditioned-cycles{a.attempt:02d}'
    require(not out.exists() and not work.exists(),'new attempt')
    parent_name='evidence/voice_joint_prefix_native01.json';parent=json.loads((ROOT/parent_name).read_text());require(parent['passed'],'completed parent')
    for p in parent['outputs']:require(sha(ROOT/p['path'])==p['sha256'],'protected prefix '+p['path'])
    library=parent['cached_library'];compiler=parent['compiler'];require(sha(ROOT/library['path'])==library['sha256'] and sha(Path(compiler['path']))==compiler['sha256'],'compiled identity')
    used={library['path']:library['sha256']};remaining={}
    for maximum,limit,completed in [(65536,32000,2009),(32768,48000,4006)]:
        n=f'references-local/joint-prefix01/{maximum}/final.ckp';cp=checkpoint((ROOT/n).read_bytes());require(cp['ticks']==262144000 and cp['maximum']==maximum,'checkpoint scope');used[n]=sha(ROOT/n);remaining[maximum]=limit-completed
    names=[parent_name,'tools/run_joint_conditioned_cycles.py','tools/prepare_joint_conditioned_cycles.py','tools/joint_conditioned_cycles_runner.rs','tools/joint_cycles_resume_runner.rs','tools/joint_cycles_analysis.py','docs/VOZ_CICLOS_CONDICIONADOS_PROTOCOLO.md','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt']
    hashes={n:sha(ROOT/n) for n in names};r=dict(schema='rf-d/joint-conditioned-cycles-native/v1',passed=False,source_sha256=hashes,private_used_sha256=used,compiler=compiler,cached_library=library,commands=[],profiles=[],replays=[],outputs=[],available_free_bytes=shutil.disk_usage(ROOT).free,reserve_bytes=1073741824,estimated_output_bytes=41943040,profile_budget_s=1800,global_budget_s=3600,remaining_interval_budgets=remaining,goal_ticks=2752512000,lab_stack_bytes=33554432,new_audio=False,new_spice_processes=0,new_library_compile=False)
    def write():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
    start=time.perf_counter();write();env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432'
    try:
        require(r['available_free_bytes']>=r['reserve_bytes']+r['estimated_output_bytes'],'disk preflight');work.mkdir();exe=work/'run.exe'
        cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_conditioned_cycles_runner.rs','--extern','rf_d_circuit='+str(ROOT/library['path']),'-o',str(exe)]
        t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);r['commands'].append(dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr));write()
        if p.returncode:
            replay=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);r['replays'].append(dict(command=cmd,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr));require(False,'caller compile')
        for maximum in [65536,32768]:
            directory=work/str(maximum);directory.mkdir();cmd=[str(exe),'run',str(maximum),str(directory),str(remaining[maximum]),str(ROOT/f'references-local/joint-prefix01/{maximum}/final.ckp')];t=time.perf_counter();minimum=shutil.disk_usage(ROOT).free;stop_at=None;reason=None
            with (directory/'stdout.txt').open('wb') as stdout,(directory/'stderr.txt').open('wb') as stderr:
                process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                while process.poll() is None:
                    now=time.perf_counter();space=shutil.disk_usage(ROOT).free;minimum=min(minimum,space)
                    if stop_at is None and (space<r['reserve_bytes'] or now-t>1800 or now-start>3600):
                        reason='disk reserve' if space<r['reserve_bytes'] else 'CPU budget';stop_at=now;(work/'stop.flag').write_text(reason+'\n',encoding='utf8')
                    if stop_at is not None and now-stop_at>20:process.terminate()
                    time.sleep(.25)
            text=(directory/'stderr.txt').read_text(encoding='utf8');r['profiles'].append(dict(maximum_half_ticks=maximum,interval_budget=remaining[maximum],command=cmd,exit_code=process.returncode,wall_s=time.perf_counter()-t,minimum_free_bytes=minimum,administrative_stop=stop_at is not None,stop_reason=reason,stdout=(directory/'stdout.txt').read_text(encoding='utf8'),stderr=text));write();print('CONDITIONED_PROFILE',maximum,process.returncode,r['profiles'][-1]['wall_s'],text[-1500:],flush=True)
            if process.returncode:
                match=re.search(r'FAILURE,target_ticks=(\d+),reason=ENGINE_REJECT',text)
                if match:
                    cmd=[str(exe),'replay',str(directory/'final.ckp'),match[1]];p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);r['replays'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
                else:r['replay_pending']='Administrative/observation failure; inspect preserved checkpoint before an electrical replay.'
                require(False,'continuation incomplete')
        require(time.perf_counter()-start<=3600 and all(not p['administrative_stop'] and p['minimum_free_bytes']>=r['reserve_bytes'] for p in r['profiles']),'resource gates');r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
    r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()] if work.exists() else []
    r['wall_s']=time.perf_counter()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in used};require(r['source_sha256_after']==hashes and r['private_used_sha256_after']==used,'unchanged inputs');write();print('CONDITIONED_CYCLES_NATIVE',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
