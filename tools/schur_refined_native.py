"""Bounded native experiment receipts, with unchanged-source replay on rejection."""
import base64,json,os,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def experiment(tag,text,args,sources,private,validate=None,replay=False,timeout=600):
    work=ROOT/('references-local/schur-refined-'+tag);require(not work.exists(),'exclusive experiment');work.mkdir();p=work/'main.rs';p.write_text(text,encoding='utf8',newline='\n');exe=work/'run.exe';sources=sorted(set(sources)|{'tools/schur_refined_native.py'});before={n:sha(ROOT/n) for n in sources};used={n:sha(ROOT/n) for n in private};compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];r=dict(passed=False,source_sha256=before,private_used_sha256=used,compiler=compiler);started=time.perf_counter()
    def run(cmd,limit):
        t=time.perf_counter();q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);a=dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-t);commands.append(a);return a
    try:
        q=run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(p),'--extern','rf_d_circuit='+str(ROOT/'references-local/joint-startup01/librf_d_circuit.rlib'),'-o',str(exe)],120)
        if q['exit_code']:run(q['command'],120);require(False,'compile rejection')
        cmd=[str(exe)]+[str(x).replace('WORK',str(work)) for x in args];q=run(cmd,timeout)
        if q['exit_code']:
            for x in list(work.iterdir()):
                if x.suffix in ['.bin','.txt']:(work/('preserved-'+x.name)).write_bytes(x.read_bytes())
            run(cmd,timeout);require(False,'native rejection')
        if replay:
            saved={x.name:x.read_bytes() for x in work.iterdir() if x.suffix in ['.bin','.txt']};second=run(cmd,timeout);require(q['exit_code']==second['exit_code'] and q['stdout']==second['stdout'] and q['stderr']==second['stderr'] and all((work/n).read_bytes()==b for n,b in saved.items()),'identical native replay');r['identical_replay']=True
        if validate:r.update(validate(work,q))
        r['passed']=True
    except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in sources}
    r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in sources},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x),bytes=x.stat().st_size) for x in sorted(work.iterdir()) if x.is_file()],wall_s=time.perf_counter()-started);require(before==r['source_sha256_after'] and used==r['private_used_sha256_after'],'stable experiment');write('evidence/voice_schur_refined_'+tag+'.json',r);print('SCHUR_REFINED',tag,r['passed'],r.get('failure',''),flush=True);return r
