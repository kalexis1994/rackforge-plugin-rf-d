"""Build the isolated electrical-control family, compare nominal, run two histories."""
import argparse,base64,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_decay_control import RUST
from joint_cycles_analysis import require

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt
 work=ROOT/f'references-local/decay-voice{attempt:02d}';out=f'evidence/voice_decay_native{attempt:02d}.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive decay campaign')
 old=json.loads((ROOT/'evidence/voice_release_tests01.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_decay_inputs01.json').read_text(encoding='utf8'));require(old['passed'] and inp['passed'],'admitted own inputs')
 for n,h in inp['source_sha256'].items():require(sha(ROOT/n)==h,'declared source '+n)
 names={p.relative_to(ROOT).as_posix() for p in (ROOT/'crates/rf-d-circuit/src').rglob('*.rs')}|set(RUST)|{'tools/run_decay_control.py','tools/prepare_decay_control.py','tools/prepare_decay_callers.py','evidence/voice_decay_inputs01.json','evidence/voice_release_tests01.json','docs/DECAY_CONTROL_PROTOCOLO.md'};sources={n:sha(ROOT/n) for n in sorted(names)}
 lib='references-local/conditioned-recipe-library02/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),**inp['private_used_sha256']}
 for n,h in private.items():require(h==old['private_input_sha256'][n],'frozen private '+n)
 compiler=json.loads((ROOT/'evidence/voice_conditioned_recipe_library02.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'frozen compiler');free=shutil.disk_usage(ROOT).free;require(free>=1024**3+128*1024**2,'reserve and budget')
 env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];work.mkdir();newlib=work/'librf_d_circuit.rlib';exe=work/'decay.exe';legacy=work/'nominal-legacy.exe';commands=[];profiles=[];legacy_runs=[];replays=[];start=time.perf_counter()
 r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler,new_library_compile=True,new_cargo_cache=False,lab_stack_bytes=33554432,available_free_bytes=free,reserve_bytes=1024**3,output_budget_bytes=128*1024**2)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
 try:
  builds=[[compiler['path'],'--edition=2021','--crate-name','rf_d_circuit','--crate-type','rlib','-C','opt-level=2','-C','debuginfo=0','crates/rf-d-circuit/src/lib.rs','-o',str(newlib)]]
  builds += [[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',src,'--extern','rf_d_circuit='+str(link),'-o',str(dest)] for src,link,dest in [(RUST[3],newlib,exe),(RUST[4],ROOT/lib,legacy)]]
  for cmd in builds:
   c=run(cmd,120);commands.append(c)
   if c['exit_code']:replays.append(run(cmd,120));require(False,'native compile rejected')
  for maximum in [1048576,524288]:
   seed=next(s for s in inp['seeds'] if s['maximum_half_ticks']==maximum);lc=run([str(legacy),str(ROOT/seed['path']),str(work/('legacy-'+str(maximum)))],120);legacy_runs.append(lc);require(lc['exit_code']==0,'frozen nominal comparator')
   cmd=[str(exe),str(ROOT/seed['path']),str(work/str(maximum))];p=run(cmd,1900);profiles.append(dict(final_decay=True,maximum_half_ticks=maximum,**p));print('DECAY_PROFILE',maximum,p['exit_code'],p['stderr'][-250:],flush=True)
   if p['exit_code']:replays.append(run(cmd[:-1]+[str(work/('rejected-replay-'+str(maximum)))],1900));require(False,'controlled trajectory rejected')
   a=(work/('legacy-'+str(maximum))/'nominal.bin').read_bytes();require(a==(work/str(maximum)/'nominal-old.bin').read_bytes()==(work/str(maximum)/'nominal-new.bin').read_bytes(),'three nominal accepted histories by bits')
  require(time.perf_counter()-start<=4000,'campaign budget');r.update(passed=True,nominal_three_way_identical=True,nominal_compared_accepted=8,invalid_control_rejections=12,invalid_control_restore_rejections=2,only_resistance_changed_at_event=True)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n in RUST or n.startswith('tools/')}
 r.update(commands=commands,legacy_runs=legacy_runs,profiles=profiles,replays=replays,wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},minimum_free_bytes=shutil.disk_usage(ROOT).free,outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()])
 require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable campaign inputs');write(out,r);print('DECAY_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'controlled native campaign')
if __name__=='__main__':main()
