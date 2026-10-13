"""Bounded condensation experiment; retain all failed commands and raw source."""
import argparse,json,os,subprocess,time,traceback,base64
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt;work=ROOT/f'references-local/dynamic-schur-bench{attempt:02d}';require(not work.exists(),'exclusive benchmark');work.mkdir();compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');inp=json.loads((ROOT/f'evidence/voice_dynamic_schur_inputs{attempt:02d}.json').read_text(encoding='utf8'));names=['tools/run_dynamic_schur_fast_bench.py','tools/dynamic_schur_fast_solver.rs','tools/joint_dynamic_schur_fast_kernel.rs','tools/prepare_dynamic_schur_fast.py','docs/SCHUR_DINAMICO_INDICES.md','tools/prepare_dynamic_schur_bench.py','tools/dynamic_schur_fast_bench.rs','tools/prepare_dynamic_schur.py','tools/dynamic_schur_solver.rs','tools/joint_dynamic_schur_kernel.rs','tools/joint_lu_extent_kernel.rs','docs/SCHUR_DINAMICO_PROTOCOLO.md',f'evidence/voice_dynamic_schur_inputs{attempt:02d}.json'];sources={n:sha(ROOT/n) for n in names};private={**inp['private_used_sha256'],'references-local/joint-startup01/librf_d_circuit.rlib':sha(ROOT/'references-local/joint-startup01/librf_d_circuit.rlib')};env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);q=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t);commands.append(q);write(f'evidence/voice_dynamic_schur_bench_command{attempt:02d}-{len(commands):02d}.json',q);return q
 try:
  exe=work/'bench.exe';q=run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/dynamic_schur_fast_bench.rs','--extern','rf_d_circuit='+str(ROOT/'references-local/joint-startup01/librf_d_circuit.rlib'),'-o',str(exe)],120)
  if q['exit_code']:run(q['command'],120);require(False,'compile rejection')
  q=run([str(exe),str(ROOT/inp['pair_packet']),str(work/'roots.txt')],600)
  if q['exit_code']:run(q['command'],600);require(False,'condensation benchmark rejection')
  r['passed']=True
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
 r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable measurement');write(f'evidence/voice_dynamic_schur_bench_native{attempt:02d}.json',r);print('DYNAMIC_SCHUR_BENCH',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
