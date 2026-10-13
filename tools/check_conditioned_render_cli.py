"""Exercise the user CLI, fixed PCM and rejection of an existing output."""
import base64,json,subprocess,sys,time,traceback
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    names=['tools/check_conditioned_render_cli.py','tools/conditioned_render_cli.py',
        'tools/render_conditioned_recipe.py','tests/test_conditioned_render.py',
        'evidence/voice_conditioned_recipe_listening01.json']
    before={n:sha(ROOT/n) for n in names};listening=json.loads((ROOT/names[-1]).read_text(encoding='utf8'));require(listening['passed'],'listening')
    work=ROOT/'references-local/conditioned-recipe-cli01';require(not work.exists(),'exclusive CLI');work.mkdir()
    source='references-local/conditioned-recipe-render02/1-524288/j7.bin';expected=next(x['path'] for x in listening['files'] if x['stretch']==1 and '-on-' in x['path'])
    private={n:sha(ROOT/n) for n in [source,expected]};commands=[];r=dict(passed=False,source_sha256=before,private_used_sha256=private)
    def run(cmd):
        start=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW)
        c=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-start);commands.append(c);return c
    try:
        q=run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_conditioned_render.py','-v']);require(q['exit_code']==0 and 'Ran 2 tests' in q['stderr'],'adapter tests')
        cmd=[sys.executable,'-B','tools/conditioned_render_cli.py','--trace',source,'--output',str(work/'j7.wav')]
        q=run(cmd);require(q['exit_code']==0 and sha(work/'j7.wav')==private[expected],'public CLI entire WAV identity')
        metadata=json.loads((work/'j7.json').read_text(encoding='utf8'))
        require(metadata['input_trace_sha256']==private[source] and metadata['wav_sha256']==private[expected] and metadata['frames']==144 and metadata['stretch']==1 and not metadata['repeated'],'CLI sidecar')
        preserved={n:sha(work/n) for n in ['j7.wav','j7.json']}
        q=run(cmd);require(q['exit_code']!=0 and 'preserve existing WAV and sidecar' in q['stderr'] and preserved=={n:sha(work/n) for n in preserved},'existing output rejection/immutability')
        r.update(passed=True,native_python_test_count=2,user_cli_wav_identical=True,existing_output_rejected_without_mutation=True)
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()])
    require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable CLI inputs')
    write('evidence/voice_conditioned_recipe_cli01.json',r);print('RECIPE_CLI',r['passed'],r.get('failure',''));require(r['passed'],'CLI')
if __name__=='__main__':main()
