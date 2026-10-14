"""Measure nested phases, validate all observed numerical fields against current baseline."""
import base64,json,os,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_zero_profile import RUST
from prepare_voice_pivot import LABELS
from joint_cycles_analysis import require
def main():
 work=ROOT/'references-local/voice-zero-profile01';out='evidence/voice_zero_profile01.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive current profile');names=[*RUST,'tools/prepare_zero_profile.py','tools/run_zero_profile.py','tools/prepare_voice_pivot.py','tools/prepare_zero_voice.py','evidence/voice_zero_inputs01.json'];before={n:sha(ROOT/n) for n in names};private={n:sha(ROOT/n) for n in ['references-local/voice-zero-inputs01/pairs.bin','references-local/voice-block-library02/librf_d_circuit.rlib']};compiler=json.loads((ROOT/'evidence/voice_block_library02.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');work.mkdir();exe=work/'profile.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];replays=[];r=dict(passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,new_library_compile=False,new_cargo_cache=False,timing_is_nested=True,timing_overhead_not_subtracted=True,production_promoted=False,real_time=False,physical_fidelity=False)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
 try:
  for cmd,limit in [([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',RUST[-1],'--extern','rf_d_circuit='+str(ROOT/'references-local/voice-block-library02/librf_d_circuit.rlib'),'-o',str(exe)],120),([str(exe),str(ROOT/'references-local/voice-zero-inputs01/pairs.bin')],300)]:
   q=run(cmd,limit);commands.append(q)
   if q['exit_code']:replays.append(run(cmd,limit));require(False,'current profiling rejection')
  lines=q['stdout'].splitlines();require(lines[-1].startswith('CURRENT_PROFILE_PASSED,168,'),'complete current bank');phases=[]
  for line in lines:
   if line.startswith('PROFILE,'):_,k,ns,calls=line.split(',');phases.append(dict(name=LABELS[int(k)],time_ns=int(ns),calls=int(calls)))
  require(len(phases)==18 and phases[0]['calls']==168,'all clock phases');r.update(passed=True,pairs=168,all_1834_f64_and_counters_identical=True,phases=phases,baseline_bank_ns=int(lines[-1].split(',')[2]),profiled_bank_ns=int(lines[-1].split(',')[3]))
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith(('.py','.rs'))}
 r.update(commands=commands,replays=replays,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]);require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable profile inputs');write(out,r);print('CURRENT_PROFILE',r['passed'],r.get('failure',''),flush=True);require(r['passed'],'current exact phase profile')
if __name__=='__main__':main()
