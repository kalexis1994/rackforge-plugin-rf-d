"""Isolated profiling and contemporaneous utility of the zero-pivot guard."""
import argparse,base64,json,os,shutil,statistics,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_voice_pivot import profile_sources,LABELS
from joint_cycles_analysis import require

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt;work=ROOT/f'references-local/voice-pivot-bench{attempt:02d}';out=f'evidence/voice_pivot_bench{attempt:02d}.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive bench')
 for n,s in profile_sources().items():require((ROOT/n).read_text(encoding='utf8')==s,'declared profile kernel')
 names=['tools/run_voice_pivot_bench.py','tools/prepare_voice_pivot.py','tools/voice_pivot_bench.rs','docs/VOZ_COSTO_PIVOTE_PROTOCOLO.md','evidence/voice_pivot_inputs01.json',*profile_sources()];before={n:sha(ROOT/n) for n in names};old=json.loads((ROOT/'evidence/voice_decay_tests01.json').read_text(encoding='utf8'));lib='references-local/decay-voice02/librf_d_circuit.rlib';bank='references-local/voice-pivot-inputs01/pairs.bin';require(sha(ROOT/lib)==old['private_input_sha256'][lib],'frozen library');private={n:sha(ROOT/n) for n in [lib,bank]}
 compiler=json.loads((ROOT/'evidence/voice_decay_native02.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');require(shutil.disk_usage(ROOT).free>=1024**3+96*1024**2,'budget/reserve');work.mkdir();exe=work/'bench.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];replays=[];r=dict(passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,new_library_compile=False,new_cargo_cache=False,lab_stack_bytes=33554432)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);q=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t);commands.append(q);return q
 try:
  cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/voice_pivot_bench.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];c=run(cmd,120)
  if c['exit_code']:replays.append(run(cmd,120));require(False,'bench compile rejected')
  cmd=[str(exe),str(ROOT/bank)];q=run(cmd,300)
  if q['exit_code']:replays.append(run(cmd,300));require(False,'bench exact bank rejected')
  lines=q['stdout'].splitlines();rows=[list(map(int,l.split(',')[1:])) for l in lines if l.startswith('PROFILE,')];rounds=[list(map(int,l.split(',')[1:])) for l in lines if l.startswith('ROUND,')];require(len(rows)==18 and [x[0] for x in rows]==list(range(18)) and len(rounds)==5 and [x[0] for x in rounds]==list(range(5)) and lines[-1]=='PIVOT_BENCH_PASSED,78,1834,5' and 'ERRORS_PASSED,6' in lines,'observed scope')
  t=[row[1] for row in rows];c=[row[2] for row in rows];require(c[0]==78 and c[3]==c[2] and c[5]==c[17]==c[14] and c[6]==2*c[5] and all(c[k]==c[5] for k in [7,8,9]) and c[13]==c[16],'nested factor call accounting');require(t[1]+t[17]<=t[0] and t[2]<=t[1] and t[3]<=t[2] and sum(t[6:10])+t[14]<=t[5] and t[5]+t[15]+t[16]<=t[17],'nested clocks')
  baseline=statistics.median(x[1] for x in rounds);candidate=statistics.median(x[2] for x in rounds);worst=max(x[2]/x[1] for x in rounds);utility=candidate<=.9*baseline and worst<=1.05
  r.update(passed=True,numeric_bank_passed=True,copy_and_profile_exact=True,candidate_exact=True,pairs=78,bit_fields_per_pair=1834,nominal_counters_known_pairs=24,error_policy_checks=6,phases=[dict(name=n,time_ns=a,calls=b) for n,a,b in zip(LABELS,t,c)],timing_is_nested=True,rounds=[dict(round=i,baseline_ns=a,candidate_ns=b,ratio=b/a) for i,a,b in rounds],baseline_median_ns=baseline,candidate_median_ns=candidate,median_ratio=candidate/baseline,worst_round_ratio=worst,cost_utility_passed=utility,production_promoted=False,full_trajectory_admitted=False,real_time=False,physical_fidelity=False)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith(('.py','.rs'))}
 r.update(commands=commands,replays=replays,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()]);require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable bench inputs');write(out,r);print('PIVOT_BENCH',r['passed'],r.get('median_ratio'),r.get('cost_utility_passed'),r.get('failure',''));require(r['passed'],'pivot bank/profile')
if __name__=='__main__':main()
