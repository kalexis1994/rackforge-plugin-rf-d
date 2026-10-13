"""Execute two loaded continuations with the already admitted frozen rlib."""
import argparse,base64,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_extended_release import EXAMPLE
from joint_cycles_analysis import require
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt
 work=ROOT/f'references-local/extended-release{attempt:02d}';out=f'evidence/voice_extended_native{attempt:02d}.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive experiment')
 inp=json.loads((ROOT/'evidence/voice_extended_inputs01.json').read_text(encoding='utf8'));qa=json.loads((ROOT/'evidence/voice_block_tests01.json').read_text(encoding='utf8'));require(inp['passed'] and qa['passed'],'admitted inputs')
 names=set(inp['source_sha256'])|{p.relative_to(ROOT).as_posix() for p in (ROOT/'crates/rf-d-circuit/src').rglob('*.rs')}|{'tools/run_extended_release.py','evidence/voice_extended_inputs01.json','evidence/voice_block_tests01.json','evidence/voice_block_library02.json'};sources={n:sha(ROOT/n) for n in sorted(names)}
 for n,h in inp['source_sha256'].items():require(sources[n]==h,'declared source '+n)
 private=inp['private_used_sha256']
 for n,h in private.items():require(sha(ROOT/n)==h and qa['private_input_sha256'][n]==h,'frozen private '+n)
 compiler=json.loads((ROOT/'evidence/voice_block_library02.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler identity');free=shutil.disk_usage(ROOT).free;require(free>=1024**3+128*1024**2,'reserve and output budget');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];work.mkdir();exe=work/'extended.exe';commands=[];profiles=[];replays=[];started=time.perf_counter();lib='references-local/voice-block-library02/librf_d_circuit.rlib'
 r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler,new_library_compile=False,new_cargo_cache=False,lab_stack_bytes=33554432,available_free_bytes=free,reserve_bytes=1024**3,output_budget_bytes=128*1024**2)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
 try:
  cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',EXAMPLE,'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];q=run(cmd,120);commands.append(q)
  if q['exit_code']:replays.append(run(cmd,120));require(False,'compile rejected')
  for seed in inp['seeds']:
   maximum=seed['maximum_half_ticks'];cmd=[str(exe),str(ROOT/seed['path']),str(work/str(maximum))];q=run(cmd,1900);profiles.append(dict(final_decay=True,maximum_half_ticks=maximum,**q));print('EXTENDED_PROFILE',maximum,q['exit_code'],q['stderr'][-250:],flush=True)
   if q['exit_code']:replays.append(run(cmd[:-1]+[str(work/('rejected-replay-'+str(maximum)))],1900));require(False,'native continuation rejected')
   require((work/str(maximum)/'seam-old.bin').read_bytes()==(work/str(maximum)/'seam-new.bin').read_bytes(),'complete seam advances by bits')
  require(time.perf_counter()-started<=4000,'campaign wall budget');r.update(passed=True,seam_bits_identical=True,seam_compared_accepted=8,new_source_event=False)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n==EXAMPLE or n.startswith('tools/')}
 r.update(commands=commands,profiles=profiles,replays=replays,wall_s=time.perf_counter()-started,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},minimum_free_bytes=shutil.disk_usage(ROOT).free,outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()]);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable native inputs');require(sum(o['bytes'] for o in r['outputs'])<=128*1024**2,'native output budget');write(out,r);print('EXTENDED_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'extended native continuation')
if __name__=='__main__':main()
