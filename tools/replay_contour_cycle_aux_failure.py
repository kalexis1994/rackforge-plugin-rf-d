"""Recover the surviving recursive-include compile rejection; originals lacked stderr."""
import json,os,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 source=ROOT/'references-local/contour-cycle-diagnostic02/proposed.rs';h=sha(source);compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];work=ROOT/'references-local/contour-cycle-aux-replay02';require(not work.exists(),'exclusive recovery');work.mkdir();lib=ROOT/'references-local/joint-startup01/librf_d_circuit.rlib';cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(source),'--extern','rf_d_circuit='+str(lib),'-o',str(work/'rejected.exe')];commands=[]
 for _ in range(2):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);commands.append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t))
 write('evidence/voice_contour_cycle_aux_replay_commands01.json',dict(passed=False,commands=commands,scope='raw recovery commands before validation'))
 require(commands[0]['exit_code']!=0 and commands[0]['exit_code']==commands[1]['exit_code'] and commands[0]['stderr']==commands[1]['stderr'] and sha(source)==h,'identical surviving-source compile rejection')
 write('evidence/voice_contour_cycle_aux_replay01.json',dict(passed=True,source_sha256={'tools/replay_contour_cycle_aux_failure.py':sha(ROOT/'tools/replay_contour_cycle_aux_failure.py')},private_used_sha256={source.relative_to(ROOT).as_posix():h,lib.relative_to(ROOT).as_posix():sha(lib)},compiler=compiler,commands=commands,original_attempts_stderr_retained=False,recovery_after_adapter_fix=True,circuit_trajectory_evidence=False));print('AUX_REJECTION_REPLAY',commands[0]['exit_code'])
if __name__=='__main__':main()
