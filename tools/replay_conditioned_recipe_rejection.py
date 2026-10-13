"""Preserve an unchanged native replay before correcting history selection."""
import json,os,struct,subprocess,time,traceback
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from run_conditioned_recipe import compare

def main():
    name='evidence/voice_conditioned_recipe_native01.json';q=json.loads((ROOT/name).read_text(encoding='utf8'))
    require(not q['passed'] and 'full exported bits j7.bin' in q['failure'] and 'full exported bits j7.bin' in q['adapter_replay'],'preserved initial adapter rejection')
    original=ROOT/'references-local/conditioned-recipe-render01/1-524288';directory=ROOT/'references-local/conditioned-recipe-render01/rejected-replay-1-524288'
    require(not directory.exists(),'exclusive unchanged replay')
    names=['tools/replay_conditioned_recipe_rejection.py','tools/run_conditioned_recipe.py',name,
        'crates/rf-d-circuit/src/conditioned_recipe.rs','crates/rf-d-circuit/src/conditioned_recipe_seed.rs']
    before={n:sha(ROOT/n) for n in names};exe=ROOT/'references-local/conditioned-recipe-render01/render.exe';private={exe.relative_to(ROOT).as_posix():sha(exe)}
    cmd=[str(exe),'on','1',str(directory)];env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];start=time.perf_counter()
    p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=990,creationflags=subprocess.CREATE_NO_WINDOW)
    require(p.returncode==0,'unchanged native completion')
    for n in ['j7.bin','steps.bin','grids.bin','events.txt']:require((directory/n).read_bytes()==(original/n).read_bytes(),'unchanged native bytes '+n)
    try:compare(directory,ROOT/'references-local/conditioned-portable-cycle01/1-524288');raise AssertionError('rejection must reproduce')
    except ValueError as e:require(str(e)=='full exported bits j7.bin','same rejected gate');failure=traceback.format_exc()
    require(before=={n:sha(ROOT/n) for n in names},'unchanged rejected sources')
    write('evidence/voice_conditioned_recipe_rejection_replay01.json',dict(passed=True,source_sha256=before,source_sha256_after=before,private_used_sha256=private,private_used_sha256_after=private,
        command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-start,
        identical_native_replay=True,repeated_adapter_failure=failure,numerical_gates_changed=False,
        outputs=[dict(path=a.relative_to(ROOT).as_posix(),sha256=sha(a),bytes=a.stat().st_size) for a in sorted(directory.iterdir())]))
    print('RECIPE_REJECTION_REPLAY',True,flush=True)
if __name__=='__main__':main()
