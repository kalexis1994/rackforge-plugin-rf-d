"""Four bounded serial laboratory trajectories with explicit parameter recipes."""
import json,os,re,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
def main():
 out=ROOT/'evidence/voice_cutoff_temporal_native01.json';work=ROOT/'references-local/cutoff-temporal01';require(not out.exists() and not work.exists(),'exclusive campaign');old=json.loads((ROOT/'evidence/voice_cutoff_opening_tests01.json').read_text(encoding='utf8'));inputs=json.loads((ROOT/'evidence/voice_cutoff_temporal_inputs01.json').read_text(encoding='utf8'));require(old['passed'] and inputs['passed'],'base');lib='references-local/joint-startup01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),**{p['path']:p['sha256'] for p in inputs['profiles']}}
 for n,h in private.items():require(old['private_input_sha256'][n]==h and sha(ROOT/n)==h,'protected input '+n)
 compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');names=['tools/run_cutoff_temporal.py','tools/prepare_cutoff_temporal.py','tools/joint_cutoff_temporal_runner.rs','tools/joint_candidate_cycles_runner.rs','docs/VOZ_CUTOFF_TEMPORAL_PROTOCOLO.md','evidence/voice_cutoff_temporal_inputs01.json','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt'];before={n:sha(ROOT/n) for n in names};free=shutil.disk_usage(ROOT).free;minimum=free;r=dict(schema='rf-d/cutoff-temporal-native/v1',passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,commands=[],profiles=[],replays=[],outputs=[],reserve_bytes=1024**3,estimated_output_bytes=32*1024**2,available_free_bytes=free,profile_budget_s=900,interval_budget=12000,success_budget_s=3800,administrative_budget_s=4200,lab_stack_bytes=33554432,new_library_compile=False,new_audio=False,new_spice_processes=0)
 def save():out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
 start=time.perf_counter();env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';save()
 try:
  require(free>=r['reserve_bytes']+r['estimated_output_bytes'],'resource preflight');work.mkdir();exe=work/'run.exe';cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_cutoff_temporal_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['commands'].append(dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr));save()
  if p.returncode:
   q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['replays'].append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr));require(False,'caller compilation')
  for seed in inputs['profiles']:
   knob=seed['cutoff_fraction'];maximum=seed['maximum_half_ticks'];directory=work/f'{knob}-{maximum}';directory.mkdir();cmd=[str(exe),'run',str(maximum),str(directory),'12000',str(ROOT/seed['path']),str(knob)];t=time.perf_counter();stop_at=None;reason=None
   with (directory/'stdout.txt').open('xb') as stdout,(directory/'stderr.txt').open('xb') as stderr:
    process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
    while process.poll() is None:
     now=time.perf_counter();minimum=min(minimum,shutil.disk_usage(ROOT).free)
     if stop_at is None and (minimum<r['reserve_bytes'] or now-t>900 or now-start>4200):stop_at=now;reason='disk or elapsed budget';(work/'stop.flag').write_text(reason+'\n',encoding='utf8')
     if stop_at is not None and now-stop_at>20:process.kill();process.wait()
     time.sleep(.25)
   text=(directory/'stderr.txt').read_text(encoding='utf8');r['profiles'].append(dict(cutoff_fraction=knob,maximum_half_ticks=maximum,initial_checkpoint=seed['path'],command=cmd,exit_code=process.returncode,wall_s=time.perf_counter()-t,administrative_stop=stop_at is not None,stop_reason=reason,stdout=(directory/'stdout.txt').read_text(encoding='utf8'),stderr=text));save();print('CUTOFF_TEMPORAL_PROFILE',knob,maximum,process.returncode,r['profiles'][-1]['wall_s'],text[-650:],flush=True)
   if process.returncode:
    r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))};match=re.search(r'FAILURE,target_ticks=(\d+),reason=ENGINE_REJECT',text)
    if match:
     cmd=[str(exe),'replay',str(directory/'final.ckp'),match[1],str(knob)];p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['replays'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));save()
    else:r['replay_pending']='Administrative or observation failure; preserve exact state before further diagnosis.'
  require(len(r['profiles'])==4 and all(p['exit_code']==0 and not p['administrative_stop'] for p in r['profiles']) and time.perf_counter()-start<=3800,'complete bounded campaign');r['passed']=True
 except Exception:r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
 r['minimum_free_bytes']=minimum;r['wall_s']=time.perf_counter()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in private};require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'unchanged inputs');r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()] if work.exists() else [];save();print('CUTOFF_TEMPORAL_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
