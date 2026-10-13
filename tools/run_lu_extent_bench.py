"""Run bounded paired benchmark, retaining command receipts before validation."""
import json,os,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 work=ROOT/'references-local/lu-extent-bench01';require(not work.exists(),'exclusive benchmark');work.mkdir();compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');inp=json.loads((ROOT/'evidence/voice_lu_extent_inputs01.json').read_text(encoding='utf8'));names=['tools/run_lu_extent_bench.py','tools/lu_extent_bench.rs','tools/prepare_lu_extent.py','evidence/voice_lu_extent_inputs01.json','docs/LU_EXTENSION_PROTOCOLO.md'];sources={n:sha(ROOT/n) for n in names};private={**inp['private_used_sha256'],'references-local/joint-startup01/librf_d_circuit.rlib':sha(ROOT/'references-local/joint-startup01/librf_d_circuit.rlib')};env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';commands=[];r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);q=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t);commands.append(q);write(f'evidence/voice_lu_extent_bench_command01-{len(commands):02d}.json',q);return q
 try:
  exe=work/'bench.exe';a=run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/lu_extent_bench.rs','--extern','rf_d_circuit='+str(ROOT/'references-local/joint-startup01/librf_d_circuit.rlib'),'-o',str(exe)],120)
  if a['exit_code']:run(a['command'],120);require(False,'compile rejection')
  q=run([str(exe),str(ROOT/inp['pair_packet'])],300)
  if q['exit_code']:run(q['command'],300);require(False,'benchmark rejection')
  r['passed']=True
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:__import__('base64').b64encode((ROOT/n).read_bytes()).decode() for n in names}
 r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]);require(r['source_sha256']==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable benchmark');write('evidence/voice_lu_extent_bench_native01.json',r);print('REUSE_BENCH',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
