"""Bounded native C2 circuit campaign, same library and recorded own seeds."""
import argparse,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args();out=f'evidence/newton_reuse_native{args.attempt:02d}.json';work=ROOT/f'references-local/newton-reuse{args.attempt:02d}';require(not (ROOT/out).exists() and not work.exists(),'exclusive native campaign')
 input_name=f'evidence/newton_reuse_inputs{args.attempt:02d}.json';inp=json.loads((ROOT/input_name).read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/voice_contour_cycle_tests01.json').read_text(encoding='utf8'));lib='references-local/joint-startup01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in inp['seeds']},**{s['origin_path']:s['origin_sha256'] for s in inp['seeds']}};require(old['private_input_sha256'][lib]==private[lib],'library identity')
 for n,h in private.items():require(sha(ROOT/n)==h,'private input '+n)
 compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');names=['tools/run_newton_reuse.py','tools/prepare_newton_reuse.py','tools/joint_newton_reuse_kernel.rs','tools/joint_newton_reuse_runner.rs','tools/joint_contour_cycle_kernel.rs','tools/contour_reset_engine.rs','tools/latch_charge_driver.rs','tools/contour_closed_driver.rs','crates/rf-d-circuit/src/joint_engine.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',input_name,'docs/NEWTON_REUSO_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names};free=shutil.disk_usage(ROOT).free;require(free>=1024**3+64*1024**2,'disk reserve');work.mkdir();r=dict(passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,commands=[],profiles=[],replays=[],outputs=[],available_free_bytes=free,reserve_bytes=1024**3,estimated_output_bytes=64*1024**2,lab_stack_bytes=33554432,new_library_compile=False)
 env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';started=time.perf_counter();exe=work/'run.exe'
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);return dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr)
 try:
  cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_newton_reuse_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];a=run(cmd,120);r['commands'].append(a)
  if a['exit_code']:r['replays'].append(run(cmd,120));require(False,'compile rejection')
  for s in inp['seeds']:
   tag=f"{int(s['final_decay'])}-{s['maximum_half_ticks']}";cmd=[str(exe),str(ROOT/s['path']),str(work/tag)];p=run(cmd,990);r['profiles'].append(dict(final_decay=s['final_decay'],maximum_half_ticks=s['maximum_half_ticks'],**p));print('CONTOUR_PROFILE',tag,p['exit_code'],p['stderr'][-300:],flush=True)
   if p['exit_code']:r['replays'].append(run(cmd[:-1]+[str(work/('replay'+tag))],990));require(False,'profile rejection')
  require(time.perf_counter()-started<=4000,'campaign budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
 r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in private};r['wall_s']=time.perf_counter()-started;r['minimum_free_bytes']=shutil.disk_usage(ROOT).free;r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()];require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable inputs');write(out,r);print('CONTOUR_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
