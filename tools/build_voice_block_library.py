"""Build the public candidate and benchmark both public families together."""
import argparse,base64,json,os,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def public_bench():
 s=(ROOT/'tools/voice_block_bench.rs').read_text(encoding='utf8');return s.replace('#[path="voice_block_kernel.rs"] mod candidate;','use rf_d_circuit::block_decay_voice as candidate;').replace('BLOCK_BENCH_PASSED','PUBLIC_BLOCK_BENCH_PASSED').replace('let cs=cases(&args[1]);','let cs=cases(&args[1]);assert_eq!(candidate::dynamic_schur::structural_policy_audit(),209764);println!("STRUCTURE_PASSED,209764");')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt
 work=ROOT/f'references-local/voice-block-library{attempt:02d}';out=f'evidence/voice_block_library{attempt:02d}.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive public library');require(json.loads((ROOT/'evidence/voice_block_promotion01.json').read_text(encoding='utf8'))['passed'],'family promotion input');work.mkdir();src=work/'public_bench.rs';s=public_bench()
 for n in ['voice_pivot_profile_kernel.rs','voice_pivot_copy_kernel.rs']:s=s.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
 src.write_text(s,encoding='utf8',newline='\n');names={p.relative_to(ROOT).as_posix() for p in (ROOT/'crates/rf-d-circuit/src').rglob('*.rs')}|{'tools/build_voice_block_library.py','tools/voice_block_bench.rs','evidence/voice_block_promotion01.json'};sources={n:sha(ROOT/n) for n in names};compiler=json.loads((ROOT/'evidence/voice_decay_native02.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];lib=work/'librf_d_circuit.rlib';exe=work/'public-bench.exe';commands=[];replays=[];r=dict(passed=False,source_sha256=sources,compiler=compiler,new_library_compile=True,new_cargo_cache=False,lab_stack_bytes=33554432)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);q=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t);commands.append(q);return q
 try:
  cmds=[[compiler['path'],'--edition=2021','--crate-name','rf_d_circuit','--crate-type','rlib','-C','opt-level=2','-C','debuginfo=0','crates/rf-d-circuit/src/lib.rs','-o',str(lib)],[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(src),'--extern','rf_d_circuit='+str(lib),'-o',str(exe)]]
  for cmd in cmds:
   q=run(cmd,120)
   if q['exit_code']:replays.append(run(cmd,120));require(False,'public compile rejected')
  cmd=[str(exe),str(ROOT/'references-local/voice-pivot-inputs01/pairs.bin')];q=run(cmd,300)
  if q['exit_code']:replays.append(run(cmd,300));require(False,'public bank rejected')
  require(q['stdout'].splitlines()[-1]=='PUBLIC_BLOCK_BENCH_PASSED,78,1834,5' and 'STAMPS_PASSED,78,211138' in q['stdout'],'public matrix and bank identity');rounds=[list(map(int,l.split(',')[1:])) for l in q['stdout'].splitlines() if l.startswith('ROUND,')];require(len(rounds)==5,'public cost scope');import statistics
  a=statistics.median(r[1] for r in rounds);b=statistics.median(r[2] for r in rounds);w=max(r[2]/r[1] for r in rounds);r.update(passed=True,public_bank_exact=True,complete_stamp_bit_fields=78*211138,rounds=rounds,median_ratio=b/a,worst_round_ratio=w,cost_utility_passed=b<=.9*a and w<=1.05,physical_fidelity=False,real_time=False)
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith(('.py','.rs'))}
 r.update(commands=commands,replays=replays,source_sha256_after={n:sha(ROOT/n) for n in names},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()]);require(sources==r['source_sha256_after'],'stable library inputs');write(out,r);print('PUBLIC_BLOCK_LIBRARY',r['passed'],r.get('median_ratio'),r.get('cost_utility_passed'),r.get('failure',''));require(r['passed'],'public library and bank')
if __name__=='__main__':main()
