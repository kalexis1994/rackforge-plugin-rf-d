"""Bounded serial campaign using exact own checkpoints and a frozen 205-node kernel."""
import json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 out='evidence/voice_loudness_control_native01.json';work=ROOT/'references-local/loudness-control01';require(not (ROOT/out).exists() and not work.exists(),'exclusive campaign')
 inp=json.loads((ROOT/'evidence/voice_loudness_control_inputs01.json').read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/voice_loudness_tests01.json').read_text(encoding='utf8'));lib='references-local/joint-startup01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),inp['origin_path']:inp['origin_sha256'],**{s['path']:s['sha256'] for s in inp['seeds']}}
 require(old['private_input_sha256'][lib]==private[lib],'library identity')
 for n,h in private.items():require(sha(ROOT/n)==h,'private inputs '+n)
 compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler')
 names=['tools/run_loudness_control.py','tools/prepare_loudness_control.py','tools/joint_loudness_control_body.rs','tools/joint_loudness_control_runner.rs','tools/joint_loudness_runner.rs','tools/joint_loudness_kernel.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','docs/VOZ_SEGUIDOR_CONTROL_PROTOCOLO.md','evidence/voice_loudness_control_inputs01.json'];before={n:sha(ROOT/n) for n in names};free=shutil.disk_usage(ROOT).free;require(free>=1024**3+16*1024**2,'disk reserve');work.mkdir()
 r=dict(passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,commands=[],profiles=[],replays=[],outputs=[],reserve_bytes=1024**3,estimated_output_bytes=16*1024**2,available_free_bytes=free,lab_stack_bytes=33554432,new_library_compile=False)
 env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';start=time.perf_counter();exe=work/'run.exe'
 def run(command,limit):
  t=time.perf_counter();p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);return dict(command=command,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr)
 try:
  cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_loudness_control_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];r['commands'].append(run(cmd,120))
  if r['commands'][0]['exit_code']:r['replays'].append(run(cmd,120));require(False,'compile rejection')
  for s in inp['seeds']:
   cmd=[str(exe),str(ROOT/s['path']),str(work/str(s['half_ticks']))];a=run(cmd,300);r['profiles'].append(dict(half_ticks=s['half_ticks'],**a))
   if a['exit_code']:
    replay=cmd[:-1]+[str(work/f"replay{s['half_ticks']}")];r['replays'].append(run(replay,300));require(False,'profile rejection')
  require(time.perf_counter()-start<=750,'campaign budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
 r['wall_s']=time.perf_counter()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in private};r['minimum_free_bytes']=shutil.disk_usage(ROOT).free
 r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()];require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'unchanged inputs');write(out,r);print('LOUDNESS_CONTROL_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
