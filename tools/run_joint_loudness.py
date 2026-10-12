"""Bounded caller compilation and immutable library/input execution; preserve failures."""
import argparse,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);a=parser.parse_args();out=f'evidence/voice_loudness_native{a.attempt:02d}.json';work=ROOT/f'references-local/joint-loudness{a.attempt:02d}'
 require(not (ROOT/out).exists() and not work.exists(),'exclusive run')
 old=json.loads((ROOT/'evidence/voice_cutoff_cycles_tests01.json').read_text(encoding='utf8'));input_name=f'evidence/voice_loudness_inputs{a.attempt:02d}.json';inp=json.loads((ROOT/input_name).read_text(encoding='utf8'))
 lib='references-local/joint-startup01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),inp['seed_path']:sha(ROOT/inp['seed_path'])}
 require(all(old['private_input_sha256'][n]==h for n,h in private.items()),'protected inputs')
 compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler identity')
 names=['tools/run_joint_loudness.py','tools/prepare_joint_loudness.py','tools/joint_loudness_kernel.rs','tools/joint_loudness_runner.rs','docs/VOZ_SEGUIDOR_PROTOCOLO.md',input_name,'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs']
 sources={n:sha(ROOT/n) for n in names};free=shutil.disk_usage(ROOT).free;require(free>=1024**3+16*1024**2,'reserve');work.mkdir()
 r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler,commands=[],replays=[],outputs=[],available_free_bytes=free,reserve_bytes=1024**3,estimated_output_bytes=16*1024**2,lab_stack_bytes=33554432,new_library_compile=False)
 env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';start=time.perf_counter()
 exe=work/'run.exe';cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_loudness_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)]
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW)
  return dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr)
 try:
  for command,limit in [(cmd,120),([str(exe),str(ROOT/inp['seed_path']),str(work/'selected.txt')],300)]:
   a=run(command,limit);r['commands'].append(a)
   if a['exit_code']:
    replay=command.copy()
    if limit==300:replay[-1]=str(work/'replay.txt')
    r['replays'].append(run(replay,limit));require(False,'native rejection')
  r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
 r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in private};r['minimum_free_bytes']=shutil.disk_usage(ROOT).free;r['wall_s']=time.perf_counter()-start
 r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()]
 require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'unchanged inputs');write(out,r);print('LOUDNESS_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
