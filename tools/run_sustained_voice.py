"""Bounded held/released ON campaign using the frozen public library."""
import argparse,base64,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_sustained_voice import EXAMPLE
from joint_cycles_analysis import require

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt
    work=ROOT/f'references-local/sustained-voice{attempt:02d}';out=f'evidence/voice_sustained_native{attempt:02d}.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive campaign')
    previous='evidence/voice_conditioned_recipe_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));require(old['passed'],'admitted history/library')
    inp='evidence/voice_sustained_inputs01.json';q=json.loads((ROOT/inp).read_text(encoding='utf8'));require(q['passed'],'inputs')
    for n,h in q['source_sha256'].items():require(sha(ROOT/n)==h,'declared input '+n)
    names=[EXAMPLE,'tools/run_sustained_voice.py','tools/prepare_sustained_voice.py','tools/sustained_voice_body.rs','docs/VOZ_SOSTENIDA_PROTOCOLO.md',inp,previous]
    sources={n:sha(ROOT/n) for n in names};private=dict(q['private_used_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h==old['private_input_sha256'][n],'frozen private '+n)
    compiler=json.loads((ROOT/'evidence/voice_conditioned_recipe_library02.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler')
    free=shutil.disk_usage(ROOT).free;require(free>=1024**3+96*1024**2,'reserve and output budget')
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];work.mkdir();exe=work/'sustained.exe'
    commands=[];profiles=[];replays=[];start=time.perf_counter();r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler,new_library_compile=False,new_cargo_cache=False,lab_stack_bytes=33554432,available_free_bytes=free,reserve_bytes=1024**3,output_budget_bytes=96*1024**2)
    def run(cmd,limit):
        t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW)
        return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
    try:
        lib=next(iter(private));cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',EXAMPLE,'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)]
        c=run(cmd,120);commands.append(c)
        if c['exit_code']:replays.append(run(cmd,120));require(False,'native compile rejection')
        for maximum,arg in [(1048576,'2'),(524288,'1')]:
            cmd=[str(exe),arg,str(work/str(maximum))];p=run(cmd,1590);profiles.append(dict(final_decay=True,maximum_half_ticks=maximum,**p));print('SUSTAINED_PROFILE',maximum,p['exit_code'],p['stderr'][-240:],flush=True)
            if p['exit_code']:replays.append(run(cmd[:-1]+[str(work/('rejected-replay-'+str(maximum)))],1590));require(False,'native profile rejection')
        require(time.perf_counter()-start<=3300,'campaign wall budget');r['passed']=True
    except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    r.update(commands=commands,profiles=profiles,replays=replays,wall_s=time.perf_counter()-start,
        source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},minimum_free_bytes=shutil.disk_usage(ROOT).free,
        outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()])
    require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable campaign inputs');write(out,r);print('SUSTAINED_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'native campaign')
if __name__=='__main__':main()
