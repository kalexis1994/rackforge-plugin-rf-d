"""Exercise the joined public CLI, its artifact guard and a mismatched seam."""
import base64,json,subprocess,sys,time,traceback
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    names=['tools/check_release_cli.py','tools/release_render_cli.py','tools/render_release_voice.py','tools/render_sustained_voice.py','tools/render_conditioned_recipe.py','evidence/voice_release_listening01.json']
    before={n:sha(ROOT/n) for n in names};listening=json.loads((ROOT/names[-1]).read_text(encoding='utf8'));require(listening['passed'],'listening before CLI')
    parent='references-local/sustained-voice01/524288/selected.txt';continuation='references-local/release-voice01/524288/selected.txt';expected=next(f['path'] for f in listening['files'] if f['maximum_half_ticks']==524288)
    private={n:sha(ROOT/n) for n in [parent,continuation,expected]};work=ROOT/'references-local/release-cli01';require(not work.exists(),'exclusive CLI integration');work.mkdir();commands=[];r=dict(passed=False,source_sha256=before,private_used_sha256=private)
    def run(cmd):
        t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);c=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t);commands.append(c);return c
    try:
        cmd=[sys.executable,'-B','tools/release_render_cli.py','--parent',parent,'--continuation',continuation,'--output',str(work/'j7.wav')];q=run(cmd);require(q['exit_code']==0 and sha(work/'j7.wav')==private[expected],'entire CLI WAV identity')
        meta=json.loads((work/'j7.json').read_text(encoding='utf8'));input_hashes={str((ROOT/n).resolve()):private[n] for n in [parent,continuation]}
        require(meta['frames']==960 and meta['input_sha256']==input_hashes and meta['wav_sha256']==private[expected] and not meta['repeated'],'joined CLI metadata')
        saved={n:sha(work/n) for n in ['j7.wav','j7.json']};q=run(cmd);require(q['exit_code']!=0 and 'preserve existing WAV and sidecar' in q['stderr'] and saved=={n:sha(work/n) for n in saved},'existing artifacts unchanged')
        # Preserve both original traces. Alter one inherited HIGH J7 coordinate
        # only in a separate fixture; rejection must precede audio publication.
        lines=(ROOT/continuation).read_text(encoding='utf8').splitlines();fields=lines[1].split(',');require(fields[0]=='JOINT_STATE' and len(fields)==459,'fixture state layout');fields[195]=format(float(fields[195])+1e-3,'.17e');lines[1]=','.join(fields)
        fixture=work/'mismatched-seam.txt';fixture.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
        negative=[sys.executable,'-B','tools/release_render_cli.py','--parent',parent,'--continuation',str(fixture),'--output',str(work/'rejected.wav')];q=run(negative)
        require(q['exit_code']!=0 and 'full inherited state at audio seam' in q['stderr'] and not (work/'rejected.wav').exists() and not (work/'rejected.json').exists(),'mismatched seam rejected before publication')
        r.update(passed=True,user_cli_wav_identical=True,sidecar_verified=True,existing_output_rejected_without_mutation=True,mismatched_seam_rejected_before_publication=True,new_unit_test_definitions=0,integration_checks=3)
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
        try:run([sys.executable,'-B','tools/release_render_cli.py','--parent',parent,'--continuation',continuation,'--output',str(work/'failure-replay.wav')])
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()])
    require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable CLI inputs');write('evidence/voice_release_cli01.json',r);print('RELEASE_CLI',r['passed'],r.get('failure',''));require(r['passed'],'joined public CLI')
if __name__=='__main__':main()
