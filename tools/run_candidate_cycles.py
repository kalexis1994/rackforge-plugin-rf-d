"""Two bounded independent processes, exact saved candidate and frozen library."""
import ctypes,json,os,re,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require

def main():
 out=ROOT/'evidence/voice_candidate_cycles_native01.json';work=ROOT/'references-local/candidate-cycles01';require(not out.exists() and not work.exists(),'exclusive campaign')
 old=json.loads((ROOT/'evidence/voice_dynamic_direction_tests01.json').read_text(encoding='utf8'));inputs=json.loads((ROOT/'evidence/voice_candidate_cycles_inputs01.json').read_text(encoding='utf8'));lib='references-local/joint-startup01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),inputs['candidate_path']:inputs['candidate_sha256'],**{p['path']:p['sha256'] for p in inputs['outputs']}}
 require(old['passed'] and inputs['passed'] and private[lib]==old['private_input_sha256'][lib],'base library')
 for n,h in private.items():require(sha(ROOT/n)==h,'private input '+n)
 compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler')
 names=['tools/run_candidate_cycles.py','tools/prepare_candidate_cycles.py','tools/joint_candidate_cycles_runner.rs','tools/joint_corrected_cycles_runner.rs','docs/VOZ_CANDIDATO_CICLOS_PROTOCOLO.md','evidence/voice_candidate_cycles_inputs01.json','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_vectors06.txt'];before={n:sha(ROOT/n) for n in names}
 class Memory(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ['total','available','total_page','available_page','total_virtual','available_virtual','extended']]
 memory=Memory();memory.length=ctypes.sizeof(memory);require(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)),'memory inventory')
 free=shutil.disk_usage(ROOT).free;minimum=free;r=dict(schema='rf-d/candidate-cycles-native/v1',passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,commands=[],profiles=[],replays=[],outputs=[],workers=2,processor_count=os.cpu_count(),initial_available_memory_bytes=memory.available,lab_stack_bytes=33554432,reserve_bytes=1024**3,estimated_output_bytes=64*1024**2,available_free_bytes=free,goal_ticks=5373952000,profile_budget_s=7200,success_budget_s=7400,administrative_budget_s=9000,new_library_compile=False,new_audio=False,new_spice_processes=0)
 def save():out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
 env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';start=time.perf_counter();live=[]
 try:
  require(os.cpu_count()>=2 and memory.available>=1024**3 and free>=r['reserve_bytes']+r['estimated_output_bytes'],'resources');work.mkdir();save();exe=work/'run.exe'
  cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','tools/joint_candidate_cycles_runner.rs','--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['commands'].append(dict(command=cmd,exit_code=p.returncode,wall_s=time.perf_counter()-t,stdout=p.stdout,stderr=p.stderr));save()
  if p.returncode:
   q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['replays'].append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr));require(False,'compile')
  for seed in inputs['outputs']:
   maximum=seed['maximum_half_ticks'];directory=work/str(maximum);directory.mkdir();cmd=[str(exe),'run',str(maximum),str(directory),str(65000 if maximum==65536 else 100000),str(ROOT/seed['path'])];so=(directory/'stdout.txt').open('xb');se=(directory/'stderr.txt').open('xb');t=time.perf_counter();p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW);live.append(dict(process=p,stdout=so,stderr=se,start=t,command=cmd,seed=seed,directory=directory,done=False))
  stop_at=None;reason=None
  while any(not x['done'] for x in live):
   now=time.perf_counter();minimum=min(minimum,shutil.disk_usage(ROOT).free)
   if stop_at is None and (minimum<r['reserve_bytes'] or now-start>9000 or any(not x['done'] and now-x['start']>7200 for x in live)):
    stop_at=now;reason='disk reserve or wall budget';(work/'stop.flag').write_text(reason+'\n',encoding='utf8')
   for x in live:
    if x['done']:continue
    p=x['process']
    if stop_at is not None and now-stop_at>20 and p.poll() is None:p.kill();p.wait()
    if p.poll() is not None:
     x['done']=True;x['stdout'].close();x['stderr'].close();directory=x['directory'];text=(directory/'stderr.txt').read_text(encoding='utf8');r['profiles'].append(dict(maximum_half_ticks=x['seed']['maximum_half_ticks'],initial_checkpoint=x['seed']['path'],command=x['command'],exit_code=p.returncode,wall_s=now-x['start'],administrative_stop=stop_at is not None,stop_reason=reason,stderr=text,stdout=(directory/'stdout.txt').read_text(encoding='utf8')));save();print('CANDIDATE_PROFILE',r['profiles'][-1]['maximum_half_ticks'],p.returncode,text[-650:],flush=True)
   time.sleep(.25)
  for profile in r['profiles']:
   if profile['exit_code']:
    match=re.search(r'FAILURE,target_ticks=(\d+),reason=ENGINE_REJECT',profile['stderr'])
    if match:
     cmd=[str(exe),'replay',str(Path(profile['command'][3])/'final.ckp'),match[1]];q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);r['replays'].append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr))
    else:r['replay_pending']='Administrative/observation failure preserved without interpreting it as an electrical rejection.'
  require(len(r['profiles'])==2 and all(p['exit_code']==0 and not p['administrative_stop'] for p in r['profiles']) and time.perf_counter()-start<=7400,'complete bounded campaign');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py'))}
  for x in live:
   if x['process'].poll() is None:x['process'].kill();x['process'].wait()
   x['stdout'].close();x['stderr'].close()
 r['minimum_free_bytes']=minimum;r['wall_s']=time.perf_counter()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['private_used_sha256_after']={n:sha(ROOT/n) for n in private};r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()] if work.exists() else []
 require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'unchanged inputs');save();print('CANDIDATE_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
