"""Bounded drivers linked to the freshly built public library."""
import base64,json,os,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
LIB='references-local/conditioned-portable-library01/librf_d_circuit.rlib'

def experiment(tag,text,args,sources,private,validate,replay=True,timeout=600):
    build=json.loads((ROOT/'evidence/voice_conditioned_portable_library01.json').read_text(encoding='utf8'));require(build['passed'] and sha(ROOT/LIB)==next(q['sha256'] for q in build['outputs'] if q['path']==LIB),'public library identity')
    work=ROOT/('references-local/conditioned-portable-'+tag);require(not work.exists(),'exclusive experiment');work.mkdir();p=work/'main.rs';p.write_text(text,encoding='utf8',newline='\n');exe=work/'run.exe'
    sources=sorted(set(sources)|{'tools/conditioned_portable_native.py','evidence/voice_conditioned_portable_library01.json'});private=sorted(set(private)|{LIB});before={n:sha(ROOT/n) for n in sources};used={n:sha(ROOT/n) for n in private};compiler=build['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];r=dict(passed=False,source_sha256=before,private_used_sha256=used,compiler=compiler)
    def run(cmd,limit):
        t=time.perf_counter();q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);c=dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-t);commands.append(c);return c
    try:
        q=run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(p),'--extern','rf_d_circuit='+str(ROOT/LIB),'-o',str(exe)],120)
        if q['exit_code']:run(q['command'],120);require(False,'driver compile rejection')
        cmd=[str(exe)]+[str(a).replace('WORK',str(work)) for a in args];q=run(cmd,timeout)
        if q['exit_code']:
            for a in list(work.iterdir()):
                if a.suffix in ['.txt','.bin']:(work/('preserved-'+a.name)).write_bytes(a.read_bytes())
            run(cmd,timeout);require(False,'driver rejection')
        if replay:
            saved={a.name:a.read_bytes() for a in work.iterdir() if a.suffix in ['.txt','.bin']};second=run(cmd,timeout);require(second['exit_code']==0 and second['stdout']==q['stdout'] and second['stderr']==q['stderr'] and all((work/n).read_bytes()==b for n,b in saved.items()),'identical driver replay');r['identical_replay']=True
        r.update(validate(work,q));r['passed']=True
    except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in sources}
    r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in sources},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=a.relative_to(ROOT).as_posix(),sha256=sha(a),bytes=a.stat().st_size) for a in sorted(work.iterdir()) if a.is_file()]);require(before==r['source_sha256_after'] and used==r['private_used_sha256_after'],'stable public driver inputs');write('evidence/voice_conditioned_portable_'+tag+'.json',r);print('CONDITIONED_PORTABLE',tag,r['passed'],r.get('failure',''),flush=True)
    return r
