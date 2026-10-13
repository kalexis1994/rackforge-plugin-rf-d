"""Compile the additive public library without a Cargo cache or new dependencies."""
import base64,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    work=ROOT/'references-local/conditioned-recipe-library01';require(not work.exists(),'exclusive library build');require(shutil.disk_usage(ROOT).free>=1024**3+96*1024**2,'reserve');work.mkdir()
    names=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'crates/rf-d-circuit/src').glob('*.rs'))+['tools/build_conditioned_recipe.py','tools/prepare_conditioned_recipe.py','docs/RECETA_CONDICIONADA_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names}
    compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];lib=work/'librf_d_circuit.rlib';cmd=[compiler['path'],'--edition=2021','--crate-name','rf_d_circuit','--crate-type','rlib','-C','opt-level=2','-C','strip=symbols','crates/rf-d-circuit/src/lib.rs','-o',str(lib)];commands=[];r=dict(passed=False,source_sha256=before,compiler=compiler,new_library_compile=True,new_cargo_cache=False)
    def run():
        t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);q=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t);commands.append(q);return q
    try:
        q=run()
        if q['exit_code']:run();require(False,'public library compile rejection')
        r['passed']=True
    except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()]);require(before==r['source_sha256_after'],'stable library inputs');write('evidence/voice_conditioned_recipe_library01.json',r);print('CONDITIONED_RECIPE_LIBRARY',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
