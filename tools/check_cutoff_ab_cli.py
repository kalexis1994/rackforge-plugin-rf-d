"""Check paired WAVs, full provenance, overwrite guard and two specific input rejections."""
import base64,json,subprocess,sys,time,traceback
from prepare_vco1_portable import ROOT,sha,write
from render_cutoff_ab import inputs
from joint_cycles_analysis import require
def main():
 out='evidence/cutoff_ab_cli01.json';work=ROOT/'references-local/cutoff-ab-cli01';require(not work.exists() and not (ROOT/out).exists(),'exclusive CLI campaign');work.mkdir();opened=ROOT/'references-local/cutoff-ab01/524288/selected.txt';closed=ROOT/'references-local/voice-cutoff01/524288/selected.txt';listening=json.loads((ROOT/'evidence/cutoff_ab_listening01.json').read_text(encoding='utf8'));require(listening['passed'],'paired audio before CLI');names=['tools/check_cutoff_ab_cli.py','tools/cutoff_ab_cli.py','tools/render_cutoff_ab.py','evidence/cutoff_ab_listening01.json'];before={n:sha(ROOT/n) for n in names};private={f.relative_to(ROOT).as_posix():sha(f) for f in inputs(opened,closed)};commands=[];r=dict(passed=False,source_sha256=before,private_used_sha256=private)
 def run(cmd):
  start=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);c=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-start);commands.append(c);return c
 base=[sys.executable,'-B','tools/cutoff_ab_cli.py','--open',str(opened),'--closed',str(closed)]
 try:
  cmd=base+['--output',str(work/'pair.json')];q=run(cmd);require(q['exit_code']==0,'paired CLI render');meta=json.loads((work/'pair.json').read_text(encoding='utf8'));require(meta['input_sha256']=={str(f.resolve()):sha(f) for f in inputs(opened,closed)} and meta['start_ticks']==82024857600 and meta['end_ticks']==86219161600 and len(meta['input_sha256'])==7,'all seven inputs and clocks')
  for branch in ['open','closed']:
   expected=ROOT/next(f['path'] for f in listening['files'] if f['branch']==branch and f['maximum_half_ticks']==524288);require(sha(work/f'pair-{branch}.wav')==sha(expected),'entire paired WAV');private[expected.relative_to(ROOT).as_posix()]=sha(expected)
  expected_metrics=next({k:v for k,v in x.items() if k!='maximum_half_ticks'} for x in listening['ab_metrics'] if x['maximum_half_ticks']==524288);require(meta['metrics']==expected_metrics and all(f['frames']==384 for f in meta['files']) and meta['open_alpha']==1. and meta['closed_alpha']==.5 and not meta['peak_normalization'] and not meta['dc_removed'],'full paired sidecar');saved={f.name:sha(f) for f in work.iterdir()};q=run(cmd);require(q['exit_code']!=0 and 'preserve existing WAVs and sidecar' in q['stderr'] and saved=={f.name:sha(f) for f in work.iterdir()},'existing pair unchanged')
  for n in ['incoming-original.ckp','final.ckp']:(work/n).write_bytes(opened.with_name(n).read_bytes())
  with opened.open(encoding='utf8') as f:lines=[f.readline().rstrip('\n'),f.readline().rstrip('\n')]
  fields=lines[1].split(',');fields[195]=format(float(fields[195])+1e-3,'.17e');fixture=work/'mismatched.txt';fixture.write_text(lines[0]+'\n'+','.join(fields)+'\n',encoding='utf8',newline='\n');q=run([*base[:4],str(fixture),*base[5:],'--output',str(work/'rejected.json')]);require(q['exit_code']!=0 and 'same initial A/B state' in q['stderr'] and not any((work/n).exists() for n in ['rejected.json','rejected-open.wav','rejected-closed.wav']),'specific initial-state rejection before publication')
  fixture=work/'incomplete.txt';fixture.write_text('\n'.join(lines)+'\nBOUNDARY,0,82024857600,0.00000000000000000e0,0\n',encoding='utf8',newline='\n');q=run([*base[:4],str(fixture),*base[5:],'--output',str(work/'incomplete.json')]);require(q['exit_code']!=0 and 'complete A/B observations' in q['stderr'] and not any((work/n).exists() for n in ['incomplete.json','incomplete-open.wav','incomplete-closed.wav']),'specific incomplete-window rejection');r.update(passed=True,integration_checks=4,paired_wavs_identical=True,sidecar_verified=True,existing_output_rejected_without_mutation=True,mismatched_state_rejected_before_publication=True,incomplete_trace_rejected_before_publication=True)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
  try:run(base+['--output',str(work/'failure-replay.json')])
  except Exception:r['replay']=traceback.format_exc()
 r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=f.relative_to(ROOT).as_posix(),sha256=sha(f),bytes=f.stat().st_size) for f in sorted(work.iterdir()) if f.is_file()]);require(before==r['source_sha256_after'],'stable CLI code');write(out,r);print('CUTOFF_AB_CLI',r['passed'],r.get('failure',''));require(r['passed'],'paired CLI campaign')
if __name__=='__main__':main()
