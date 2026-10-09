"""Reuse measured physics and continue the fine prefix once, with bounded IO."""
import argparse,json,os,re,shutil,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import checkpoint,trace
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_cycles_resume{a.attempt:02d}.json';work=ROOT/f'references-local/joint-cycles-resume{a.attempt:02d}';assert not out.exists() and not work.exists()
    parent=json.loads((ROOT/'evidence/voice_joint_cycles_native01.json').read_text());extension=json.loads((ROOT/'evidence/voice_joint_cycles_extension01.json').read_text());assert not parent['passed'] and parent['profiles'][0]['exit_code']==0
    for item in parent['outputs']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    prefix=ROOT/'references-local/joint-cycles01/32768';old=checkpoint((prefix/'final.ckp').read_bytes());rows=trace(prefix/'trace.bin');completed=len(rows)//2;remaining=48000-completed;assert completed==7875 and int(rows[-1]['ticks'])==old['ticks']
    compiler=parent['compiler'];assert sha(Path(compiler['path']))==compiler['sha256'];lib=ROOT/extension['cached_library'];assert sha(lib)==extension['cached_library_sha256']
    sources=['tools/run_joint_cycles_resume.py','tools/prepare_joint_cycles_resume.py','tools/joint_cycles_resume_runner.rs','tools/joint_cycles_analysis.py','docs/VOZ_PRIMER_CICLO_EXTENSION.md','evidence/voice_joint_cycles_native01.json','evidence/voice_joint_cycles_extension01.json',extension['cached_library'],'references-local/joint-cycles01/32768/final.ckp']
    hashes={n:sha(ROOT/n) for n in sources};free=shutil.disk_usage(ROOT).free
    report=dict(schema='rf-d/joint-cycles-continuation/v1',passed=False,source_sha256=hashes,compiler=compiler,commands=[],replays=[],profiles=[],outputs=[],available_free_bytes=free,reserve_bytes=1024**3,estimated_output_bytes=28*1024**2,process_budget_s=1800,global_budget_s=2100,lab_stack_bytes=33554432,preserved_prefix_ticks=old['ticks'],preserved_prefix_intervals=completed,remaining_interval_budget=remaining)
    def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write();assert free>=report['reserve_bytes']+report['estimated_output_bytes'],'disk preflight'
    work.mkdir();exe=work/'resume.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';start=time.perf_counter()
    cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_cycles_resume_runner.rs','--extern','rf_d_circuit='+str(lib),'-o',str(exe)]
    r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);report['commands'].append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));write()
    if r.returncode:
        report['failed_source_text']={n:(ROOT/n).read_text() for n in sources if n.endswith(('.rs','.py'))};rr=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);report['replays'].append(dict(command=cmd,exit_code=rr.returncode,stdout=rr.stdout,stderr=rr.stderr))
    else:
        directory=work/'32768';directory.mkdir();command=[str(exe),'run','32768',str(directory),str(remaining),str(prefix/'final.ckp')];stderr_path=directory/'stderr.txt';stdout_path=directory/'stdout.txt';minimum_free=shutil.disk_usage(ROOT).free;administrative=False;began=time.perf_counter()
        with stdout_path.open('wb') as stdout,stderr_path.open('wb') as stderr:
            p=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            while p.poll() is None:
                space=shutil.disk_usage(ROOT).free;minimum_free=min(minimum_free,space)
                if space<report['reserve_bytes'] or time.perf_counter()-start>2100 or time.perf_counter()-began>1810:(work/'stop.flag').write_text('resource stop\n');administrative=True
                if time.perf_counter()-began>1830:p.terminate();administrative=True
                time.sleep(.25)
        text=stderr_path.read_text();record=dict(maximum_half_ticks=32768,interval_budget=remaining,command=command,exit_code=p.returncode,wall_s=time.perf_counter()-began,stderr=text,stdout=stdout_path.read_text(),minimum_free_bytes=minimum_free,administrative_stop=administrative);report['profiles'].append(record);write();print(text[-1600:],flush=True)
        if p.returncode:
            report['failed_source_text']={n:(ROOT/n).read_text() for n in sources if n.endswith(('.rs','.py'))};match=re.search(r'FAILURE,target_ticks=(\d+),reason=ENGINE_REJECT',text)
            if match:
                replay=[str(exe),'replay',str(directory/'final.ckp'),match[1]];rr=subprocess.run(replay,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120);report['replays'].append(dict(command=replay,exit_code=rr.returncode,stdout=rr.stdout,stderr=rr.stderr))
            else:report['replay_pending']='inspect preserved administrative or observation failure'
    report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()];report['source_sha256_after']={n:sha(ROOT/n) for n in sources};report['wall_s']=time.perf_counter()-start
    report['passed']=r.returncode==0 and len(report['profiles'])==1 and report['profiles'][0]['exit_code']==0 and not report['profiles'][0]['administrative_stop'] and report['profiles'][0]['minimum_free_bytes']>=report['reserve_bytes'] and report['wall_s']<=2100 and hashes==report['source_sha256_after']
    write();print('CYCLES_CONTINUATION',report['passed'],flush=True)
if __name__=='__main__':main()
